import os, uuid, json
import azure.functions as func


def get_db_connection():
    import pyodbc
    host = os.getenv("SQL_HOST")
    db = os.getenv("SQL_DB")
    user = os.getenv("SQL_USER")
    pwd = os.getenv("SQL_PASSWORD")
    port = os.getenv("SQL_PORT", "1433")

    try:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={host},{port};"
            f"DATABASE={db};"
            f"UID={user};"
            f"PWD={pwd};"
            f"Connection Timeout=30;"
        )
        return pyodbc.connect(conn_str, autocommit=True)
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        raise

def main(req: func.HttpRequest) -> func.HttpResponse:
    # Add CORS headers
    headers = {
        "Access-Control-Allow-Origin": "http://localhost:4200",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400"
    }

    # Handle OPTIONS requests (preflight)
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=200, headers=headers)

    try:
        # Only attempt to get_json if method is POST
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

            # Generate unique code
            code = uuid.uuid4().hex[:6]

            try:
                # Get database connection inside the function
                cnxn = get_db_connection()
                cursor = cnxn.cursor()

                # Save to database
                cursor.execute(
                    "INSERT INTO UrlMap (code, originalUrl) VALUES (?, ?);",
                    code, orig
                )

                # Build short link
                base = req.url.rstrip("/shorten")
                short = f"{base}/{code}"

                # Close database resources
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