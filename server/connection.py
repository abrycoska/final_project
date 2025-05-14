import time
import secrets
from aiortc import RTCPeerConnection
from aiortc.contrib.media import MediaRelay

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

        # path = f'{DIR}code_{owner_id}.json'
        # if not os.path.exists(path):
        #     info =  { "owner_id": owner_id,
        #               "owner_active" : True,
        #               "meet_password" : meet_password,
        #               "start_time": datetime.utcnow().isoformat(),
        #               "participants": {} }
        #     save_info(path, info)
        # else:
        #     info = load_info(path)
        #     info["owner_active"] = True
        #     save_info(path, info)

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
    def disconnect_participant(actor):
        meet_id = actor["meet_id"]
        if actor["role"] == "Teacher":
            meetings[meet_id]["owner_active"] = False

        else:
            with lock:
                path = meetings[meet_id]['path']
                info = load_info(path)
                info.pop(actor["personal_id"], None)
                save_info(path, info)
        meetings[meet_id]["part_num_changed_time"] = time.time()

    async def on_offer(data):
        personal_id = data['personal_id']
        meet_id = data['meet_id']
        pcs = meetings[meet_id]['pcs']

        pc = RTCPeerConnection()
        pcs[personal_id] = pc

        @pc.on("track")
        async def on_track(track):
            relay_track = relay.subscribe(track)

            for



def connection_management(sio):
    connection_events(sio)
    cleanup_func(sio)

    # @sio.on('join_meet')
    # def join_meet(supposed_ids):
    #     meet_id = supposed_ids['meet_id']
    #     supposed_password = supposed_ids['meet_password']
    #     personal_id = supposed_ids['personal_id']
    #     path = f'{DIR}code_{meet_id}.json'
    #     if not os.path.exists(path):
    #         return False
    #
    #     info = load_info(path)
    #     real_password = info['meet_password']
    #
    #     # якщо паролі співпали, то додає
    #     if real_password == supposed_password:
    #         info["participants"][f"{personal_id}"] = {'emotions' : [],
    #                                                   'camera' : False,
    #                                                   'hand_raised': False}
    #         save_info(path, info)
    #         return True
    #     else:
    #         return False


    # @sio.on('disconnect_participant')
    # def disconnect_participant(actor):
    #
    #     if actor["role"] == "Teacher":
    #         path = f"{DIR}code_{actor['personal_id']}.json"
    #         info = load_info(path)
    #         info["owner_active"] = False
    #         save_info(path, info)
    #
    #     else:
    #         path = f"{DIR}code_{actor['meet_id']}.json"
    #         info = load_info(path)
    #         info["participants"].pop(actor["personal_id"], None)
    #         save_info(path, info)
