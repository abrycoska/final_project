import json
import os
import threading
import time
import eventlet


lock = threading.Lock()

DIR = os.path.join(os.path.dirname(__file__), '..', 'active_meets/')
if not os.path.exists(DIR):
    os.makedirs(DIR)

# список всіх активних користувачів
occupied_ids = set()
meetings = {}

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
            for k, meet in meetings.values():
                try:
                    alone_time = time.time() - meetings["part_dscn_time"]
                    participant = load_info(meet['path'])
                    if alone_time > 120 and participant == {}:
                        meetings.pop(k, None)
                except Exception:
                    pass
            eventlet.sleep(30)

    sio.start_background_task(cleanup)