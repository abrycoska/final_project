from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton
from main_interface.elements.done_elements import *

class EnterCode(QMainWindow):

    def __init__(self, prev_page, next_page, sio):
        #prev: choice window    next : student meet
        super().__init__()
        self.buildUI(prev_page, next_page)

    def buildUI(self, prev_page, next_page):
        def addJoinControls(main_container):
            def inputsArea():
                inputs = QVBoxLayout()
                inputs.setSpacing(10)
                inputs.addStretch()
                inputs.addWidget(lineInput(200, "Введіть код конференції"))
                inputs.addWidget(lineInput(200, "Введіть пароль"))
                inputs.addStretch()
                inputs_widget = QWidget()
                inputs_widget.setLayout(inputs)
                return inputs_widget

            layout_widget = QWidget()
            layout_widget.setFixedWidth(320)
            layout = QHBoxLayout(layout_widget)
            layout.addWidget(inputsArea())
            layout.addWidget(changeWindowButton(next_page, text_input="Go"))
            main_container.layout().addWidget(layout_widget)


        outer_layout = QVBoxLayout()
        outer_layout.addWidget(topContainer(prev_page))
        outer_layout.addWidget(horLine())

        main_container = mainContainer()
        main_container.layout().addStretch()
        addJoinControls(main_container)
        main_container.layout().addStretch()

        outer_layout.addWidget(main_container)
        central = QWidget()
        central.setLayout(outer_layout)
        self.setCentralWidget(central)

class MeetStudent(QMainWindow):
    def __init__(self, prev_page, sio):
        # prev: choice window
        super().__init__()


        outer_layout = QVBoxLayout()
        main_container = mainContainer()

        outer_layout.addWidget(topContainer(prev_page))
        outer_layout.addWidget(horLine())
        outer_layout.addWidget(main_container)

        central = QWidget()
        central.setLayout(outer_layout)
        self.setCentralWidget(central)