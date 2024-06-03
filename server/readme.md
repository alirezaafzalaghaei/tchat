# TChat Server

This folder contains the server-side implementation of TChat. It is divided into several components:

- `messenger folder`: Contains the Flask application for handling database management and data storage.
- `notification folder`: Includes the Sanic application for opening a WebSocket server and sending notifications to clients.
- `nginx folder`: Contains the configuration for the Nginx reverse proxy, which manages SSL, and routes incoming URLs to the appropriate servers.
- `docker-compose.yaml`: The Docker Compose file for deploying all these services in containers. This file runs the following services:
  - **Flask Service**: Manages messaging logic.
  - **Sanic Service**: Handles real-time notifications.
  - **Nginx Service**: Acts as a reverse proxy to secure and route traffic.
  - **MySQL Service**: Stores account information and messages.
  - **Redis Service**: Utilizes the Pub/Sub messaging paradigm to send notifications to clients.
 
The Docker Compose setup opens port 10443 for secure message transmission between the backend and the client.
