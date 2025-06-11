import asyncio
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
    async def cleanup():
        while True:
            for meet_id, meet in list(meetings.items()):
                try:
                    alone_time = time.time() - meet.get("part_dscn_time",0)
                    participant = load_info(meet['path'])

                    if alone_time > 120 and not participant:
                        for pc in meet.get('pcs', {}).values():
                            if callable(getattr(pc, "close", None)):
                                await pc.close

                        meetings.pop(meet_id, None)
                except Exception:
                    pass
            await asyncio.sleep(30)

    def run_cleanup():
        loop = asyncio.new_event_loop()  # Створюємо новий цикл подій
        asyncio.set_event_loop(loop)
        loop.run_until_complete(cleanup())  # Запускаємо корутину

    threading.Thread(target=run_cleanup, daemon=True).start()