import asyncio
import time
import secrets
from aiortc import RTCPeerConnection, RTCIceCandidate, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaRelay
from flask import request
from server.meet_management import *

relay = MediaRelay()

def connection_events(sio):
    @sio.on('gen_personal_id')
    def gen_meet_code():
        print('--- gen_personal_id')
        while True:
            personal_id = str(secrets.randbelow(10**2)).zfill(2)
            if personal_id not in occupied_ids:
                occupied_ids.add(personal_id)
                break
        meet_password = str(secrets.randbelow(10**2)).zfill(2)
        ids = {'personal_id': personal_id, 'meet_password': meet_password}
        print(f"SERVER: Generated IDs: {ids}")
        return ids

    @sio.on('register_new_meet')
    def register_new_meet(ids):
        print(f"SERVER: Registering new meet with IDs: {ids}")
        owner_id = ids['personal_id']
        meet_password = ids['meet_password']
        path = f'{DIR}code_{owner_id}.json'
        with lock:
            if owner_id not in meetings.keys():
                meetings[owner_id] = {
                    "owner_active": True,
                    "meet_password": meet_password,
                    "part_dscn_time": time.time(),
                    "pcs": {},
                    "relay_tracks": [],
                    "path": path
                }
                info = {}
                save_info(path, info)
            else:
                meetings[owner_id]["owner_active"] = True

    @sio.on('join_meet')
    def join_meet(supposed_ids):
        print(f"SERVER: Join meet request: {supposed_ids}")
        meet_id = supposed_ids['meet_id']
        supposed_password = supposed_ids['meet_password']
        personal_id = supposed_ids['personal_id']
        if meet_id not in meetings.keys():
            print(f"SERVER: Meet {meet_id} not found")
            return False
        real_password = meetings[meet_id]['meet_password']
        if real_password == supposed_password:
            with lock:
                info = load_info(meetings[meet_id]['path'])
                info[f"{personal_id}"] = {'emotions': [], 'camera': False, 'micro': False, 'hand_raised': False}
                save_info(meetings[meet_id]['path'], info)
            print(f"SERVER: Join successful for {personal_id} in meet {meet_id}")
            return True
        else:
            print(f"SERVER: Invalid password for meet {meet_id}")
            return False

    @sio.on('disconnect_participant')
    def disconnect_participant(leaving_participant):
        print(f"SERVER: Disconnect participant: {leaving_participant}")
        meet_id = leaving_participant["meet_id"]
        personal_id = leaving_participant["personal_id"]
        if not meetings.get(meet_id, None):
            print(f"SERVER: Meet {meet_id} not found for disconnect")
            return
        if leaving_participant["role"] == "teacher":
            meetings[meet_id]["owner_active"] = False
        else:
            with lock:
                path = meetings[meet_id]['path']
                info = load_info(path)
                info.pop(personal_id, None)
                save_info(path, info)
        pcs = meetings[meet_id]['pcs']
        pc = pcs.pop(personal_id, None)
        occupied_ids.discard(personal_id)
        if pc:
            asyncio.create_task(pc.close())
        meetings[meet_id]["part_dscn_time"] = time.time()

    @sio.on('webrtc_offer')
    def webrtc_offer(data):
        print(f"SERVER: Received WebRTC offer: {data}")
        role = data.get('role')
        sid = request.sid
        def runner():
            asyncio.run(handle_offer(sid, data, role))
        threading.Thread(target=runner, daemon=True).start()

    async def handle_offer(sid, data, role):
        meet_id = data['meet_id']
        personal_id = data['personal_id']
        session = meetings.get(meet_id)
        if not session:
            print(f"SERVER: No session for meet_id {meet_id}")
            return
        configuration = RTCConfiguration(
            iceServers=[RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
        )
        pc = RTCPeerConnection(configuration=configuration)
        session['pcs'][personal_id] = pc
        if role == "teacher":
            pc.addTransceiver("video", direction="recvonly")  # For student's video (not used now)
            pc.addTransceiver("video", direction="recvonly")  # For student's screen (not used now)
        else:
            pc.addTransceiver("video", direction="sendonly")  # Relay teacher's video to student
            pc.addTransceiver("video", direction="sendonly")  # Relay teacher's screen to student
        for owner, track in session['relay_tracks']:
            if owner != personal_id:
                print(f"SERVER: Adding track to {personal_id}: kind={track.kind}, id={track.id}")
                pc.addTrack(track)
        @pc.on("track")
        async def on_track(track):
            print(f"SERVER: Received track: kind={track.kind}, id={track.id}")
            if role == "student" and track.kind != "audio":
                return  # Students don't send video/screen for now
            relay_track = relay.subscribe(track)
            session['relay_tracks'].append((personal_id, relay_track))
            print(f"SERVER: Relay tracks updated: {[(pid, t.id) for pid, t in session['relay_tracks']]}")
            for other_pid, other_pc in session['pcs'].items():
                if other_pid != personal_id:
                    print(f"SERVER: Relaying track {track.id} to {other_pid}")
                    other_pc.addTrack(relay_track)

        @pc.on("iceconnectionstatechange")
        def _on_ice_connection_state_change():
            print("CLIENT-SIDE GOT IE CONNECTION STATE:", pc.iceConnectionState)

        @pc.on("icecandidate")
        async def on_icecandidate(candidate):
            if candidate:
                candidate_data = {
                    "candidate": candidate.candidate,
                    "sdpMid": candidate.sdpMid,
                    "sdpMLineIndex": candidate.sdpMLineIndex
                }
                print(f"SERVER: Sending ICE candidate to {sid}: {candidate_data}")
                sio.emit("webrtc_ice_candidate", {"candidate": candidate_data}, room=sid)
        offer = data.get('offer')
        print(f"SERVER: Received Offer: {offer['sdp']}")
        description = RTCSessionDescription(sdp=offer["sdp"], type=offer["type"])
        await pc.setRemoteDescription(description)
        print("SERVER: Accepted offer, creating Answer")
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        print(f"SERVER: Sending Answer: {pc.localDescription.sdp}")
        sio.emit("webrtc_answer", {
            "answer": {
                "sdp": pc.localDescription.sdp,
                "type": pc.localDescription.type
            }
        }, room=sid)

    @sio.on("webrtc_ice_candidate")
    async def on_webrtc_ice_candidate(data):
        print(f"SERVER: Received ICE candidate: {data['candidate']}")
        meet_id = data['meet_id']
        personal_id = data['personal_id']
        session = meetings.get(meet_id)
        if not session:
            print(f"SERVER: No session for meet_id {meet_id}")
            return
        pc = session['pcs'].get(personal_id)
        if not pc:
            print(f"SERVER: No PeerConnection for personal_id {personal_id}")
            return
        candidate = RTCIceCandidate(
            candidate=data['candidate']['candidate'],
            sdpMid=data['candidate']['sdpMid'],
            sdpMLineIndex=data['candidate']['sdpMLineIndex']
        )
        await pc.addIceCandidate(candidate)
        print(f"SERVER: Added ICE candidate for {personal_id}")


def connection_management(sio):
    connection_events(sio)
    cleanup_func(sio)

