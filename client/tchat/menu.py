# Standard library imports
import json
import os
import os.path
import time
from collections import defaultdict
from datetime import datetime

# Third-party imports
import ast
import pytz
from platformdirs import user_cache_dir
from rich.console import Console
from rich.segment import Segment
from rich.style import Style
from rich_pixels import Pixels
from textual import events, on, work
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.screen import Screen
from textual.widgets import *

# Local imports
from .interface import MessengerAPI as Messenger


def convert_to_localtz(gmt_time_string):

    gmt_time = datetime.strptime(gmt_time_string, "%Y-%m-%d %H:%M:%S")
    gmt_zone = pytz.timezone("GMT")
    localized_time = gmt_zone.localize(gmt_time)
    local_zone = datetime.utcnow().astimezone().tzinfo
    local_time = localized_time.astimezone(local_zone)
    local_time_string = local_time.strftime("%Y-%m-%d %H:%M:%S")
    return local_time_string


def logo():
    grid = """\
        xx   xx
        ox   ox
        Ox   Ox
    xx             xx
    xxxxxxxxxxxxxxxxx
    """

    mapping = {
        "x": Segment(" ", Style.parse("yellow on yellow")),
        "o": Segment(" ", Style.parse("on white")),
        "O": Segment(" ", Style.parse("on blue")),
    }

    pixels = Pixels.from_ascii(grid, mapping)
    return pixels


def write_message(name, timestamp, message):
    return "[yellow]%s[/yellow] [bold magenta]%s[/bold magenta] : %s" % (
        convert_to_localtz(timestamp),
        name,
        message,
    )


class LogMessage(Message):
    def __init__(self, message_obj, _type) -> None:
        self.message_obj = message_obj
        self._type = _type
        super().__init__()


class AlertScreen(Screen):
    """
    AlertScreen is a screen for displaying alert messages.

    Attributes:
        text (str): The alert message text.
        type (str): The type of alert (e.g., "warning").
    """

    CSS_PATH = "menu.tcss"

    def __init__(self, text: str, type: str = "warning") -> None:
        self.text = text  # self._wrap_text(text)
        self.type = type
        super().__init__()

    def _wrap_text(self, text: str, width: int = 120) -> str:
        return "\n".join(text[i : i + width] for i in range(0, len(text), width))

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Label(self.type, id="title", classes=self.type.lower()),
            Label(self.text, id="text"),
            Button("Ok", id="ok_btn"),
            id="alert",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()


class SearchResult(ListItem):
    def __init__(self, username: str, user_id: int) -> None:
        super().__init__()
        self.username = username
        self.user_id = user_id

    def compose(self) -> ComposeResult:
        yield Label("@" + self.username)


