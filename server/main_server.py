import eventlet

eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO
from server.connection import  connection_management


app = Flask(__name__)
# app.register_blueprint(meet_code_bp)

socketio = SocketIO(app,
                    cors_allowed_origins="*",
                    async_mode='eventlet',
                    ping_interval=30,
                    logger=True,
                    ping_timeout=5)

connection_management(socketio)

@app.route('/')
def index():
    return 'Server is up and running'

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
