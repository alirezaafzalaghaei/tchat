# Use the official Nginx image from the Docker Hub
FROM nginx:latest


# Install OpenSSL
# RUN apt-get update && apt-get install -y openssl

# Create a directory for the SSL certificates
RUN mkdir -p /etc/nginx/ssl

# Generate a self-signed certificate
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/nginx.key \
    -out /etc/nginx/ssl/nginx.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=Department/CN=localhost"

# Copy the custom Nginx configuration file
COPY nginx.conf /etc/nginx/nginx.conf
