import os
import azure.functions as func
import pymssql

def get_db_connection():
    host = os.getenv("SQL_HOST")
    db = os.getenv("SQL_DB")
    user = os.getenv("SQL_USER")
    pwd = os.getenv("SQL_PASSWORD")
    port = int(os.getenv("SQL_PORT", "1433"))

    try:
        conn = pymssql.connect(
            server=host,
            user=user,
            port= port,
            password=pwd,
            database=db
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
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
        code = req.route_params.get("code")
        if not code:
            return func.HttpResponse("Missing code", status_code=400)

        cnxn = get_db_connection()
        cursor = cnxn.cursor()

        cursor.execute(
            "SELECT originalUrl FROM UrlMap WHERE code = %s",
            (code,)
        )
        row = cursor.fetchone()

        cursor.close()
        cnxn.close()

        if row:
            return func.HttpResponse(
                status_code=302,
                headers={"Location": row[0]}
            )
        else:
            return func.HttpResponse("Not found", status_code=404)

    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)