class MessengerApp(App):
    CSS_PATH = "menu.tcss"

    def __init__(self, session_file=None, ip=None, port=None):
        self.messenger = Messenger(ip, port)
        if session_file is None:
            cache_dir = user_cache_dir("TChat")
            os.makedirs(cache_dir, exist_ok=True)
            session_file = os.path.join(cache_dir, "session-default.json")

        if not session_file.endswith(".json"):
            session_file += ".json"

        self.session_file = session_file
        self.richlog_private = defaultdict(
            lambda: RichLog(highlight=False, markup=True, id="private")
        )
        self.richlog_public = RichLog(highlight=False, markup=True, id="public")

        super().__init__()

    def close(self):
        if hasattr(self, "ws") and self.ws:
            self.ws.close()

    @work(thread=True, exclusive=True)
    def notification(self):
        def on_message(ws, message):
            try:
                message = json.loads(message)
                where = message.get("where", "public")
                msg = message.get("content", "")
                self.post_message(LogMessage(msg, where))
            except json.JSONDecodeError:
                self.post_message(LogMessage("Invalid message format", "public"))

        def on_close(ws, close_status_code, close_msg):
            self.sub_title = "Server connection lost"

        def on_open(ws):
            data = {
                "user_id": self.app.user["user_id"],
                "session_id": self.app.user["session_id"],
            }
            ws.send(json.dumps(data))
            self.sub_title = ""

        self.ws = self.messenger.websocket(
            on_open=on_open, on_message=on_message, on_close=on_close
        )
        self.ws.run_forever(reconnect=5, sslopt=self.messenger.ws_params)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()

    def on_mount(self) -> None:
        if os.path.isfile(self.session_file):
            with open(self.session_file) as session_file:
                session = json.load(session_file)
            self.app.user = session
            try:
                is_session_valid = self.app.messenger.user.is_session_valid(
                    session["user_id"], session["session_id"]
                )
            except:
                self.push_screen(AlertScreen("No Internet!", type="Error"))
                return

            if is_session_valid:
                self.push_screen(ChatsScreen())
                self.notification()
            else:
                self.push_screen(ChooseScreen())
        else:
            self.push_screen(ChooseScreen())

    def on_unmount(self):
        self.close()

    def on_log_message(self, event: LogMessage) -> None:

        try:
            event_data = ast.literal_eval(event.message_obj)
        except (ValueError, SyntaxError):
            self.richlog_public.write(
                "Invalid message format, received: " + str(event.message_obj)
            )
            return

        if event._type == "public":
            _, _, message, _, timestamp, name = event_data
            self.richlog_public.write(write_message(name, timestamp, message))
        elif event._type == "private":
            _, sender_id, receiver_id, message, timestamp, name = event_data
            self.richlog_private[sender_id].write(
                write_message(name, timestamp, message)
            )
            self.richlog_private[receiver_id].write(
                write_message(name, timestamp, message)
            )
        else:
            self.richlog_public.write(event._type)


class ChooseScreen(Screen):
    """
    ChooseScreen is a screen that allows users to choose between login and register options.

    Attributes:
        CSS_PATH (str): The path to the CSS file.
    """

    CSS_PATH = "menu.tcss"

    def compose(self) -> ComposeResult:
        """
        Composes the UI elements of the screen.
        """
        yield Header(show_clock=True)
        yield Footer()
        yield RichLog(id="logo")
        yield Container(
            Label("Login or Register", id="question"),
            Button("Login", id="login_btn", classes="btn"),
            Button("Register", id="register_btn", classes="btn"),
            id="dialog",
        )

    def on_mount(self) -> None:
        """
        Writes the logo to the RichLog when the screen is mounted.
        """
        self.query_one(RichLog).write(logo())

    @on(Button.Pressed, "#login_btn")
    def login(self, event: Button.Pressed) -> None:
        """
        Handles the login button press event.
        """
        self.app.pop_screen()
        self.app.push_screen(LoginScreen())

    @on(Button.Pressed, "#register_btn")
    def register(self, event: Button.Pressed) -> None:
        """
        Handles the register button press event.
        """
        self.app.pop_screen()
        self.app.push_screen(RegisterScreen())


class RegisterScreen(Screen):
    CSS_PATH = "menu.tcss"

    def compose(self) -> ComposeResult:
        """Compose the elements of the register screen."""
        yield Header(show_clock=True)
        yield Footer()
        with Container(id="register_form"):
            yield Input(placeholder="Name", id="name")
            yield Input(placeholder="User Name", id="username")
            yield Input(placeholder="Email", id="email")
            yield Input(placeholder="Password", password=True, id="password")
            yield Button("Back", id="back")
            yield Button("Register", id="submit")

    @on(Button.Pressed, "#submit")
    def handle_register(self, event) -> None:
        """Handle the register button press event."""
        try:
            name = self.query_one("#name").value
            username = self.query_one("#username").value
            email = self.query_one("#email").value
            password = self.query_one("#password").value
        except AttributeError:
            self.app.push_screen(
                AlertScreen("Form input retrieval error!", type="Error")
            )
            return

        success = self.app.messenger.user.register(username, name, password, email)
        if success:
            self.app.push_screen(ChooseScreen())
            self.app.push_screen(
                AlertScreen("Registration successful!", type="Information")
            )
        else:
            register_error = "Registration failed! Possible issues:\n1) Incorrect email address\n2) Weak password (must be at least 10 characters with lowercase and uppercase letters, digits, and symbols)\n3) Username already taken"
            self.app.push_screen(AlertScreen(register_error, type="Error"))

    @on(Button.Pressed, "#back")
    def handle_back(self) -> None:
        """Handle the back button press event."""
        self.app.pop_screen()
        self.app.push_screen(ChooseScreen())


