import os, pyodbc
import azure.functions as func

# — ODBC setup (share cu shorten)
host     = os.getenv("SQL_HOST")
db       = os.getenv("SQL_DB")
user     = os.getenv("SQL_USER")
pwd      = os.getenv("SQL_PASSWORD")
port     = os.getenv("SQL_PORT", "1433")

conn_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={host},{port};DATABASE={db};UID={user};PWD={pwd}"
)
cnxn   = pyodbc.connect(conn_str, autocommit=True)
cursor = cnxn.cursor()

def main(req: func.HttpRequest) -> func.HttpResponse:
    code = req.route_params.get("code")
    if not code:
        return func.HttpResponse("Missing code", status_code=400)

    
    cursor.execute(
        "SELECT originalUrl FROM UrlMap WHERE code = ?;",
        code
    )
    row = cursor.fetchone()
    if row:
        
        return func.HttpResponse(
            status_code=302,
            headers={ "Location": row[0] }
        )
    else:
        return func.HttpResponse("Not found", status_code=404)
