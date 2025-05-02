from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import pyqtSignal
import socketio
from main_interface.elements.done_elements import mainContainer, shadowedLabel, topContainer, horLine


class MeetTeacher(QMainWindow):
    code_receiver = pyqtSignal(str)
    def __init__(self, prev_page, sio, id):
        # prev: choice window
        super().__init__()
        self.sio = sio
        self.id = id
        self.current_ids = None
        self.code_receiver.connect(self.handle_received_code)
        # self.sio.on('personal_code_generated', self.meet_code_generated)

        self.buildUI(prev_page)

    def buildUI(self, prev_page):
        self.outer_layout = QVBoxLayout()
        self.main = mainContainer()
        self.top = topContainer(prev_page)
        line = horLine()

        self.outer_layout.addWidget(self.top)
        self.outer_layout.addWidget(line)
        self.outer_layout.addWidget(self.main)

        central = QWidget()
        central.setLayout(self.outer_layout)
        self.setCentralWidget(central)

    def meet_code_generated(self, data):
        code = data['code']
        self.code_receiver.emit(code)
    def handle_received_code(self, code):
        if self.current_ids is not None:
            self.top.layout().removeWidget(self.current_ids)
            self.current_ids.deleteLater()
            self.current_ids = None
        msg = f"Meet code: {code}"
        self.current_ids = shadowedLabel(msg)
        self.top.layout().addWidget(self.current_ids)

    def showEvent(self, event):
        # кожного разу, коли вікно показують,
        # просимо новий код у сервера
        super().showEvent(event)
        self.sio.emit('register_new_meet', {'id' : self.id})



