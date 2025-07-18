# Jarviss Backend

This is the backend for the Jarviss application, a personal finance assistant.

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/jarviss-backend.git
    ```
2.  Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
3.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Create a PostgreSQL database and user:
    ```sql
    CREATE DATABASE jarviss;
    CREATE USER jarviss_user WITH PASSWORD 'password';
    GRANT ALL PRIVILEGES ON DATABASE jarviss TO jarviss_user;
    ```
5.  Set the environment variables. Create a `.env` file and add the following:
    ```
    export APP_SETTINGS="config.DevelopmentConfig"
    export DATABASE_URL="postgresql://jarviss_user:password@localhost/jarviss"
    export SECRET_KEY="a-very-secret-key"
    ```
6.  Run the database migrations:
    ```bash
    flask db init
    flask db migrate
    flask db upgrade
    ```
7.  Run the application:
    ```bash
    python main.py
    ```

## Deployment

This project is configured for deployment on Render. You can deploy it by creating a new "Web Service" on Render and pointing it to your GitHub repository. Render will automatically detect the `render.yaml` file and configure the service for you.

You will need to set the following environment variables in the Render dashboard:

-   `OPENAI_API_KEY`
-   `GOOGLE_APPLICATION_CREDENTIALS`
-   `TWILIO_ACCOUNT_SID`
-   `TWILIO_AUTH_TOKEN`
-   `TWILIO_WHATSAPP_NUMBER`

## API Documentation

The API is documented using Postman. You can find the collection in the `docs/` directory.

## Contributing

Please read `CONTRIBUTING.md` for details on our code of conduct, and the process for submitting pull requests to us.
