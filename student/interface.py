import asyncio

from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QTimer
from main_interface.elements.done_elements import *



class EnterCode(QMainWindow):

    def __init__(self, prev_page, next_page, sio, id):
        #switch to ->  prev: choice window  |  next : student meet
        super().__init__()
        # id = {'personal_id' : ###, 'meet_password' : ###}
        self.personal_id = id['personal_id']
        self.sio = sio
        self.prev_page = prev_page
        self.next_page = next_page
        self.code_input = None
        self.pswd_input = None
        self.name_input = None
        self.buildUI()

    def buildUI(self):
        def addJoinControls(main_container):
            def inputsArea():
                inputs = QVBoxLayout()
                inputs.setSpacing(10)
                inputs.addStretch()
                self.code_input = lineInput(200, "Введіть код конференції")
                self.pswd_input = lineInput(200, "Введіть пароль")
                self.name_input = lineInput(200, "Введіть ім'я користувача")
                inputs.addWidget(self.code_input)
                inputs.addWidget(self.pswd_input)
                inputs.addWidget(self.name_input)
                inputs.addStretch()
                inputs_widget = QWidget()
                inputs_widget.setLayout(inputs)
                return inputs_widget

            layout_widget = QWidget()
            layout_widget.setFixedWidth(320)
            layout = QHBoxLayout(layout_widget)
            layout.addWidget(inputsArea())
            layout.addWidget(changeWindowButton(lambda: asyncio.create_task(self.on_join_attempt()), text="Go"))
            main_container.layout().addWidget(layout_widget)


        outer_layout = QVBoxLayout()
        outer_layout.addWidget(topContainer(self.prev_page))
        outer_layout.addWidget(horLine())

        main_container = mainContainer()
        main_container.layout().addStretch()
        addJoinControls(main_container)
        main_container.layout().addStretch()

        outer_layout.addWidget(main_container)
        central = QWidget()
        central.setLayout(outer_layout)
        self.setCentralWidget(central)

    #перевіряє чи введені пароль і код конференції
    #якшо є, то відправляє на сервер запит, щоб знайти конференцію і додати туди учасника
    #переключитись на вікно к-ції (MeetStudent)
    async def on_join_attempt(self):
        meet_id = self.code_input.text().strip()
        pswd = self.pswd_input.text().strip()
        print(meet_id, type(meet_id), pswd, type(pswd))
        if not (meet_id and pswd):
            return
        await self.sio.emit('join_meet',
                      {'meet_id': meet_id, 'meet_password': pswd, 'personal_id' : self.personal_id},
                      callback=self.on_join_response)

    # ф-ція, яка спрацює, коли натиснути "Go"
    def temp(self):
        meet_id = self.code_input.text().strip()
        self.next_page(meet_id, self.name_input)

    def on_join_response(self, success=None):
        if success:
            # перекине виконання ф-ції з параметрами у головний потік Qt
            QTimer.singleShot(0, self.temp)
        else:
            self.pswd_input.clear()



class MeetStudent(QMainWindow):
    def __init__(self, prev_page, sio, id, meet_id, name):
        # prev: choice window
        super().__init__()
        # id = {'personal_id' : ###, 'meet_password' : ###}
        self.id = id
        self.meet_id = meet_id
        self.name = name
        self.sio = sio


        outer_layout = QVBoxLayout()
        main_container = mainContainer()

        outer_layout.addWidget(topContainer(prev_page))
        outer_layout.addWidget(horLine())
        outer_layout.addWidget(main_container)

        central = QWidget()
        central.setLayout(outer_layout)
        self.setCentralWidget(central)

    async def leave_meet(self):
        await self.sio.emit("disconnect_participant",
                      {"personal_id" : self.id['personal_id'],
                       "meet_id" : self.meet_id,
                       "role" : "Student"})
