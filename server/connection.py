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

# Список всіх активних користувачів
active_participants = set()

# Завантаження збереження файлу
def load_info(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_info(path: str, info: dict):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def connection_events(sio):

    @sio.on('gen_personal_id')
    def gen_meet_code():
        while True:
            personal_id = int( str(secrets.randbelow(10**6)).zfill(6) )
            if personal_id not in active_participants:
                active_participants.add(personal_id)
                break
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
                save_info(path, info)
                sio.emit('new_meet_ids', {'meet_id' : owner_id, 'meet_password' : meet_password}, room=request.sid)


    @sio.on('register_new_participant')
    def register_new_participant(data):
        participant_id = data['id']
        path = f'./code_{participant_id}.json'
        if not os.path.exists(path):
            return

        info = load_info(path)
        ids = {p["participant_id"] for p in info['participants']}
        if participant_id not in ids:
            participant = {"participant_id" : participant_id,
                           "emotions" : [],
                           "camera" : False,
                           "hand_raised" : False}
            info["participants"].append(participant)
            save_info(path, info)


    @sio.on('remove_participant')
    def remove_participant(data):
        participant_id = data['id']
        path = f'./code_{participant_id}.json'
        if not os.path.exists(path):
            return


        info = load_info(path)
        #записати всіх учасників, крім того, що має id, яке треба видалити
        info["participants"] = [p for p in info["participants"] if p["participant_id"] != participant_id]
        save_info(path, info)
    # @sio.on('connect'):