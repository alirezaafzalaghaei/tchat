# Notification Server

This folder contains the implementation of the notification server for TChat. It includes:

- `Dockerfile`: Installs the requirements for the Sanic app and runs the app using Sanic's default ASGI server.
- `app.py`: The Sanic server with notification sending logic.
- `requirements.txt`: Lists the required libraries for running the Sanic server.

## Details of `app.py`

The app serves a single route, `/notifications`, which implements WebSocket logic. Initially, the WebSocket waits for an authorization packet and validates the session using the messenger app, which is implemented with Flask. Once authorized, the app connects to the Redis client and subscribes to two channels: public and user-specific notifications. Whenever a message arrives, it is sent to the client.
