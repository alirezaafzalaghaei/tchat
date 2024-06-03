from flask_sqlalchemy import SQLAlchemy
import hashlib
import secrets
import datetime
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound
from beartype.typing import List, Tuple, Optional

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Initialize the database
db = SQLAlchemy()

CURRENT_TIMESTAMP = lambda: datetime.datetime.now(datetime.timezone.utc)


# Define the Users model
class Users(db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16), unique=True, nullable=False)
    name = db.Column(db.String(32), nullable=False)
    password = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=CURRENT_TIMESTAMP)
    public_room_messages = db.relationship(
        "PublicRoomMessages", order_by="PublicRoomMessages.id", back_populates="user"
    )
    sent_chats = db.relationship(
        "UserChat", foreign_keys="UserChat.sender_id", back_populates="sender"
    )
    received_chats = db.relationship(
        "UserChat", foreign_keys="UserChat.receiver_id", back_populates="receiver"
    )
    sessions = db.relationship("Session", back_populates="user")


# Define the PublicRoomMessages model
class PublicRoomMessages(db.Model):
    __tablename__ = "PublicRoomMessages"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id"))
    message = db.Column(db.Text, nullable=False)
    room_name = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.TIMESTAMP, default=CURRENT_TIMESTAMP)
    user = db.relationship("Users", back_populates="public_room_messages")

    def to_tuple(self) -> Tuple[int, int, str, str, str]:
        return (
            self.id,
            self.user_id,
            self.message,
            self.room_name,
            self.formatted_timestamp,
        )

    @property
    def formatted_timestamp(self) -> str:
        return self.timestamp.strftime(TIME_FORMAT)


# Define the UserChat model
class UserChat(db.Model):
    __tablename__ = "UserChats"
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("Users.id"))
    receiver_id = db.Column(db.Integer, db.ForeignKey("Users.id"))
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.TIMESTAMP, default=CURRENT_TIMESTAMP)
    sender = db.relationship(
        "Users", foreign_keys=[sender_id], back_populates="sent_chats"
    )
    receiver = db.relationship(
        "Users", foreign_keys=[receiver_id], back_populates="received_chats"
    )

    def to_tuple(self) -> Tuple[int, int, int, str, str]:
        return (
            self.id,
            self.sender_id,
            self.receiver_id,
            self.message,
            self.formatted_timestamp,
        )

    @property
    def formatted_timestamp(self) -> str:
        return self.timestamp.strftime(TIME_FORMAT)


