import json
import os
import eventlet
import secrets
from datetime import datetime
from glob import glob
from flask import request

# meet_code_bp = Blueprint('meet_code_bp', __name__)
# @meet_code_bp.route('/gen_meet_code', methods=['POST'])
# def gen_meet_code():
#     return '325 632', 200

# папка з файлами зустрічей
DIR = os.path.join(os.path.dirname(__file__), '..', 'active_meets/')
if not os.path.exists(DIR):
    os.makedirs(DIR)

# список всіх активних користувачів
occupied_ids = set()

# завантаження збереження файлу
def load_info(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_info(path: str, info: dict):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def cleanup_func(sio):
    # кожні 30 секунд перевіряє і видаляє json завершених конференцій
    # якщо власник не серед активних учасників та список учасників порожній
    def cleanup():
        while True:
            for file_path in glob(f"{DIR}code_*.json"):
                try:
                    info = load_info(file_path)
                    active = info["owner_active"]
                    participant = info["participants"]
                    print(file_path, active, participant)
                    if not active and participant == {}:
                        os.remove(file_path)
                except Exception:
                    pass
            eventlet.sleep(30)

    sio.start_background_task(cleanup)


def connection_events(sio):
    # при створенні, відправляє id, який буде використаний як код конфи,
    # якщо обрати вчителем
    @sio.on('gen_personal_id')
    def gen_meet_code():
        while True:
            personal_id = str(secrets.randbelow(10**2)).zfill(2)
            if personal_id not in occupied_ids:
                occupied_ids.add(personal_id)
                break
        meet_password = str(secrets.randbelow(10**2)).zfill(2)
        ids: dict[str, str] = {'personal_id' : personal_id, 'meet_password' : meet_password}
        return ids


    @sio.on('register_new_meet')
    def register_new_meet(ids):
        owner_id = ids['personal_id']
        meet_password = ids['meet_password']

        path = f'{DIR}code_{owner_id}.json'
        if not os.path.exists(path):
            info =  { "owner_id": owner_id,
                      "owner_active" : True,
                      "meet_password" : meet_password,
                      "start_time": datetime.utcnow().isoformat(),
                      "participants": {} }
            save_info(path, info)
        else:
            info = load_info(path)
            info["owner_active"] = True
            save_info(path, info)

    @sio.on('join_meet')
    def join_meet(supposed_ids):
        print('supposed_ids', supposed_ids is not None)
        meet_id = supposed_ids['meet_id']
        supposed_password = supposed_ids['meet_password']
        personal_id = supposed_ids['personal_id']
        path = f'{DIR}code_{meet_id}.json'
        if not os.path.exists(path):
            return False

        info = load_info(path)
        real_password = info['meet_password']

        # якщо паролі співпали, то додає
        if real_password == supposed_password:
            info["participants"][f"{personal_id}"] = {'emotions' : [],
                                                      'camera' : False,
                                                      'hand_raised': False}
            save_info(path, info)
            return True
        else:
            return False


    @sio.on('disconnect_participant')
    def disconnect_participant(actor):

        if actor["Teacher"]:
            path = f"{DIR}code_{actor['personal_id']}.json"
            info = load_info(path)
            info["owner_active"] = False
            save_info(path, info)

        else:
            path = f"{DIR}code_{actor['meet_id']}.json"
            info = load_info(path)
            info["participants"].pop(actor["personal_id"], None)
            save_info(path, info)
