# TChat Client

The `client` directory holds the implementation of the TChat client application. This directory contains two major files and directories:

- **TChat:** This is the main terminal user interface (TUI) application for the TChat client.
- **setup.py:** This file is used to install the TChat client as a Python module and also as a system-wide application. It installs the following required libraries:
    - `requests`: Used for sending HTTP requests such as POST for sending and retrieving messages, PUT for updating account data, and DELETE for deleting accounts.
    - `websocket-client`: Enables connection to the server's WebSocket for retrieving notifications.
	- `textual`: Implements the terminal user interface (TUI) for the application.
	- `rich-pixels`: Used for drawing TChat logo within the TUI.
	- `platformdirs`: Allows access to the operating system's cache directory.
	- `pytz`: Provides timezone functionality.


To install the TChat client, run the following command in your terminal:

```bash
$ pip install .
```
This will install the TChat client along with its dependencies, allowing you to use it as a system-wide application.