# Define the Session model
class Session(db.Model):
    __tablename__ = "Sessions"
    session_id = db.Column(db.String(32), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id"))
    login_time = db.Column(db.TIMESTAMP, default=CURRENT_TIMESTAMP)
    user = db.relationship("Users", back_populates="sessions")


# Database connection and session management
class DatabaseConnection:
    def __init__(self, app):
        self.app = app
        with self.app.app_context():
            db.create_all()


class UserManager:
    def __init__(self, session) -> None:
        self.session = session

    def register(self, username: str, name: str, password: str, email: str) -> None:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        new_user = Users(
            username=username, name=name, password=hashed_password, email=email
        )
        self.session.add(new_user)
        self.session.commit()

    def login(
        self, username: str, password: str
    ) -> Optional[Tuple[str, int, str, str]]:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        try:
            user = (
                self.session.query(Users)
                .filter_by(username=username, password=hashed_password)
                .one()
            )
            session_id = secrets.token_hex(16)
            new_session = Session(session_id=session_id, user_id=user.id)
            self.session.add(new_session)
            self.session.commit()
            return session_id, user.id, user.name, user.email
        except NoResultFound:
            return None

    def is_session_valid(self, user_id: int, session_id: str) -> bool:
        session_info = (
            self.session.query(Session)
            .filter_by(session_id=session_id, user_id=user_id)
            .first()
        )
        return bool(session_info)

    def logout(self, session_id: str) -> None:
        self.session.query(Session).filter_by(session_id=session_id).delete()
        self.session.commit()

    def find_by_username(
        self, username: str, limit: int = 5, offset: int = 0
    ) -> List[Tuple[int, str]]:
        users = (
            self.session.query(Users)
            .filter(Users.username.like(f"%{username}%"))
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [(user.id, user.username) for user in users]

    def find_by_user_id(self, user_id: int) -> Optional[Tuple[int, str, str, str]]:
        user = self.session.query(Users).filter_by(id=user_id).first()
        return (user.id, user.username, user.name, user.email) if user else None

    def chat_list(
        self, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[Tuple[int, str]]:
        subquery = (
            self.session.query(UserChat.sender_id.label("intr"))
            .filter(UserChat.receiver_id == user_id)
            .union(
                self.session.query(UserChat.receiver_id.label("intr")).filter(
                    UserChat.sender_id == user_id
                )
            )
            .subquery()
        )

        chat_users = (
            self.session.query(Users.id, Users.username)
            .join(subquery, Users.id == subquery.c.intr)
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [(chat.id, chat.username) for chat in chat_users]

    def update(
        self, user_id: int, username: str, name: str, password: str, email: str
    ) -> None:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        self.session.query(Users).filter_by(id=user_id).update(
            {
                Users.name: name,
                Users.password: hashed_password,
                Users.email: email,
                Users.username: username,
            }
        )
        self.session.commit()

    def delete(self, user_id: int) -> None:
        self.session.query(Users).filter_by(id=user_id).delete()
        self.session.commit()


class PublicManager:
    def __init__(self, session) -> None:
        self.session = session

    def send_message(
        self, user_id: int, message: str, room_name: str
    ) -> Tuple[int, int, str, str, str]:
        new_message = PublicRoomMessages(
            user_id=user_id, message=message, room_name=room_name
        )
        self.session.add(new_message)
        self.session.commit()
        return new_message.to_tuple()

    def read_messages(
        self,
        limit: int = 100,
        offset: int = 0,
        timestamp: datetime.datetime = datetime.datetime.now(),
    ) -> List[Tuple[int, str, str, str]]:
        messages = (
            self.session.query(PublicRoomMessages, Users.name)
            .join(Users, PublicRoomMessages.user_id == Users.id)
            .filter(PublicRoomMessages.timestamp > timestamp)
            .order_by(PublicRoomMessages.timestamp.asc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [
            (
                msg.PublicRoomMessages.user_id,
                msg.PublicRoomMessages.message,
                msg.PublicRoomMessages.formatted_timestamp,
                msg.name,
            )
            for msg in messages
        ]


class PrivateManager:
    def __init__(self, session) -> None:
        self.session = session

    def send_message(
        self, sender_id: int, receiver_id: int, message: str
    ) -> Tuple[int, int, int, str, str]:
        new_message = UserChat(
            sender_id=sender_id, receiver_id=receiver_id, message=message
        )
        self.session.add(new_message)
        self.session.commit()
        return new_message.to_tuple()

    def read_messages(
        self,
        sender_id: int,
        receiver_id: int,
        limit: int = 100,
        offset: int = 0,
        timestamp: datetime.datetime = datetime.datetime.now(),
    ) -> List[Tuple[int, str, int, str, str, str]]:

        sender_alias = aliased(Users, name="sender")
        receiver_alias = aliased(Users, name="receiver")

        messages = (
            self.session.query(
                UserChat,
                sender_alias.name.label("sender_name"),
                receiver_alias.name.label("receiver_name"),
            )
            .join(sender_alias, UserChat.sender_id == sender_alias.id)
            .join(receiver_alias, UserChat.receiver_id == receiver_alias.id)
            .filter(
                (
                    (UserChat.sender_id == sender_id)
                    & (UserChat.receiver_id == receiver_id)
                )
                | (
                    (UserChat.sender_id == receiver_id)
                    & (UserChat.receiver_id == sender_id)
                )
            )
            .filter(UserChat.timestamp > timestamp)
            .order_by(UserChat.timestamp.asc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [
            (
                msg.UserChat.sender_id,
                msg.sender_name,
                msg.UserChat.receiver_id,
                msg.receiver_name,
                msg.UserChat.message,
                msg.UserChat.formatted_timestamp,
            )
            for msg in messages
        ]


# Messenger class
class Messenger:
    def __init__(self, app):
        self.db_connection = DatabaseConnection(app)
        self.user = UserManager(db.session)
        self.public = PublicManager(db.session)
        self.private = PrivateManager(db.session)
