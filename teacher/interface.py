from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import pyqtSignal
from main_interface.elements.done_elements import mainContainer, shadowedLabel, topContainer, horLine


class MeetTeacher(QMainWindow):
    code_receiver = pyqtSignal(str)
    def __init__(self, prev_page, sio, id):
        # prev: choice window
        super().__init__()
        self.sio = sio
        self.ids = id
        sio.on("new_meet_ids", self.on_new_meet_ids)
        sio.emit("register_new_meet")
        self.current_ids = None

        self.buildUI(prev_page)

    def buildUI(self, prev_page):
        self.outer_layout = QVBoxLayout()
        self.main = mainContainer()
        self.top = topContainer(prev_page)
        line = horLine()

        self.outer_layout.addWidget(self.top)
        self.outer_layout.addWidget(line)
        self.outer_layout.addWidget(self.main)

        msg = f"Meet code: {self.ids['id']}\tMeet passwd: {self.ids['meet_password']}"
        self.current_ids = shadowedLabel(msg)
        self.top.layout().addWidget(self.current_ids)

        central = QWidget()
        central.setLayout(self.outer_layout)
        self.setCentralWidget(central)

    def on_new_meet_ids(self, new_meet_ids):
        self.current_ids = new_meet_ids

