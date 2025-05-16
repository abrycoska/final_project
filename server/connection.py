import asyncio
import time
import secrets
from aiortc import RTCPeerConnection, RTCIceCandidate, RTCSessionDescription
from aiortc.contrib.media import MediaRelay
from flask import request


# meet_code_bp = Blueprint('meet_code_bp', __name__)
# @meet_code_bp.route('/gen_meet_code', methods=['POST'])
# def gen_meet_code():
#     return '325 632', 200

# папка з файлами зустрічей

from server.meet_management import *
relay = MediaRelay()


def connection_events(sio):
    # при створенні, відправляє id, який буде використаний як код конфи,
    # якщо обрати вчителем
    @sio.on('gen_personal_id')
    def gen_meet_code():
        print('--- gen_personal_id')
        while True:
            personal_id = str(secrets.randbelow(10**2)).zfill(2)
            if personal_id not in occupied_ids:
                occupied_ids.add(personal_id)
                break
        meet_password = str(secrets.randbelow(10**2)).zfill(2)
        ids: dict[str, str] = {'personal_id' : personal_id, 'meet_password' : meet_password}
        print(ids)
        return ids

    @sio.on('register_new_meet')
    def register_new_meet(ids):
        print('Registering new meet')
        owner_id = ids['personal_id']
        meet_password = ids['meet_password']

        path = f'{DIR}code_{owner_id}.json'
        with lock:
            if owner_id not in meetings.keys():
                meetings[owner_id] = {"owner_active" : True,
                                      "meet_password" : meet_password,
                                      "part_dscn_time": time.time(),
                                      "pcs" : {},
                                      "path": path}
                info = {}
                save_info(path, info)
            else:
                meetings[owner_id]["owner_active"] = True


    @sio.on('join_meet')
    def join_meet(supposed_ids):
        meet_id = supposed_ids['meet_id']
        supposed_password = supposed_ids['meet_password']
        personal_id = supposed_ids['personal_id']

        if meet_id not in meetings.keys():
            return False

        real_password = meetings[meet_id]['meet_password']
        # якщо паролі співпали, то додає
        if real_password == supposed_password:
            with lock:
                info = load_info(meetings[meet_id]['path'])

                info[f"{personal_id}"] = {'emotions': [],
                                          'camera': False,
                                          'hand_raised': False}
                save_info(meetings[meet_id]['path'], info)

            return True
        else:
            return False

    @sio.on('disconnect_participant')
    def disconnect_participant(leaving_participant):
        meet_id = leaving_participant["meet_id"]
        personal_id = leaving_participant["personal_id"]
        if leaving_participant["role"] == "Teacher":
            meetings[meet_id]["owner_active"] = False

        else:
            with lock:
                path = meetings[meet_id]['path']
                info = load_info(path)
                info.pop(personal_id, None)
                save_info(path, info)

        pcs = meetings[meet_id]['pcs']
        pc = pcs.pop(personal_id, None)
        if pc:
            asyncio.create_task(pc.close())

        meetings[meet_id]["part_num_changed_time"] = time.time()

    @sio.on('webrtc_offer')
    def webrtc_offer(data):
        sid = request.sid
        sio.start_background_task(lambda: asyncio.run(offer_handler(sid, data)))

    async def offer_handler(sid, data):
        print(1)

        personal_id = data['personal_id']
        meet_id = data['meet_id']
        offer = data["offer"]
        pcs = meetings[meet_id]['pcs']

        pc = RTCPeerConnection()
        pcs[personal_id] = pc

        @pc.on("track")
        async def on_track(track):
            relay_track = relay.subscribe(track)

            for other_id, other_pc in pcs.items():
                if other_id != personal_id:
                    other_pc.addTrack(relay_track)

        # приймаємо Offer
        description = RTCSessionDescription(sdp=offer["sdp"], type=offer["type"])
        await pc.setRemoteDescription(description)
        # відповідаємо Answer
        answer = await pc.createAnswer()

        @pc.on("icecandidate")
        async def on_icecandidate(candidate):
            print('++')
            if candidate:
                candidate_data = {
                    "candidate" : candidate.candidate,
                    "sdpMid" : candidate.sdpMid,
                    "sdpMLineIndex" : candidate.sdpMLineIndex}
                await sio.emit("webrtc_ice_candidate", {"candidate" : candidate_data}, room=sid)

        #після setLocalDescription вже починає збирати айс-кандидата
        await pc.setLocalDescription(answer)
        await sio.emit("webrtc_answer", {
            "answer": {
               "sdp": pc.localDescription.sdp,
               "type": pc.localDescription.type}
            },
            room=sid)
        print(5)


    @sio.on('webrtc_ice_candidate')
    async def webrtc_ice_candidate(data):
        print('--')
        personal_id = data['personal_id']
        meet_id = data['meet_id']
        pcs = meetings[meet_id]['pcs']
        pc = pcs.get(personal_id)
        if pc:
            await pc.addIceCandidate(data["candidate"])

def connection_management(sio):
    connection_events(sio)
    cleanup_func(sio)