class LoginScreen(Screen):
    CSS_PATH = "menu.tcss"

    def compose(self) -> ComposeResult:
        """Compose the elements of the login screen."""
        yield Header(show_clock=True)
        yield Footer()
        with Container(id="login_form"):
            yield Input(placeholder="User Name", id="username")
            yield Input(placeholder="Password", password=True, id="password")
            yield Button("Back", id="back")
            yield Button("Login", id="submit")

    @on(Button.Pressed, "#submit")
    def handle_login(self, event) -> None:
        """Handle the login button press event."""
        try:
            username = self.query_one("#username").value
            password = self.query_one("#password").value
        except AttributeError:
            self.app.push_screen(
                AlertScreen("Form input retrieval error!", type="Error")
            )
            return

        success, session_id, user_id, name, email = self.app.messenger.user.login(
            username, password
        )

        if success:
            self.app.user = {
                "session_id": session_id,
                "username": username,
                "name": name,
                "user_id": user_id,
                "email": email,
            }
            json_data = json.dumps(self.app.user, indent=4)
            with open(self.app.session_file, "w") as session:
                session.write(json_data)
            self.app.push_screen(ChatsScreen())
            self.app.close()
            self.app.notification()
        else:
            self.app.push_screen(
                AlertScreen("Username or Password is incorrect.", type="Error")
            )

    @on(Button.Pressed, "#back")
    def handle_back(self) -> None:
        """Handle the back button press event."""
        self.app.pop_screen()
        self.app.push_screen(ChooseScreen())


