# Nginx Configurations

This folder contains the configurations for the Nginx web server Docker, used to serve the messenger backend and notification manager, as well as manage SSL configurations. The folder includes:

- `nginx.conf`: The Nginx configuration file, which sets SSL certificate files and routing rules.
- `Dockerfile`: The Docker service file, which generates a self-signed SSL certificate and applies the configuration settings.
