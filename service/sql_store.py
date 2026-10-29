import os
import re
from contextlib import contextmanager
from dataclasses import dataclass
from uuid import UUID

import pyodbc
from .cloud_errors import SqlStoreError
from .cancellation import check_cancelled

pyodbc.pooling = False


@dataclass(frozen=True)
class SqlConfiguration:
    server: str
    database: str
    client_id: str

    @classmethod
    def from_environment(cls):
        server = os.environ.get("BENEFITS_SQL_SERVER", "")
        database = os.environ.get("BENEFITS_SQL_DATABASE", "")
        client_id = os.environ.get("BENEFITS_MANAGED_IDENTITY_CLIENT_ID", "")
        try:
            if not re.fullmatch(r"[a-z0-9-]+\.database\.windows\.net", server):
                raise ValueError("An Azure SQL server DNS name is required.")
            if not re.fullmatch(r"[a-zA-Z0-9_-]{1,63}", database):
                raise ValueError("An explicit database name is required.")
            if str(UUID(client_id)) != client_id.lower():
                raise ValueError("An explicit managed identity client ID is required.")
        except ValueError as error:
            raise RuntimeError("SQL_CONFIGURATION_INVALID: server, database and managed identity client ID are required.") from error
        return cls(server, database, client_id)

    def connection_string(self):
        return (f"Driver={{ODBC Driver 18 for SQL Server}};Server=tcp:{self.server},1433;"
                f"Database={self.database};Authentication=ActiveDirectoryMsi;UID={self.client_id};"
                "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60;")


class SqlRow(dict):
    def __getitem__(self, key):
        if isinstance(key, int):
            return tuple(self.values())[key]
        return super().__getitem__(key)


class SqlResult:
    def __init__(self, cursor):
        self.cursor = cursor
        self.names = [column[0] for column in cursor.description] if cursor.description else []
        if not self.names:
            self.cursor.close()
            self.cursor = None

    def fetchone(self):
        if self.cursor is None:
            return None
        try:
            row = self.cursor.fetchone()
            return SqlRow(zip(self.names, row)) if row is not None else None
        finally:
            self.cursor.close()
            self.cursor = None

    def fetchall(self):
        if self.cursor is None:
            return []
        try:
            return [SqlRow(zip(self.names, row)) for row in self.cursor.fetchall()]
        finally:
            self.cursor.close()
            self.cursor = None


class SqlConnection:
    def __init__(self, raw):
        self.raw = raw

    def execute(self, statement, params=()):
        check_cancelled()
        cursor = self.raw.cursor()
        if statement == "BEGIN IMMEDIATE":
            # Match the local store's single-writer transaction boundary.
            cursor.execute(
                "IF @@TRANCOUNT=0 BEGIN TRANSACTION; "
                "DECLARE @result int; EXEC @result=sys.sp_getapplock "
                "@Resource=N'benefits-iq-workflow-write',@LockMode='Exclusive',"
                "@LockOwner='Transaction',@LockTimeout=10000; SELECT @result AS lock_result;"
            )
            while cursor.description is None:
                if not cursor.nextset():
                    cursor.close()
                    raise SqlStoreError("CASE_WRITE_LOCK_FAILED")
            result = cursor.fetchone()[0]
            cursor.close()
            if result < 0:
                raise SqlStoreError("CASE_WRITE_BUSY_RETRY")
            return None
        insert = re.fullmatch(r"INSERT OR IGNORE INTO (cases|case_operations|tasks) (.+)", statement)
        if insert:
            table, body = insert.groups()
            key = "case_id" if table == "case_operations" else "id"
            statement = (f"IF NOT EXISTS(SELECT 1 FROM dbo.{table} WITH(UPDLOCK,HOLDLOCK) WHERE {key}=?) "
                         f"INSERT INTO dbo.{table} {body}")
            params = (params[0], *params)
        try:
            cursor.execute(statement, tuple(params))
            return SqlResult(cursor)
        except Exception:
            cursor.close()
            raise


@contextmanager
def connection():
    check_cancelled()
    config = SqlConfiguration.from_environment()
    if "ODBC Driver 18 for SQL Server" not in pyodbc.drivers():
        raise SqlStoreError("ODBC_DRIVER_18_REQUIRED")
    try:
        raw = pyodbc.connect(config.connection_string(), autocommit=False, timeout=60)
    except pyodbc.Error as error:
        raise SqlStoreError("SQL_CONNECTION_UNAVAILABLE") from error
    try:
        raw.timeout = 90
        yield SqlConnection(raw)
        check_cancelled()
        raw.commit()
    except Exception as error:
        try:
            raw.rollback()
        except pyodbc.Error:
            raise SqlStoreError("SQL_ROLLBACK_FAILED") from error
        if isinstance(error, pyodbc.Error):
            raise SqlStoreError("SQL_OPERATION_FAILED") from error
        raise
    finally:
        raw.close()


def verify_schema():
    with connection() as db:
        row = db.execute("SELECT version FROM dbo.schema_migrations WHERE version=1").fetchone()
        if row is None:
            raise SqlStoreError("SQL_SETUP_REQUIRED")
