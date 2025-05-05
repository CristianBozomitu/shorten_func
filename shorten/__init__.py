import json
import os
import azure.functions as func
import pymssql
import logging
import random
import string

def generate_short_code(length=6):
    """Generate a random alphanumeric code of specified length"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def get_db_connection():
    host = os.getenv("SQL_HOST")
    db = os.getenv("SQL_DB")
    user = os.getenv("SQL_USER")
    pwd = os.getenv("SQL_PASSWORD")
    port = int(os.getenv("SQL_PORT", "1433"))

    logging.info(f"Attempting database connection to {host}:{port}/{db}")

    logging.info(f"Environment variables set: HOST={bool(host)}, DB={bool(db)}, USER={bool(user)}, PWD={bool(pwd)}, PORT={bool(port)}")

    try:
        conn = pymssql.connect(
            server=host,
            user=user,
            port=port,
            password=pwd,
            database=db
        )
        logging.info("Database connection successful")
        return conn
    except Exception as e:
        logging.error(f"Database connection error: {str(e)}")
        raise

def main(req: func.HttpRequest) -> func.HttpResponse:
    headers = {
        "Access-Control-Allow-Origin": "http://localhost:4200",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    }

    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=200, headers=headers)

    try:
        req_body = req.get_json()
        original_url = req_body.get('url')

        if not original_url:
            logging.warning("Request missing URL in body")
            return func.HttpResponse(
                "Missing URL in request body",
                status_code=400,
                headers=headers
            )

        logging.info(f"Processing URL shortening for: {original_url}")

        try:
            short_code = generate_short_code()

            cnxn = get_db_connection()
            cursor = cnxn.cursor()

            code_exists = True
            max_attempts = 5
            attempts = 0

            while code_exists and attempts < max_attempts:
                cursor.execute("SELECT COUNT(*) FROM UrlMap WHERE code = %s", (short_code,))
                count = cursor.fetchone()[0]
                code_exists = count > 0

                if code_exists:
                    short_code = generate_short_code()
                    attempts += 1

            if attempts >= max_attempts:
                raise Exception("Failed to generate a unique code after multiple attempts")

            cursor.execute(
                "INSERT INTO UrlMap (code, originalUrl, createdAt) VALUES (%s, %s, GETDATE())",
                (short_code, original_url)
            )

            cnxn.commit()

            cursor.close()
            cnxn.close()

            base_url = os.getenv("BASE_URL", "https://cloud-compute-func.azurewebsites.net/api/")
            short_url = f"{base_url}{short_code}"

            return func.HttpResponse(
                body=json.dumps({"shortUrl": short_url, "code": short_code}),
                mimetype="application/json",
                status_code=201,
                headers=headers
            )

        except Exception as db_error:
            logging.error(f"Database operation error: {str(db_error)}")
            return func.HttpResponse(
                f"Database error: {str(db_error)}",
                status_code=500,
                headers=headers
            )

    except Exception as e:
        logging.error(f"General error: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500, headers=headers)