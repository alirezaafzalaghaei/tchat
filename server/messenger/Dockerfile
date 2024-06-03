# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port 13247 available to the world outside this container
EXPOSE 13247

COPY wait-for-it.sh /wait-for-it.sh

RUN chmod +x /wait-for-it.sh

ENTRYPOINT ["./wait-for-it.sh", "mysql:3306", "--", "gunicorn", "-w", "4", "-b", "0.0.0.0:13247", "app:app"]
# ENTRYPOINT ["./wait-for-it.sh", "mysql:3306", "--", "flask", "--app", "app", "--debug", "run", "--host", "0.0.0.0","--port=13247"]
