from flask import Flask, request, jsonify
import redis
import json
import os
import logging
from datetime import datetime
from messengerdb import db, Messenger
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps
from email_validator import validate_email
from password_lib.utils import PasswordUtil


TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
BEGINNING_OF_DATE = datetime(1970, 1, 1, 0, 0, 0)

app = Flask(__name__)
password_util = PasswordUtil()


# Configuration
class Config:
    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    MYSQL_HOST = os.getenv("MYSQL_HOST")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CHECK_SECURE_PASSWORD = True


app.config.from_object(Config)

# Initialize Redis client
redis_client = redis.StrictRedis(
    host=app.config["REDIS_HOST"], port=app.config["REDIS_PORT"]
)

# Initialize SQLAlchemy
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

messenger_db = Messenger(app)

# Logger setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def session_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.headers.get("Session-Id")
        user_id = int(request.headers.get("User-Id"))
        if not session_id or not user_id:
            return jsonify(message="Session-Id and User-Id required"), 401
        result = messenger_db.user.is_session_valid(user_id, session_id)
        if not result:
            return jsonify(message="Invalid session"), 401

        return f(*args, **kwargs)

    return decorated_function


@app.route("/api/user/is_session_valid", methods=["POST"])
def user_is_session_valid():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        session_id = data.get("session_id")
        result = messenger_db.user.is_session_valid(user_id, session_id)
        return jsonify({"success": result})
    except Exception as e:
        logger.debug(f"Error validating session: {e}")
        return jsonify({"success": False}), 500


@app.route("/api/user/logout", methods=["POST"])
@session_required
def user_logout():
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        result = messenger_db.user.logout(session_id)
        return jsonify({"success": result})
    except Exception as e:
        logger.debug(f"Error logging out: {e}")
        return jsonify({"success": False}), 500


@app.route("/api/user/find_by_username", methods=["POST"])
@session_required
def user_find_by_username():
    try:
        data = request.get_json()
        username = data.get("username")
        limit = data.get("limit", 100)
        offset = data.get("offset", 0)
        result = messenger_db.user.find_by_username(username, limit, offset)
        return jsonify({"result": result})
    except Exception as e:
        logger.debug(f"Error finding user by username: {e}")
        return jsonify({"success": False}), 500


@app.route("/api/user/login", methods=["POST"])
def user_login():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        session_id, user_id, name, email = messenger_db.user.login(username, password)
        return jsonify(
            {
                "success": True,
                "session_id": session_id,
                "user_id": user_id,
                "name": name,
                "email": email,
            }
        )
    except Exception as e:
        logger.debug(f"Error logging in: {e}")
        return jsonify({"success": False}), 500


@app.route("/api/user/register", methods=["POST"])
def user_register():
    try:
        data = request.get_json()
        username = data.get("username")
        name = data.get("name")
        password = data.get("password")
        if app.config["CHECK_SECURE_PASSWORD"]:
            if not password_util.is_secure(password):
                return jsonify({"success": False}), 500

        email = data.get("email")
        emailinfo = validate_email(email, check_deliverability=False)
        email = emailinfo.normalized

        messenger_db.user.register(username, name, password, email)
        return jsonify({"success": True})
    except SQLAlchemyError as e:
        logger.debug(f"Database error: {e}")
        return jsonify({"success": False}), 500
    except Exception as e:
        logger.debug(f"Error registering user: {e}")
        return jsonify({"success": False}), 500


@app.route("/api/user/find_by_user_id", methods=["POST"])
@session_required
def user_find_by_user_id():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        result = messenger_db.user.find_by_user_id(user_id)
        return jsonify(result)
    except Exception as e:
        logger.debug(f"Error finding user by ID: {e}")
        return jsonify({"success": False}), 500


@app.route("/api/user/chat_list", methods=["POST"])
@session_required
def user_chat_list():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        limit = data.get("limit", 100)
        offset = data.get("offset", 0)
        result = messenger_db.user.chat_list(user_id, limit, offset)
        return jsonify(result)
    except Exception as e:
        logger.debug(f"Error getting chat list: {e}")
        return jsonify({"success": False}), 500


@app.route("/api/user/update", methods=["PUT"])
@session_required
def user_update():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        username = data.get("username")
        name = data.get("name")
        password = data.get("password")
        if app.config["CHECK_SECURE_PASSWORD"]:
            if not password_util.is_secure(password):
                return jsonify({"success": False}), 500

        email = data.get("email")
        emailinfo = validate_email(email, check_deliverability=False)
        email = emailinfo.normalized

        messenger_db.user.update(user_id, username, name, password, email)
        return jsonify({"success": True})
    except Exception as e:
        logger.debug(f"Error updating user: {e}")
        return jsonify({"success": False}), 500


@app.route("/api/user/delete", methods=["DELETE"])
@session_required
def user_delete():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        messenger_db.user.delete(user_id)
        return jsonify({"success": True})
    except Exception as e:
        logger.debug(f"Error deleting user: {e}")
        return jsonify({"success": False}), 500


@app.route("/api/public/send_message", methods=["POST"])
@session_required
def public_send_message():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        message = data.get("message")
        name = data.get("name")
        room_name = data.get("room_name")
        row = messenger_db.public.send_message(user_id, message, room_name)
        redis_client.publish("public_room", json.dumps((*row, name)))
        return jsonify({"success": True})
    except Exception as e:
        logger.debug(f"Error sending public message: {e}")
        return jsonify({"success": False}), 500


@app.route("/api/public/read_messages", methods=["POST"])
@session_required
def public_read_messages():
    try:
        data = request.get_json()
        limit = data.get("limit", 100)
        offset = data.get("offset", 0)
        timestamp = data.get("timestamp", "")
        if timestamp == "":
            timestamp = BEGINNING_OF_DATE
        result = messenger_db.public.read_messages(limit, offset, timestamp)
        return jsonify({"messages": result})
    except Exception as e:
        logger.debug(f"Error reading public messages: {e}")
        return jsonify({"success": False}), 500


@app.route("/api/private/send_message", methods=["POST"])
@session_required
def private_send_message():
    try:
        data = request.get_json()
        sender_id = data.get("sender_id")
        receiver_id = data.get("receiver_id")
        message = data.get("message")
        name = data.get("name")
        row = messenger_db.private.send_message(sender_id, receiver_id, message)
        redis_client.publish(f"user-{sender_id}", json.dumps((*row, "Me")))
        redis_client.publish(f"user-{receiver_id}", json.dumps((*row, name)))
        return jsonify({"success": True})
    except Exception as e:
        logger.debug(f"Error sending private message: {e}")
        return jsonify({"success": False}), 500


@app.route("/api/private/read_messages", methods=["POST"])
@session_required
def private_read_messages():
    try:
        data = request.get_json()
        sender_id = data.get("sender_id")
        receiver_id = data.get("receiver_id")
        limit = data.get("limit", 100)
        offset = data.get("offset", 0)
        timestamp = data.get("timestamp", "")
        if timestamp == "":
            timestamp = BEGINNING_OF_DATE
        result = messenger_db.private.read_messages(
            sender_id, receiver_id, limit, offset, timestamp=timestamp
        )
        return jsonify({"messages": result})
    except Exception as e:
        logger.debug(f"Error reading private messages: {e}")
        return jsonify({"success": False}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=13247)
