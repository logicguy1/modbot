import sqlite3

class SQLiteManager:
    def __init__(self, db_file, logging):
        self.db_file = db_file
        self.connection = None
        self.cursor = None
        self.logging = logging

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_file)
            self.cursor = self.connection.cursor()
            self.logging.info(f"Connected to SQLite database: {self.db_file}")
        except sqlite3.Error as e:
            self.logging.error(f"Error connecting to SQLite database: {e}")

    def execute_query(self, query, parameters=None):
        try:
            if parameters:
                self.cursor.execute(query, parameters)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            self.logging.info("Query executed successfully")
        except sqlite3.Error as e:
            self.logging.error(f"Error executing query: {e}")

    def fetch_all(self, query, parameters=None):
        try:
            if parameters:
                self.cursor.execute(query, parameters)
            else:
                self.cursor.execute(query)
            rows = self.cursor.fetchall()
            return rows
        except sqlite3.Error as e:
            self.logging.error(f"Error fetching data: {e}")
            return None

    def close_connection(self):
        if self.connection:
            self.connection.close()
            self.logging.info("Connection closed.")

# Example usage:
# db_manager = SQLiteManager("example.db")
# db_manager.connect()
# db_manager.execute_query("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
# db_manager.execute_query("INSERT INTO users (name, age) VALUES (?, ?)", ("John Doe", 30))
# result = db_manager.fetch_all("SELECT * FROM users")
# self.logging.info(result)
# db_manager.close_connection()


