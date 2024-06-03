import requests
from urllib.parse import urljoin
import json
from typing import Optional, List, Tuple, Any, Dict
import websocket
import ssl
from requests.packages.urllib3.exceptions import InsecureRequestWarning


class ServerMiddleware(requests.Session):
    def __init__(self, base_url: Optional[str] = None, verify=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = base_url
        self.verify = verify

    def request(self, method: str, url: str, *args, **kwargs) -> requests.Response:
        joined_url = urljoin(self.base_url, url)
        kwargs["verify"] = self.verify
        return super().request(method, joined_url, *args, **kwargs)


class UserManager:
    def __init__(self, session: ServerMiddleware):
        self.session = session

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.post(endpoint, json=data)
        return response.json()

    def is_session_valid(self, user_id: int, session_id: str) -> bool:
        data = {"user_id": user_id, "session_id": session_id}
        result = self._post("user/is_session_valid", data)
        if result.get("success"):
            self.session.cookies.set("session_id", session_id)
            self.session.headers.update(
                {"User-Id": str(user_id), "Session-Id": session_id}
            )
        return result.get("success", False)

    def logout(self, session_id: str) -> bool:
        data = {"session_id": session_id}
        result = self._post("user/logout", data)
        return result.get("success", False)

    def find_by_username(
        self, username: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        data = {"username": username, "limit": limit, "offset": offset}
        result = self._post("user/find_by_username", data)
        return result.get("result", [])

    def login(self, username: str, password: str) -> Tuple[str, int, str, str]:
        data = {"username": username, "password": password}
        result = self._post("user/login", data)
        result = (
            result.get("success", False),
            result.get("session_id", ""),
            result.get("user_id", 0),
            result.get("name", ""),
            result.get("email", ""),
        )
        if result[0]:
            self.session.headers.update(
                {"User-Id": str(result[2]), "Session-Id": result[1]}
            )
        return result

    def register(self, username: str, name: str, password: str, email: str) -> bool:
        data = {
            "username": username,
            "name": name,
            "password": password,
            "email": email,
        }
        result = self._post("user/register", data)
        return result.get("success", False)

    def find_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        data = {"user_id": user_id}
        result = self._post("user/find_by_user_id", data)
        return result

    def chat_list(
        self, user_id: int, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        data = {"user_id": user_id, "limit": limit, "offset": offset}
        result = self._post("user/chat_list", data)
        return result

    def update(
        self, user_id: int, username: str, name: str, password: str, email: str
    ) -> bool:
        data = {
            "user_id": user_id,
            "username": username,
            "name": name,
            "password": password,
            "email": email,
        }
        result = self.session.put("user/update", json=data)
        return result.json()["success"]

    def delete(self, user_id: int) -> None:
        data = {"user_id": user_id}
        self.session.delete("user/delete", json=data)


class PublicManager:
    def __init__(self, session: ServerMiddleware):
        self.session = session

    def send_message(
        self, user_id: int, message: str, room_name: str, name: str
    ) -> None:
        data = {
            "user_id": user_id,
            "message": message,
            "room_name": room_name,
            "name": name,
        }
        self.session.post("public/send_message", json=data)

    def read_messages(
        self, limit: int = 100, offset: int = 0, timestamp: str = ""
    ) -> List[Dict[str, Any]]:
        data = {"limit": limit, "offset": offset, "timestamp": timestamp}
        result = self.session.post("public/read_messages", json=data)
        return result.json().get("messages", [])


class PrivateManager:
    def __init__(self, session: ServerMiddleware):
        self.session = session

    def send_message(
        self, sender_id: int, receiver_id: int, message: str, name: str
    ) -> None:
        data = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "message": message,
            "name": name,
        }
        self.session.post("private/send_message", json=data)

    def read_messages(
        self,
        sender_id: int,
        receiver_id: int,
        limit: int = 100,
        offset: int = 0,
        timestamp: str = "",
    ) -> List[Dict[str, Any]]:
        data = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "limit": limit,
            "offset": offset,
            "timestamp": timestamp,
        }
        result = self.session.post("private/read_messages", json=data)
        return result.json().get("messages", [])


class MessengerAPI:
    def __init__(self, ip=None, port=None):
        if ip is None:
            ip = "localhost"

        if port is None:
            port = 10443

        self.endpoint = f"{ip}:{port}"
        url = "https://" + self.endpoint + "/api/"
        verify_ssl = False
        self.ws_params = {}
        if verify_ssl == False:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            self.ws_params["cert_reqs"] = ssl.CERT_NONE
        self.session = ServerMiddleware(url, verify=verify_ssl)
        self.session.headers.update({"Content-Type": "application/json"})

        self.user = UserManager(self.session)
        self.public = PublicManager(self.session)
        self.private = PrivateManager(self.session)

    def websocket(self, on_open, on_message, on_close):
        return websocket.WebSocketApp(
            "wss://" + self.endpoint + "/notifications/",
            on_open=on_open,
            on_message=on_message,
            on_close=on_close,
        )
