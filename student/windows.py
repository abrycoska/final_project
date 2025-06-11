import asyncio
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from setuptools.extern import names

from common.elements.done_elements import mainContainer, topContainer, horLine, lineInput, changeWindowButton
from common.webrtc_client import WebRTCClient

class EnterCodeUI:
    """Графічний інтерфейс для вікна приєднання до конференції"""
    def __init__(self, prev_page, next_page, sio, ids):
        self.prev_page = prev_page
        self.next_page = next_page
        self.sio = sio
        self.ids = ids

        self.personal_id = self.ids["personal_id"]
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

        # Блок вводу
        layout_widget = QWidget()
        layout_widget.setFixedWidth(320)
        layout = QHBoxLayout(layout_widget)

        inputs = QVBoxLayout()
        inputs.setSpacing(10)
        inputs.addStretch()
        self.code_input = lineInput(200, "Введіть код конференції")
        self.pswd_input = lineInput(200, "Введіть пароль")
        self.ids["personal_name"] = self.name_input = lineInput(200, "Введіть ім'я користувача")
        inputs.addWidget(self.code_input)
        inputs.addWidget(self.pswd_input)
        inputs.addWidget(self.name_input)
        inputs.addStretch()

        # Кнопка "Go"
        join_btn = changeWindowButton(lambda: asyncio.create_task(self._on_join_attempt()), text="Go")

        layout.addLayout(inputs)
        layout.addWidget(join_btn)
        main_container.layout().addStretch()
        main_container.layout().addWidget(layout_widget)
        main_container.layout().addStretch()

        outer_layout.addWidget(main_container)
        container = QWidget()
        container.setLayout(outer_layout)
        return container

    async def _on_join_attempt(self):
        meet_id = self.code_input.text().strip()
        pswd = self.pswd_input.text().strip()
        name = self.name_input.text().strip()
        if not (meet_id and pswd): return

        await self.sio.emit('join_meet',
                            {
                                "meet_id": meet_id,
                                "meet_password": pswd,
                                "personal_id": self.personal_id,
                                "personal_name": name
                             },
                            callback=self._on_join_response)

    def _on_join_response(self, success=None):
        if success:
            # переключаємось на MeetStudent
            QTimer.singleShot(0, lambda: self.next_page(self.code_input.text().strip(), self.name_input))
        else:
            self.pswd_input.clear()


class MeetStudentUI:
    """Графічний інтерфейс для студентського вікна конференції"""

    def __init__(self, prev_page, sio, ids, audio, camera_track, screen_track):
        # Зберігаємо колбеки та треки
        self.prev_page = prev_page
        self.sio = sio
        self.ids = ids
        self.audio = audio
        self.camera_track = camera_track
        self.screen_track = screen_track

        # Налаштовуємо WebRTC-клієнта для прийому
        self.webrtc = WebRTCClient(
            sio=self.sio,
            meet_id=self.ids["personal_id"],
            personal_id=self.ids["personal_id"],
            direction="recvonly",
            audio_track=self.audio,
            camera_track=self.camera_track,
            screen_track=self.screen_track,
        )
        asyncio.create_task(self.webrtc.start())

    def create_widget(self) -> QWidget:
        # Зовнішній вертикальний лейаут
        outer_layout = QVBoxLayout()
        outer_layout.addWidget(topContainer(self.prev_page))
        outer_layout.addWidget(horLine())

        # Основний контейнер із горизонтальним поділом
        main_container = mainContainer()
        content_layout = main_container.layout()

        # Ліва частина: екран викладача
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        # панель для відображення скріну викладача
        screen_panel = ScreenPanel(self.screen_track)
        left_layout.addWidget(screen_panel)
        content_layout.addWidget(left_widget, 3)

        # Права частина: відео викладача та кнопки
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(10)

        # Панель для відео викладача
        video_panel = VideoPanel(self.camera_track)
        right_layout.addWidget(video_panel)

        # Кнопка "Підняти руку"
        raise_btn = changeWindowButton(
            lambda: asyncio.create_task(self._raise_hand()),
            text="підняти руку",
            width=120,
            height=40
        )
        right_layout.addWidget(raise_btn)

        # Панель перемикачів камери і мікрофону
        toggles = QWidget()
        toggles_layout = QHBoxLayout(toggles)
        cam_btn = MediaButton(self.camera_track, text="камера")
        mic_btn = MediaButton(self.audio, text="мікрофон")
        toggles_layout.addWidget(cam_btn)
        toggles_layout.addWidget(mic_btn)
        right_layout.addWidget(toggles)

        # Відступ унизу
        right_layout.addStretch()
        content_layout.addWidget(right_widget, 1)

        # Формуємо фінальний віджет
        outer_layout.addWidget(main_container)
        container = QWidget()
        container.setLayout(outer_layout)
        return container

    async def _raise_hand(self):
        # Відправляємо подію "підняти руку" на сервер
        await self.sio.emit(
            'raise_hand',
            {
                'meet_id': self.ids['personal_id'],
                'personal_id': self.ids['personal_id']
            }
        )
