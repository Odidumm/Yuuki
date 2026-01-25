import sqlite3
from sqlite3 import Error
from imports.log_helper import Logger, LogTypes

logger = Logger("Database")


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: sqlite3.Connection | None = None

    # -------------------------------
    # Verbindung öffnen
    # -------------------------------
    def connect(self):
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self.connection.row_factory = sqlite3.Row
            logger.log("Connected to the database successfully.", LogTypes.SUCCESS)
        except Error as e:
            logger.log(f"Error connecting to database: {e}", LogTypes.ERROR)
            raise

    # -------------------------------
    # Verbindung schließen
    # -------------------------------
    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.log("Database connection closed.", LogTypes.INFO)

    # -------------------------------
    # Tabellen erstellen
    # -------------------------------
    def create_tables(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS requests (
                    request_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id      TEXT NOT NULL,
                    request_text TEXT NOT NULL,
                    status       TEXT NOT NULL,
                    created_at   TEXT NOT NULL,
                    cost_amount  REAL DEFAULT 0,
                    assigned_to  TEXT DEFAULT NULL,
                    completed_at TEXT DEFAULT NULL
                )
                """
            )
            self.connection.commit()
            logger.log("Tables created successfully.", LogTypes.SUCCESS)
        except Error as e:
            logger.log(f"Error creating tables: {e}", LogTypes.ERROR)
            raise

    # -------------------------------
    # Zentrale Execute-Hilfe
    # -------------------------------
    def execute(self, query: str, params: tuple = (), commit: bool = False):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            if commit:
                self.connection.commit()
            return cursor
        except Error as e:
            logger.log(f"Database query error: {e}", LogTypes.ERROR)
            raise

    # -------------------------------
    # Request erstellen
    # -------------------------------
    def create_request(self, user_id: str, request_text: str) -> int:
        cursor = self.execute(
            """
            INSERT INTO requests (user_id, request_text, status, created_at)
            VALUES (?, ?, 'pending', datetime('now'))
            """,
            (user_id, request_text),
            commit=True
        )

        request_id = cursor.lastrowid
        logger.log(
            f"Request created for user {user_id} | ID: {request_id}",
            LogTypes.SUCCESS
        )
        return request_id
    # -------------------------------