



# Збереження останніх емоцій
student_emotions = {}

# === Роут для прийому емоцій студентів ===
@app.route('/send_emotion', methods=['POST'])
def receive_emotion():
    data = request.json
    student_id = data.get('student_id')
    emotion = data.get('emotion')
    event_type = data.get('event')  # "periodic" або "reaction"
    timestamp = data.get('timestamp', datetime.datetime.now().isoformat())

    # Зберігаємо
    student_emotions[student_id] = {
        "emotion": emotion,
        "event": event_type,
        "timestamp": timestamp
    }

    # Запис у лог-файл
    save_to_log(data)

    return jsonify({"status": "ok"}), 200

# === Подія: викладач натискає "жарт" / "погана новина" / "перевірка уваги" ===
@socketio.on('teacher_event')
def handle_teacher_event(data):
    """
    data = {
        'type': 'joke' / 'bad_news' / 'attention',
        'message': 'Викладач сказав жарт...'
    }
    """
    # Транслюємо студентам
    emit('event_triggered', data, broadcast=True)

# === Подія: студент хоче звернутися ===
@socketio.on('student_request')
def handle_student_request(data):
    """
    data = {
        'student_id': 's123',
        'message': 'Хочу поставити запитання'
    }
    """
    # Передаємо викладачу
    emit('student_signal', data, broadcast=True)

# === Запис у лог-файл ===
def save_to_log(entry):
    os.makedirs("logs", exist_ok=True)
    with open("logs/emotions_log.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")

# === Запуск ===

