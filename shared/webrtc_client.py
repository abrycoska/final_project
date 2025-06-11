# webrtc_client.py
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaStreamTrack


class WebRTCClient:
    def __init__(self, sio, meet_id: str, personal_id: str, direction : str,
                 audio_track: MediaStreamTrack,
                 camera_track: MediaStreamTrack = None,
                 screen_track: MediaStreamTrack = None):
        self.sio = sio
        self.meet_id = meet_id
        self.personal_id = personal_id
        self.direction = direction
        self.audio = audio_track
        self.scrn = screen_track
        self.cam = camera_track
        self.pc: RTCPeerConnection | None = None

    async def start(self):
        # реєстрація обробників повідомлень
        self.sio.on("webrtc_answer", self._on_answer)
        self.sio.on("webrtc_ice_candidate", self._on_ice)

        # створюємо PeerConnection
        self.pc = pc = RTCPeerConnection()

        # створюємо трансевери і замінюємо їм треки
        v_t = pc.addTransceiver("video", direction=self.direction)
        s_t = pc.addTransceiver("video", direction=self.direction)
        a_t = pc.addTransceiver("audio", direction="sendrecv")
        a_t.sender.replaceTrack(self.audio)
        if self.scrn is not None and self.cam is not None:
            s_t.sender.replaceTrack(self.scrn)
            v_t.sender.replaceTrack(self.cam)

        # відправка ICE-кандидатів
        @pc.on("icecandidate")
        async def icecandidate(candidate):
            print("ice candidate created")
            if candidate:
                candidate_data = {
                    "candidate": candidate.candidate,
                    "sdpMid": candidate.sdpMid,
                    "sdpMLineIndex": candidate.sdpMLineIndex
                }
                await self.sio.emit("webrtc_ice_candidate", {
                    "meet_id":      self.meet_id,
                    "personal_id":  self.personal_id,
                    "candidate":    candidate_data
                })

        # створюємо Offer
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        # відсилаємо його серверу
        await self.sio.emit("webrtc_offer", {
            "meet_id":     self.meet_id,
            "personal_id": self.personal_id,
            "offer": {
                "sdp":  pc.localDescription.sdp,
                "type": pc.localDescription.type
            }
        })

    async def _on_answer(self, data):
        # отримали Answer від сервера
        desc = RTCSessionDescription(sdp=data["answer"]["sdp"], type=data["answer"]["type"])
        await self.pc.setRemoteDescription(desc)

    async def _on_ice(self, data):
        print("ice candidate received")
        # отримали ICE-кандидат
        await self.pc.addIceCandidate(
            sdpMid=data["sdpMid"],
            sdpMLineIndex=data["sdpMLineIndex"],
            candidate=data["candidate"]
        )





