from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer

from main_interface.elements.done_elements import MediaButton

class MediaPanel(QWidget):
    def __init__(self, cam, scrn):
        super().__init__()

        self.video_panel = VideoPanel(cam)
        self.screen_panel = ScreenPanel(scrn)

        self.setFixedHeight(730)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.screen_panel,9)
        self.layout.addWidget(self.video_panel,9)
        self.layout.addWidget(MediaControl(cam, scrn),2)

class VideoPanel(QWidget):
    def __init__(self, cam):
        super().__init__()
        self.cam = cam
        self.video_label = QLabel()
        self.video_label.setFixedSize(600, 360)
        self.video_label.setScaledContents(False)
        self.video_label.setAlignment(Qt.AlignCenter)
        QHBoxLayout(self).addWidget(self.video_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(15)

    def update(self):
        frame = self.cam.get_frame()
        if frame is None: return
        h, w, ch = frame.shape
        # qimage це пікселі в пам'яті (також frame.data це пікселі у пам'яті)
        # pixmap робить саме картинку з цих пікселів, щоб швидко відобразити у QLabel
        q_image = QImage(frame.data, w, h, ch*w,QImage.Format_RGB888)
        pix = QPixmap.fromImage(q_image)

        # тут до максимального розміру збільшується, а дві зайві сторони обрізаються
        cropped = pix.scaled(self.video_label.size(), Qt.KeepAspectRatioByExpanding)

        self.video_label.setPixmap(cropped)

class ScreenPanel(QWidget):
    def __init__(self, scrn):
        super().__init__()
        self.scrn = scrn
        self.screen_label = QLabel()
        self.screen_label.setFixedSize(600, 360)
        self.screen_label.setAlignment(Qt.AlignCenter)
        QHBoxLayout(self).addWidget(self.screen_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(15)

    def update(self):
        img = self.scrn.get_frame_img()
        if img is None: return
        pix = QPixmap.fromImage(img)
        cropped = pix.scaled(self.screen_label.size(), Qt.KeepAspectRatioByExpanding)
        self.screen_label.setPixmap(cropped)
#
# class StatPanel():
#
# class ButtonPanel():

class MediaControl(QWidget):
    def __init__(self, cam, scrn):
        super().__init__()
        self.cam = cam
        self.scrn = scrn
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(20)
        self.addButtons()

    def addButtons(self):
        self.cam_btn = MediaButton(self.cam, text='cam')
        self.scrn_btn = MediaButton(self.scrn, text='scrn')

        self.layout.addStretch()
        self.layout.addWidget(self.cam_btn)
        self.layout.addWidget(self.scrn_btn)
        self.layout.addStretch()




