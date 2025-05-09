import asyncio, qasync, sys, cv2, numpy as np
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QSpacerItem
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from main_interface.elements.done_elements import mainContainer, shadowedLabel, topContainer, horLine
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaStreamTrack
import socketio
from teacher.gui_parts import MediaPanel, MediaControl
from main_interface.capturing import Vidosik, ScreenCapture


class MeetTeacher(QMainWindow):
    def __init__(self, prev_page, sio, id):
        # prev: choice window
        super().__init__()
        self.sio = sio
        # id = {'personal_id' : ###, 'meet_password' : ###}
        self.ids = id
        asyncio.create_task(self.sio.emit("register_new_meet", self.ids))

        self.prev_page = prev_page
        self.cam = Vidosik()
        self.scrn = ScreenCapture()
        self.buildUI()


    def buildTop(self):
        self.top = topContainer(self.prev_page)
        msg_code = f"Meet code: {self.ids['personal_id'][:3]} {self.ids['personal_id'][3:]}"
        msg_pswd = f"Meet passwd: {self.ids['meet_password'][:4]} {self.ids['meet_password'][4:]}"
        msg_label = shadowedLabel(msg_code + '\t' + msg_pswd)
        self.top.layout().addWidget(msg_label)

    def buildMain(self):
        self.main = mainContainer() #містить всередині горизонтальний лейаут
        self.size = self.main.size()
        self.main.layout().setContentsMargins(0, 0, 0, 0)

        left_wgt = QWidget(); left_part = QVBoxLayout(left_wgt)
        # right_wgt = QWidget(); right_part = QVBoxLayout(right_wgt)

        media_panel = MediaPanel(self.cam, self.scrn)
        # Media_control_panel = MediaControl()
        left_part.addWidget(media_panel)
        # left_part.addWidget(Media_control_panel.wgt)

        # buttons_panel = ButtonPanel()
        # stat_panel = StatPanel()
        # right_part.addWidget(buttons_panel.wgt)
        # right_part.addWidget(stat_panel.wgt)

        self.main.layout().addWidget(left_wgt,3)
        # self.main.layout().addWidget(right_wgt,2)


    def buildUI(self):
        self.buildTop()
        self.buildMain()

        self.outer_layout = QVBoxLayout()
        self.outer_layout.setContentsMargins(2, 2, 2, 2)
        self.outer_layout.setSpacing(0)
        self.outer_layout.addWidget(self.top)
        self.outer_layout.addWidget(horLine())
        self.outer_layout.addWidget(self.main)

        central = QWidget()
        central.setLayout(self.outer_layout)
        self.setCentralWidget(central)

    async def leave_meet(self):
        await self.sio.emit("disconnect_participant",
                          {'personal_id' : self.ids['personal_id'],
                           'meet_id' : self.ids['personal_id'],
                           "role" : "Teacher"})
        self.cam.stop()
        self.scr.stop()

    # def resizeEvent(self, event):
    #     super().resizeEvent(event)
    #     # тут self.main вже має оновлену геометрію
    #     self.size = self.main.size()
    #     print(f"Current main size: {self.size.width()}×{self.size.height()}")
