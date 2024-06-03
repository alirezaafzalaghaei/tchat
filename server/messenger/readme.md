# Messenger Server

This folder contains the messenger logic. It includes:

- `app.py`: The Flask app that receives HTTP requests from users and handles them.
- `requirements.txt`: Lists the required libraries for running the Flask server.
- `wait-for-it.sh`: A script designed to wait until a specified port opens, used to ensure the MySQL database is fully up.
- `Dockerfile`: Installs the required files for running the Flask app and then runs the app using the `gunicorn` WSGI server.
- `messengerdb folder`: Contains the SQL tables for the Flask backend.

## Details of `app.py`

The app connects to MySQL for storing messages and user information and to Redis for publishing notifications. For security reasons, all routes work with the POST HTTP method, except for the delete and update functions, which use the DELETE and PUT HTTP methods, respectively. The HTTP requests should include two headers for authentication, which are used by the `session_required` decorator to verify user access to the function. The send message functions (for private and public chats) save messages to the database and then publish the saved messages through the Redis Pub/Sub paradigm to be used by the Sanic app. Additionally, two libraries are used in this app to validate email addresses and assess the strength of passwords.
