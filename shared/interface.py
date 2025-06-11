from typing import Optional

from qasync import QEventLoop, asyncSlot
from PyQt5.QtWidgets import (QPushButton, QApplication, QMainWindow,
                             QTableWidget, QTableWidgetItem, QVBoxLayout,
                             QHBoxLayout, QWidget, QStackedWidget)
import sys
import requests
import socketio
import asyncio
import time
from common.elements.done_elements import changeWindowButton


####################### це шоб помилки виводились

import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import qInstallMessageHandler, QtMsgType

# 1. Переозначаємо excepthook
def exception_hook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)
    QMessageBox.critical(None, "Error", "".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
    sys.exit(1)
sys.excepthook = exception_hook

# 2. Встановлюємо Qt-логер
def qt_message_handler(msg_type, context, message):
    print(f"Qt ({msg_type}): {message}")
    if msg_type == QtMsgType.QtCriticalMsg:
        QMessageBox.critical(None, "Qt Critical", message)
    elif msg_type == QtMsgType.QtWarningMsg:
        QMessageBox.warning(None, "Qt Warning", message)
qInstallMessageHandler(qt_message_handler)

##########################



# server_url = "https://final-project-0ugb.onrender.com"
server_url = "http://127.0.0.1:5000"
class ChoiceWindow(QMainWindow):
    def __init__(self,switch_to_MeetTeacher, switch_to_EnterCode):
        super().__init__()
        layout = QHBoxLayout()
        buttons_layout = QVBoxLayout()

        btn1 = changeWindowButton(switch_to_MeetTeacher, text="Я вчитель", width=300)
        btn2 = changeWindowButton(switch_to_EnterCode, text="Я учень", width=300)

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
        self.sio = socketio.AsyncClient()
        if self.sio.connected:
            self.sio.disconnect()
        self.sio.connect(server_url)

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

    async def start(self):
        await self.sio.connect(server_url, transports=["websocket"])
        await self.sio.emit('gen_personal_id', callback=self.personal_id_generated)

    def personal_id_generated(self, data):
        ### personal_id: //, meet_password: //
        self.ids = data

    def clean_windows(self):
        for name, page in self.pages.items():
            if page is None: continue
            # викличе ф-цію, яка змусить сторінку emit про вихід з конференції
            if hasattr(page, 'leave_meet'):
                asyncio.create_task(page.leave_meet())
                # page.leave_meet()
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
        self.pages['student'] = MeetStudent(self.switch_to_EnterCode, sio=self.sio, ids=self.ids)
        self.stack.addWidget(self.pages['student'])
        self.stack.setCurrentWidget(self.pages['student'])

    @asyncSlot()
    async def closeEvent(self, event):
        # коли вікно закривається – відправити leave_meet для всіх активних сторінок
        # loop = asyncio.get_event_loop()
        for page in self.pages.values():
            if page and hasattr(page, "leave_meet"):
                # дочекаємося результату emit
                await page.leave_meet()
        super().closeEvent(event)

    # def closeEvent(self, event):
    #     event.ignore()
    #     asyncio.create_task(self.close_and_clean())
    #
    # async def close_and_clean(self):
    #     # коли вікно закривається – відправити leave_meet для всіх активних сторінок
    #     for page in self.pages.values():
    #         if page and hasattr(page, "leave_meet"):
    #             print('has atr')
    #             await page.leave_meet()
    #     QApplication.quit()


if __name__ == "__main__":
    # 1) Створюємо Qt-додаток і qasync-цикл
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        loop.create_task(window.start())
        loop.run_forever()
    # чистимо ресурси камери, коли закрили всі вікна
    # # cam_manager.stop()