class PrivateScreen(Screen):
    CSS_PATH = "menu.tcss"

    def __init__(self, user_id: int, username: str):
        """Initialize the PrivateScreen with the given user_id and username."""
        self.user_id = user_id
        self.username = username
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose the elements of the private screen."""
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Button("Back", id="back"),
            Label("@" + self.username, id="pvtitle"),
            self.app.richlog_private[self.user_id],
            Container(
                Input(placeholder="Message", id="message"),
                Button("Send", id="send"),
                id="input-send",
            ),
            id="private-container",
        )

    def on_mount(self) -> None:
        """Handle actions to perform when the screen is mounted."""
        log = self.query_one("#private")
        try:
            messages = self.app.messenger.private.read_messages(
                self.app.user["user_id"], self.user_id
            )
        except Exception as ex:
            self.app.push_screen(AlertScreen("Failed to load messages.", type="Error"))
            return

        for message in messages:
            (
                sender_id,
                sender_name,
                receiver_id,
                receiver_name,
                message_content,
                timestamp,
            ) = map(str, message)
            sender_name = (
                "Me" if int(sender_id) == self.app.user["user_id"] else sender_name
            )
            log.write(write_message(sender_name, timestamp, message_content))

    @on(Button.Pressed, "#back")
    def handle_back(self) -> None:
        """Handle the back button press event."""
        self.app.pop_screen()

    @on(Button.Pressed, "#send")
    def handle_send(self) -> None:
        """Handle the send button press event."""
        message = self.query_one("#message").value
        if not message:
            return
        user_id = self.app.user["user_id"]
        self.app.messenger.private.send_message(
            user_id, self.user_id, message, self.app.user["name"]
        )
        self.query_one("#message").clear()

    def on_input_submitted(self) -> None:
        """Handle the input submitted event."""
        self.handle_send()


class ChatsScreen(Screen):
    CSS_PATH = "menu.tcss"

    def compose(self) -> ComposeResult:
        """Compose the elements of the chats screen."""
        yield Header(show_clock=True)
        yield Footer()
        with TabbedContent("Public", "Private", "Me"):
            yield Container(
                self.app.richlog_public,
                Container(
                    Input(placeholder="Message", id="message"),
                    Button("Send", id="send"),
                    id="input-send",
                ),
                id="public-container",
            )
            yield Container(
                Container(
                    Input(placeholder="Username", id="username"),
                    Button("Search", id="search"),
                    id="input-send",
                ),
                Label("", id="result_message"),
                ListView(id="search_result"),
                id="private-tab",
            )
            yield Container(
                Input(placeholder=f"Name ({self.app.user['name']})", id="mename"),
                Input(
                    placeholder=f"Username ({self.app.user['username']})",
                    id="meusername",
                ),
                Input(placeholder=f"Email ({self.app.user['email']})", id="meemail"),
                Input(placeholder="Password", password=True, id="mepassword"),
                Button("Log out", id="logout"),
                Button("Update", id="submit"),
                id="register_form",
            )

    def on_mount(self) -> None:
        """Handle actions to perform when the screen is mounted."""
        self.load_public_messages()
        self.load_chat_list()

    def load_public_messages(self) -> None:
        """Load and display public messages."""
        log = self.query_one("#public")
        try:
            messages = self.app.messenger.public.read_messages()
        except Exception as ex:
            self.app.push_screen(
                AlertScreen("Failed to load messages. Error:" + str(ex), type="Error")
            )
            return

        for message in messages:
            user_id, message_content, timestamp, name = map(str, message)
            name = "Me" if int(user_id) == self.app.user["user_id"] else name
            log.write(write_message(name, timestamp, message_content))

    def load_chat_list(self) -> None:
        """Load and display the chat list."""
        listview = self.query_one("#search_result")
        try:
            chats = self.app.messenger.user.chat_list(self.app.user["user_id"])
        except Exception as ex:
            self.app.push_screen(AlertScreen("Failed to load chats.", type="Error"))
            return

        self.query_one("#result_message").update("Latest chats:")
        for user_id, username in chats:
            listview.append(SearchResult(username, user_id))

    @on(ListView.Selected, "#search_result")
    def handle_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle the selection of a list view item."""
        self.app.push_screen(PrivateScreen(event.item.user_id, event.item.username))

    @on(Button.Pressed, "#submit")
    def handle_update(self) -> None:
        """Handle the update button press event."""
        username = self.query_one("#meusername").value
        email = self.query_one("#meemail").value
        password = self.query_one("#mepassword").value
        name = self.query_one("#mename").value
        user_id = self.app.user["user_id"]
        if not all([username, email, password, name]):
            return
        success = self.app.messenger.user.update(
            user_id, username, name, password, email
        )
        if success:
            self.app.user.update(
                username=username,
                name=name,
                email=email,
            )
            json_data = json.dumps(self.app.user, indent=4)
            with open(self.app.session_file, "w") as session:
                session.write(json_data)
            self.app.push_screen(AlertScreen("Update successful!", type="Information"))
        else:
            self.app.push_screen(AlertScreen("Update unsuccessful!", type="Error"))

    @on(Button.Pressed, "#logout")
    def handle_logout(self) -> None:
        """Handle the logout button press event."""
        if os.path.isfile(self.app.session_file):
            os.remove(self.app.session_file)
        self.app.close()
        self.app.pop_screen()
        self.app.push_screen(ChooseScreen())

    @on(Button.Pressed, "#search")
    def handle_search(self) -> None:
        """Handle the search button press event."""
        username = self.query_one("#username").value.replace("@", "")
        if not username:
            return  # TODO: return all history chats

        try:
            users = self.app.messenger.user.find_by_username(username)
        except Exception as ex:
            self.app.push_screen(AlertScreen("Search failed.", type="Error"))
            return

        listview = self.query_one("#search_result")
        listview.clear()
        self.query_one("#result_message").update(f"Found {len(users)} users")
        for user_id, username in users:
            listview.append(SearchResult(username, user_id))

    @on(Button.Pressed, "#send")
    def handle_send(self) -> None:
        """Handle the send button press event."""
        message = self.query_one("#message").value
        if not message:
            return

        user_id = self.app.user["user_id"]

        try:
            self.app.messenger.public.send_message(
                user_id, message, "public_room", self.app.user["name"]
            )
        except Exception as ex:
            self.app.push_screen(AlertScreen("Failed to send message.", type="Error"))
            return

        self.query_one("#message").clear()

    def on_input_submitted(self) -> None:
        """Handle the input submitted event."""
        self.handle_send()


if __name__ == "__main__":
    app = MessengerApp()
    app.run()
