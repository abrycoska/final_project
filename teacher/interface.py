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
        self.prev_page = prev_page
        self.sio.emit("register_new_meet", self.ids)

        self.buildUI()

    def buildUI(self):
        self.outer_layout = QVBoxLayout()
        self.main = mainContainer()
        self.top = topContainer(self.prev_page)
        line = horLine()

        self.outer_layout.addWidget(self.top)
        self.outer_layout.addWidget(line)
        self.outer_layout.addWidget(self.main)

        msg_code = f"Meet code: {self.ids['personal_id'][:3]} {self.ids['personal_id'][3:]}"
        msg_pswd = f"Meet passwd: {self.ids['meet_password'][:4]} {self.ids['meet_password'][4:]}"
        msg_label = shadowedLabel(msg_code + '\t' + msg_pswd)
        self.top.layout().addWidget(msg_label)

        central = QWidget()
        central.setLayout(self.outer_layout)
        self.setCentralWidget(central)


    def leave_meet(self):
        print("huy")
        self.sio.emit("disconnect_participant", {'personal_id' : self.ids['personal_id'], "Teacher" : True})


