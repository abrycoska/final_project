import asyncio, qasync, sys, cv2, numpy as np
import threading
import time

import socketio

from av import VideoFrame, AudioFrame
import sounddevice as sd
import queue
from PyQt5.QtGui import QImage, QPixmap, QGuiApplication
from aiortc.contrib.media import MediaStreamTrack



class Vidosik(MediaStreamTrack):
    kind = "video"
    def __init__(self):
        super().__init__()
        self.running = False
        self.last_frame = np.zeros((600, 360, 3), dtype=np.uint8)
        self.lock = threading.Lock()

    def start(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.capturer, daemon=True).start()

    def stop(self):
        self.running = False
        self.last_frame = np.zeros((600, 360, 3), dtype=np.uint8)
        if hasattr(self, 'cap'):
            self.cap.release()

    def capturer(self):
        self.cap = cv2.VideoCapture(0)
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                frame = np.zeros((600, 360, 3), dtype=np.uint8)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            with self.lock:
                self.last_frame = cv2.flip(frame, 1)
            time.sleep(1/30)

    def get_frame(self):
        with self.lock:
            if self.last_frame is not None:
                return self.last_frame
            else:
                return None

    async def recv(self):
        """
        Цей метод викликає aiortc щоразу, коли потрібно новий кадр.
        Ми просто обгортаємо numpy-масив у VideoFrame.
        """
        # отримати таймінг (PTS + time_base)
        pts, time_base = await self.next_timestamp()
        img = self.get_frame()  # numpy array HxWx3 в RGB
        frame = VideoFrame.from_ndarray(img, format="rgb24")
        frame.pts = pts
        frame.time_base = time_base
        return frame



class ScreenCapture(MediaStreamTrack):
    kind = "video"
    def __init__(self):
        super().__init__()
        # щоб отримати доступ до віконної системи та екрану. Якщо вже є запущений екземпляр
        # то бере його, інакше створює новий.
        self.app = QGuiApplication.instance() or QGuiApplication(sys.argv)
        self.lock = threading.Lock()

        self.running = False
        self.screen = self.app.primaryScreen()
        self.h, self.w = self.screen.size().height(), self.screen.size().width()

        self.last_frame_arr = np.zeros((self.h, self.w, 4), dtype=np.uint8)
        self.last_frame_img = QImage(self.last_frame_arr.data, self.w, self.h, 4 * self.w, QImage.Format.Format_RGB32)

    def start(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.capturer, daemon=True).start()

    def stop(self):
        self.running = False
        np_arr = np.zeros((self.h, self.w, 4), dtype=np.uint8)
        img = QImage(np_arr.data, self.w, self.h, 4 * self.w, QImage.Format.Format_RGB32)
        with self.lock:
            self.last_frame_img = img
            self.last_frame_arr = np_arr

    def capturer(self):


        while self.running:
            try:
                pixmap = self.screen.grabWindow(0)
                img = pixmap.toImage().convertToFormat(QImage.Format.Format_RGB32)

                # вказнівник на місце в пам'яті
                pointer = img.bits()
                pointer.setsize(img.byteCount())
                np_arr = np.frombuffer(pointer, dtype=np.uint8).reshape(self.h, self.w, 4)

                if np_arr.shape != (self.h, self.w, 4):
                    raise ValueError("np_arr size is incorrect")

            except Exception as e:
                print(e)
                np_arr = np.zeros((self.h,self.w,4), dtype=np.uint8)
                img = QImage(np_arr.data, self.w, self.h, 4*self.w, QImage.Format.Format_RGB32)

            with self.lock:
                # передаємо img, а не pixmap, бо перший - то просто контейнер для пікселів,
                # і його можна безпечно передавати між потоками
                self.last_frame_arr = np_arr
                self.last_frame_img = img
            time.sleep(1/30)

    def get_frame_arr(self):
        with self.lock:
            if self.last_frame_arr is not None:
                return self.last_frame_arr
            else:
                return None

    def get_frame_img(self):
        with self.lock:
            if self.last_frame_img is not None:
                return self.last_frame_img
            else:
                return None

    async def recv(self):
        """
        Цей метод викликає aiortc щоразу, коли потрібно новий кадр.
        Ми просто обгортаємо numpy-масив у VideoFrame.
        """
        # отримати таймінг (PTS + time_base)
        pts, time_base = await self.next_timestamp()
        img = self.get_frame_arr()  # numpy array HxWx3 в RGB
        frame = VideoFrame.from_ndarray(img, format="rgb24")
        frame.pts = pts
        frame.time_base = time_base
        return frame




class AudioCapture(MediaStreamTrack):
    kind = "audio"

    def __init__(self, samplerate=48000, channels=1, frames_per_buffer=1024):
        super().__init__()  # ініціалізує MediaStreamTrack
        self.samplerate = samplerate
        self.channels = channels
        self.frames_per_buffer = frames_per_buffer

        # черга, куди з потокового колбеку складатимуться аудіоблоки
        self.queue = queue.Queue()
        self.running = False

    def start(self):
        """Запустити фоновий потік захоплення аудіо"""
        if not self.running:
            self.running = True
            self.stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                blocksize=self.frames_per_buffer,
                dtype='float32',
                callback=self.audio_callback
            )
            self.stream.start()

    def stop(self):
        """Зупинити захоплення"""
        if self.running:
            self.running = False
            self.stream.stop()
            self.stream.close()

    def audio_callback(self, indata, frames, time_info, status):
        """Колбек sounddevice: кидаємо буфер у чергу"""
        if not self.running:
            return
        # копіюємо, щоб дані не зникли після виходу з колбеку
        self.queue.put(indata.copy())

    async def recv(self):
        """
        aiortc буде викликати це для отримання нового AudioFrame.
        Беремо один буфер із черги, перетворюємо в int16 і обгортаємо в AudioFrame.
        """
        # отримаємо таймінги
        pts, time_base = await self.next_timestamp()

        try:
            data = self.queue.get(timeout=1)  # блокую до появи даних
        except queue.Empty:
            # якщо нічого не прийшло — нульовий буфер
            data = np.zeros((self.frames_per_buffer, self.channels), dtype='float32')

        # з float32 [-1.0,1.0] у int16
        int_data = (data * 32767).astype(np.int16)

        # створюємо AudioFrame; формат "s16" і layout залежить від каналів
        frame = AudioFrame.from_ndarray(int_data, format="s16", layout="mono" if self.channels == 1 else "stereo")
        frame.pts = pts
        frame.time_base = time_base
        return frame