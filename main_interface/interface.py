from PyQt5.QtWidgets import (QPushButton, QApplication, QMainWindow,
                             QTableWidget, QTableWidgetItem, QVBoxLayout,
                             QHBoxLayout, QWidget, QStackedWidget)
import sys
import requests

class ChoiceWindow(QMainWindow):
    def __init__(self,switch_to_ShowCode, switch_to_EnterCode):
        super().__init__()

        layout = QHBoxLayout()
        buttons_layout = QVBoxLayout()

        btn1 = QPushButton("Я викладач"); btn2 = QPushButton("Я учень")
        btn1.setObjectName("greenButton"); btn2.setObjectName("greenButton")
        btn1.clicked.connect(switch_to_ShowCode)
        btn2.clicked.connect(switch_to_EnterCode)

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
        self.setGeometry(200, 300, 800, 600)
        self.stack = QStackedWidget()

        # Дві сторінки, передаємо функцію перемикання
        self.page_choice = ChoiceWindow(self.switch_to_MeetTeacher, self.switch_to_EnterCode)
        self.page_teacher = None
        self.page_enterCode = None
        self.page_student = None

        self.stack.addWidget(self.page_choice)
        self.setCentralWidget(self.stack)


    def switch_to_ChoiceWindow(self):
        self.stack.setCurrentWidget(self.page_choice)

    def switch_to_MeetTeacher(self):
        if not self.page_teacher:
            from teacher.interface import MeetTeacher
            self.page_teacher = MeetTeacher(self.switch_to_ChoiceWindow)
            self.stack.addWidget(self.page_teacher)
        self.stack.setCurrentWidget(self.page_teacher)

    def switch_to_EnterCode(self):
        if not self.page_enterCode:
            from student.interface import EnterCode
            self.page_enterCode =  EnterCode(self.switch_to_ChoiceWindow, self.switch_to_MeetStudent)
            self.stack.addWidget(self.page_enterCode)
        self.stack.setCurrentWidget(self.page_enterCode)

    def switch_to_MeetStudent(self):
        if not self.page_student:
            from student.interface import MeetStudent
            self.page_student = MeetStudent(self.switch_to_EnterCode)
            self.stack.addWidget(self.page_student)
        self.stack.setCurrentWidget(self.page_student)


if __name__ == "__main__":
    app = QApplication([])
    with open("main_interface/style.qss", "r") as f:
        app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())