import os, uuid, json
import azure.functions as func


def get_db_connection():
    import pymssql
    host = os.getenv("SQL_HOST")
    db = os.getenv("SQL_DB")
    user = os.getenv("SQL_USER")
    pwd = os.getenv("SQL_PASSWORD")
    port = int(os.getenv("SQL_PORT", "1433"))

    try:
        # pymssql uses different connection parameters
        conn = pymssql.connect(
            server=host,
            port=port,
            user=user,
            password=pwd,
            database=db,
            autocommit=True
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        raise

def main(req: func.HttpRequest) -> func.HttpResponse:
    headers = {
        "Access-Control-Allow-Origin": "http://localhost:4200",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400"
    }

    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=200, headers=headers)

    try:
        if req.method == "POST":
            req_body = req.get_json()
            orig = req_body.get("url")

            if not orig:
                return func.HttpResponse(
                    json.dumps({"error": "Missing url parameter"}),
                    status_code=400,
                    mimetype="application/json",
                    headers=headers
                )

            code = uuid.uuid4().hex[:6]

            try:
                cnxn = get_db_connection()
                cursor = cnxn.cursor()

                # pymssql uses %s placeholders instead of ?
                cursor.execute(
                    "INSERT INTO UrlMap (code, originalUrl) VALUES (%s, %s);",
                    (code, orig)  # Parameters must be in a tuple
                )

                base = req.url.rstrip("/shorten")
                short = f"{base}/{code}"

                cursor.close()
                cnxn.close()

                return func.HttpResponse(
                    json.dumps({"shortUrl": short}),
                    mimetype="application/json",
                    headers=headers
                )
            except Exception as db_error:
                return func.HttpResponse(
                    json.dumps({"error": f"Database error: {str(db_error)}"}),
                    status_code=500,
                    mimetype="application/json",
                    headers=headers
                )
        else:
            return func.HttpResponse(
                json.dumps({"error": "Method not allowed"}),
                status_code=405,
                mimetype="application/json",
                headers=headers
            )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": f"Server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=headers
        )