import json
import random
import os
import secrets
from datetime import datetime
from flask import request

# meet_code_bp = Blueprint('meet_code_bp', __name__)

# @meet_code_bp.route('/gen_meet_code', methods=['POST'])
# def gen_meet_code():
#     return '325 632', 200



def connection_events(sio):

    @sio.on('gen_personal_id')
    def gen_meet_code():
        personal_id = int( str(secrets.randbelow(10**6)).zfill(6) )
        meet_password = int( str(secrets.randbelow(10**8)).zfill(8) )
        sio.emit('personal_id_generated', {'id' : personal_id, 'meet_password' : meet_password}, room=request.sid)


    @sio.on('register_new_meet')
    def register_new_meet(data):
        owner_id = data['id']

        while True:
            path = f'./code_{owner_id}.json'
            if not os.path.exists(path):
                meet_password = int( str(secrets.randbelow(10**10)).zfill(10))

                info =  { "owner_id": owner_id,
                          "meet_password" : meet_password,
                          "start_time": datetime.utcnow().isoformat(),
                          "participants": [] }
                with open(path, 'w') as f:
                    json.dump(info, f)
                sio.emit('new_meet_ids', {'meet_id' : owner_id, 'meet_password' : meet_password}, room=request.sid)


    @sio.on('register_new_participant')
    def register_new_participant(data):
        participant_id = data['id']
        path = f'./code_{participant_id}.json'
        if not os.path.exists(path):
            return

        with open(path, 'r', encoding="utf-8") as f:
            info = json.load(f)
            ids = {p["participant_id"] for p in info['participants']}
            if participant_id not in ids:
                participant = {"participant_id" : participant_id,
                               "emotions" : [],
                               "camera" : False,
                               "hand_raised" : False}
                info["participants"].append(participant)
                json.dump(info, f)

    @sio.on('remove_participant')
    def remove_participant(data):
        participant_id = data['id']
        path = f'./code_{participant_id}.json'
        if not os.path.exists(path):
            return

        with open(path, 'r', encoding="utf-8") as f:
            info = json.load(f)
            #записати всіх учасників, крім того, що має id, яке треба видалити
            info["participants"] = [p for p in info["participants"] if p["participant_id"] != participant_id]
            json.dump(info, f)

    # @sio.on('connect'):