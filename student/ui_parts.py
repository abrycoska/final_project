import asyncio
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTimer
from common.elements.done_elements import mainContainer, topContainer, horLine, lineInput, changeWindowButton


class EnterCodeUI:
    """Графічний інтерфейс для вікна приєднання до конференції"""
    def __init__(self, prev_page, next_page, sio, personal_id):
        self.prev_page = prev_page
        self.next_page = next_page
        self.sio = sio
        self.personal_id = personal_id
        self.code_input = None
        self.pswd_input = None
        self.name_input = None

    def create_widget(self) -> QWidget:
        # Основний вертикальний лейаут
        outer_layout = QVBoxLayout()
        outer_layout.addWidget(topContainer(self.prev_page))
        outer_layout.addWidget(horLine())

        # Контейнер з полями вводу та кнопкою
        main_container = mainContainer()
        main_container.layout().addStretch()

        # Блок вводу
        layout_widget = QWidget()
        layout_widget.setFixedWidth(320)
        layout = QHBoxLayout(layout_widget)

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

        # Кнопка "Go"
        join_btn = changeWindowButton(lambda: asyncio.create_task(self._on_join_attempt()), text="Go")

        layout.addLayout(inputs)
        layout.addWidget(join_btn)
        main_container.layout().addWidget(layout_widget)
        main_container.layout().addStretch()

        outer_layout.addWidget(main_container)
        container = QWidget()
        container.setLayout(outer_layout)
        return container

    async def _on_join_attempt(self):
        meet_id = self.code_input.text().strip()
        pswd = self.pswd_input.text().strip()
        if not (meet_id and pswd):
            return
        await self.sio.emit(
            'join_meet',
            {'meet_id': meet_id, 'meet_password': pswd, 'personal_id': self.personal_id},
            callback=self._on_join_response
        )

    def _on_join_response(self, success=None):
        if success:
            # переключаємось на MeetStudent
            QTimer.singleShot(0, lambda: self.next_page(self.code_input.text().strip(), self.name_input))
        else:
            self.pswd_input.clear()


class MeetStudentUI:
    """Графічний інтерфейс для студентського вікна конференції"""
    def __init__(self, prev_page):
        self.prev_page = prev_page

    def create_widget(self) -> QWidget:
        outer_layout = QVBoxLayout()
        outer_layout.addWidget(topContainer(self.prev_page))
        outer_layout.addWidget(horLine())
        main_container = mainContainer()
        outer_layout.addWidget(main_container)

        container = QWidget()
        container.setLayout(outer_layout)
        return container
