# src/database/db_setup.py
import os
import sqlite3

# Define the path to your database file
DB_PATH = 'run_history.db'


def create_database():
    # Check if the database file already exists
    if not os.path.exists(DB_PATH):
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        # SQL query to create the run_history table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS run_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_name TEXT,
            status TEXT,
            error_message TEXT
        )
        """
        cursor.execute(create_table_query)
        connection.commit()
        connection.close()
        print("SQLite database and 'run_history' table created successfully!")
    else:
        print('Database already exists. No action needed.')
