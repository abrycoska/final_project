import asyncio
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from common.elements.done_elements import mainContainer, shadowedLabel, topContainer, horLine
from teacher.ui_parts import MediaPanel
from common.capturing import Vidosik, ScreenCapture, AudioCapture
from common.webrtc_client import WebRTCClient


class MeetTeacher(QMainWindow):
    def __init__(self, prev_page, sio, id):
        # prev: choice window
        super().__init__()
        self.sio = sio
        # id = {'personal_id' : ###, 'meet_password' : ###}
        self.ids = id
        asyncio.create_task(self.sio.emit("register_new_meet", self.ids))

        self.cam = Vidosik()
        self.scrn = ScreenCapture()
        self.audio = AudioCapture()

        self.webrtc = WebRTCClient(
            sio=self.sio,
            meet_id=self.ids["personal_id"],
            personal_id=self.ids["personal_id"],
            direction="sendrecv",
            audio_track=self.audio,
            camera_track=self.cam,
            screen_track=self.scrn,
        )
        asyncio.create_task(self.webrtc.start())

        self.prev_page = prev_page

        self.buildUI()


    def buildTop(self):
        self.top = topContainer(self.prev_page)
        msg_code = f"Meet code: {self.ids['personal_id'][:3]} {self.ids['personal_id'][3:]}"
        msg_pswd = f"Meet passwd: {self.ids['meet_password'][:4]} {self.ids['meet_password'][4:]}"
        msg_label = shadowedLabel(msg_code + '\t' + msg_pswd)
        self.top.layout().addWidget(msg_label)

    def buildMain(self):
        self.main = mainContainer() #містить всередині горизонтальний лейаут
        self.size = self.main.size()
        self.main.layout().setContentsMargins(0, 0, 0, 0)

        left_wgt = QWidget(); left_part = QVBoxLayout(left_wgt)
        # right_wgt = QWidget(); right_part = QVBoxLayout(right_wgt)

        media_panel = MediaPanel(self.cam, self.scrn)
        # Media_control_panel = MediaControl()
        left_part.addWidget(media_panel)
        # left_part.addWidget(Media_control_panel.wgt)

        # buttons_panel = ButtonPanel()
        # stat_panel = StatPanel()
        # right_part.addWidget(buttons_panel.wgt)
        # right_part.addWidget(stat_panel.wgt)

        self.main.layout().addWidget(left_wgt,3)
        # self.main.layout().addWidget(right_wgt,2)


    def buildUI(self):
        self.buildTop()
        self.buildMain()

        self.outer_layout = QVBoxLayout()
        self.outer_layout.setContentsMargins(2, 2, 2, 2)
        self.outer_layout.setSpacing(0)
        self.outer_layout.addWidget(self.top)
        self.outer_layout.addWidget(horLine())
        self.outer_layout.addWidget(self.main)

        central = QWidget()
        central.setLayout(self.outer_layout)
        self.setCentralWidget(central)

    async def leave_meet(self):
        await self.sio.emit("disconnect_participant",
                          {'personal_id' : self.ids['personal_id'],
                           'meet_id' : self.ids['personal_id'],
                           "role" : "Teacher"})
        self.cam.stop()
        self.scrn.stop()

    # async def start_webrtc(self):
    #     print("1")
    #     self.sio.on("webrtc_answer", self.webrtc_answer)
    #     self.sio.on("webrtc_ice_candidate",self.webrtc_ice_candidate)
    #     self.pc = pc = RTCPeerConnection()
    #     print("2")
    #
    #     video_transceiver = pc.addTransceiver("video", direction="sendrecv")
    #     screen_transceiver = pc.addTransceiver("video", direction="sendrecv")
    #     # audio_transceiver = pc.addTransceiver("audio", direction="sendrecv")
    #
    #     video_transceiver.sender.replaceTrack(self.cam)
    #     screen_transceiver.sender.replaceTrack(self.scrn)
    #     # audio_transceiver.sender.replaceTrack(self.audio)
    #
    #     @pc.on("icecandidate")
    #     async def on_ice(candidate):
    #         if candidate:
    #             candidate_data = {"candidate": candidate.candidate,
    #                               "sdpMid": candidate.sdpMid,
    #                               "sdpMLineIndex": candidate.sdpMLineIndex}
    #
    #             await self.sio.emit("webrtc_ice_candidate", {
    #                 "meet_id": self.ids['personal_id'],
    #                 "personal_id": self.ids['personal_id'],
    #                 "candidate": candidate_data
    #             })
    #
    #     offer = await pc.createOffer()
    #     await pc.setLocalDescription(offer)
    #     await self.sio.emit("webrtc_offer", {
    #                         "meet_id" : self.ids['personal_id'],
    #                         "personal_id" : self.ids['personal_id'],
    #                         "offer" : pc.localDescription})
    #
    #
    # async def webrtc_answer(self, data):
    #     description = RTCSessionDescription(sdp=data["answer"].sdp, type=data["answer"].type)
    #     await self.pc.setRemoteDescription(description)
    #
    # async def webrtc_ice_candidate(self, data):
    #     await self.pc.addIceCandidate(data["candidate"])