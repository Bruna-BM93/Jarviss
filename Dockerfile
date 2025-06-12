idfwsp-codex/criar-app-do-zero
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "-b", "0.0.0.0:5000", "main:app"]
=======
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY main.py .
COPY templates ./templates/

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variables (FLASK_RUN_HOST is for dev, Gunicorn uses --bind)
ENV FLASK_APP=main.py
# ENV FLASK_RUN_HOST=0.0.0.0 # Not strictly needed for Gunicorn

# Command to run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
main
