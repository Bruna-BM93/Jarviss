# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies needed for psycopg2-binary and potentially other packages
# libpq-dev provides the PostgreSQL client development libraries
# gcc and other build tools might be needed if psycopg2 had to compile from source,
# though psycopg2-binary usually avoids this. It's good to have them for robustness.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY main.py .
COPY templates ./templates/

# Define environment variables
# Flask specific
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
# Note: FLASK_RUN_HOST is for the Flask development server, Gunicorn uses --bind.
# Setting it doesn't harm, but isn't used by the CMD.
ENV FLASK_RUN_HOST=0.0.0.0
# PostgreSQL connection (defaults, can be overridden at runtime)
ENV DB_HOST=db
ENV DB_NAME=jarvisdb
ENV DB_USER=jarvisuser
ENV DB_PASSWORD=jarvispass
ENV DB_PORT=5432

# Make port 5000 available to the world outside this container (Gunicorn will bind to this)
EXPOSE 5000

# Command to run the application using Gunicorn
# Consider adding --workers based on CPU cores available, e.g., (2 * CPU_CORES) + 1
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
