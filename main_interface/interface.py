from typing import Optional
from PyQt5.QtCore import QEventLoop
from PyQt5.QtWidgets import (QPushButton, QApplication, QMainWindow,
                             QTableWidget, QTableWidgetItem, QVBoxLayout,
                             QHBoxLayout, QWidget, QStackedWidget)
import sys
import requests
import socketio
import asyncio
from main_interface.elements.done_elements import changeWindowButton

# server_url = "https://final-project-0ugb.onrender.com"
server_url = "http://localhost:5000"
class ChoiceWindow(QMainWindow):
    def __init__(self,switch_to_MeetTeacher, switch_to_EnterCode):
        super().__init__()
        layout = QHBoxLayout()
        buttons_layout = QVBoxLayout()

        btn1 = changeWindowButton(switch_to_MeetTeacher, text_input="Я вчитель", width=300)
        btn2 = changeWindowButton(switch_to_EnterCode, text_input="Я учень", width=300)

        buttons_layout.addWidget(btn1)
        buttons_layout.addWidget(btn2)
        buttons_widget = QWidget()
        buttons_widget.setFixedHeight(120)
        buttons_widget.setLayout(buttons_layout)

        layout.addStretch()
        layout.addWidget(buttons_widget)
        layout.addStretch()

        container = QWidget()
        container.setMinimumSize(700, 460)
        container.setLayout(layout)
        self.setCentralWidget(container)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sio = socketio.Client()
        self.sio.connect(server_url, transports=["websocket"])
        self.sio.emit('gen_personal_id', callback=self.personal_id_generated)

        self.setGeometry(200, 300, 800, 600)
        self.stack = QStackedWidget()

        # Дві сторінки, передаємо функцію перемикання
        self.page_choice = ChoiceWindow(self.switch_to_MeetTeacher, self.switch_to_EnterCode)
        self.pages: dict[str, Optional[QWidget]] = {
                    'teacher' : None,
                    'enterCode' : None,
                    'student' : None}
        self.stack.addWidget(self.page_choice)
        self.setCentralWidget(self.stack)

    def personal_id_generated(self, data):
        self.ids = data


    def clean_windows(self):
        for name, page in self.pages.items():
            if page is not None:
                # викличе ф-цію, яка змусить сторінку emit про вихід з конференції
                if hasattr(page, 'leave_meet'):
                    page.leave_meet()

                self.stack.removeWidget(page)
                page.deleteLater()
                self.pages[name] = None

    def switch_to_ChoiceWindow(self):
        self.clean_windows()
        self.stack.setCurrentWidget(self.page_choice)

    def switch_to_MeetTeacher(self):
        self.clean_windows()
        from teacher.interface import MeetTeacher
        self.pages['teacher'] = MeetTeacher(self.switch_to_ChoiceWindow, sio=self.sio, id=self.ids)
        self.stack.addWidget(self.pages['teacher'])
        self.stack.setCurrentWidget(self.pages['teacher'])

    def switch_to_EnterCode(self):
        self.clean_windows()
        from student.interface import EnterCode
        self.pages['enterCode'] =  EnterCode(self.switch_to_ChoiceWindow, self.switch_to_MeetStudent, sio=self.sio, id=self.ids)
        self.stack.addWidget(self.pages['enterCode'])
        self.stack.setCurrentWidget(self.pages['enterCode'])

    def switch_to_MeetStudent(self, meet_id, name):
        self.clean_windows()
        from student.interface import MeetStudent
        self.pages['student'] = MeetStudent(self.switch_to_EnterCode, sio=self.sio, id=self.ids, meet_id=meet_id, name=name)
        self.stack.addWidget(self.pages['student'])
        self.stack.setCurrentWidget(self.pages['student'])

    def closeEvent(self, event):
        # коли вікно закривається – відправити leave_meet для всіх активних сторінок
        self.clean_windows()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication([])
    # loop = QEventLoop(app)
    # asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
    # with loop:
    #     loop.create_task(window.start())
    #     loop.run_forever()