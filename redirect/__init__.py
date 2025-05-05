import os
import azure.functions as func

def get_db_connection():
    import pyodbc
    host = os.getenv("SQL_HOST")
    db = os.getenv("SQL_DB")
    user = os.getenv("SQL_USER")
    pwd = os.getenv("SQL_PASSWORD")
    port = os.getenv("SQL_PORT", "1433")

    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={host},{port};DATABASE={db};UID={user};PWD={pwd}"
    )
    return pyodbc.connect(conn_str, autocommit=True)

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        code = req.route_params.get("code")
        if not code:
            return func.HttpResponse("Missing code", status_code=400)

        # Get database connection inside the function
        cnxn = get_db_connection()
        cursor = cnxn.cursor()

        cursor.execute(
            "SELECT originalUrl FROM UrlMap WHERE code = ?;",
            code
        )
        row = cursor.fetchone()

        # Close the resources
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