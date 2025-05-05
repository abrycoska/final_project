import eventlet
from PyQt5.uic.Compiler.qobjectcreator import logger

eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO
from connection import  connection_events, cleanup_func


app = Flask(__name__)
# app.register_blueprint(meet_code_bp)

socketio = SocketIO(app,
                    cors_allowed_origins="*",
                    async_mode='eventlet',
                    ping_interval=10,
                    logger=True,
                    ping_timeout=5)
connection_events(socketio)
cleanup_func(socketio)

@app.route('/')
def index():
    return 'Server is up and running'

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
