 # TChat Client

The `tchat` directory contains the main client files, including:

- `menu.py`: The terminal user interface (TUI) application for the TChat client.
- `interface.py`: The interface between the server and the client. It communicates with the server, sends TUI data to the server, and returns the results to the TUI.
- `menu.tcss`: The textual cascading stylesheet of the program.
- `main.py`: The handler of the system-wide command-line application for TChat.
- `__init__.py`: Python initialization file.

## Details of `menu.py`:

- `MessengerApp class`: The main program. It instantiates the MessengerAPI from `interface`, receives notifications in a worker on another thread.
- `RegisterScreen and LoginScreen`: Two screens for account registration and login.
- `ChatsScreen`: The main view of the program that contains public chats, search, and profile update tabs.
- `PrivateScreen`: Handles private chats.
- `LogMessage`: A thread-safe class for sending notifications into the main application thread.
- `AlertScreen`: A simple screen for showing information and errors.

## Details of `interface.py`:

- `MessengerAPI`: A class that opens the connection to the server and is ready to send and receive data. It contains the public, private and user manager objests.
- `PublicManager, PrivateManager, UserManager`: Three classes for sending data to appropriate server URLs.
