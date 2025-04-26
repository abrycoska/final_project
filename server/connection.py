import json
import random
from flask import request

# meet_code_bp = Blueprint('meet_code_bp', __name__)

# @meet_code_bp.route('/gen_meet_code', methods=['POST'])
# def gen_meet_code():
#     return '325 632', 200

active_meet_id_list = {}

def connection_events(sio):
    @sio.on('gen_personal_code')
    def gen_meet_code():

        code = str(random.randint(1000, 9999))
        participant_list = [request.sid]
        active_meet_id_list[code] = participant_list
        sio.emit('personal_code_generated', {'code' : code}, room=request.sid)
        print(active_meet_id_list)
    # @sio.on('connect'):