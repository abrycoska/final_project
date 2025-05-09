import asyncio, qasync, sys, cv2, numpy as np
import threading
import time

import socketio

from av import VideoFrame
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QGuiApplication
from main_interface.elements.done_elements import mainContainer, shadowedLabel, topContainer, horLine
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaStreamTrack


class Vidosik():
    def __init__(self):
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



class ScreenCapture():
    def __init__(self):
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