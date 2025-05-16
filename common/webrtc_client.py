# webrtc_client.py
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaStreamTrack


class WebRTCClient:
    def __init__(self, sio, meet_id: str, personal_id: str, direction : str, audio_track: MediaStreamTrack, camera_track: MediaStreamTrack, screen_track: MediaStreamTrack):
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
        v_t.sender.replaceTrack(self.cam)
        s_t.sender.replaceTrack(self.scrn)
        a_t.sender.replaceTrack(self.audio)

        # відправка ICE-кандидатів
        @pc.on("icecandidate")
        async def icecandidate(candidate):
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

        # відсилаємо його серверу у вигляді простого dict
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
        print("answer")
        desc = RTCSessionDescription(sdp=data["answer"]["sdp"], type=data["answer"]["type"])
        await self.pc.setRemoteDescription(desc)
        print("send")

    async def _on_ice(self, data):
        # отримали ICE-кандидат
        await self.pc.addIceCandidate(data["candidate"])





