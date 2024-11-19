import sqlite3

DB_PATH = 'run_history.db'


def create_database():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Create runs table
    create_runs_table_query = """
    CREATE TABLE IF NOT EXISTS runs (
        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        file_name TEXT,
        status TEXT,
        error_message TEXT
    )
    """
    cursor.execute(create_runs_table_query)

    # Create emails table
    create_emails_table_query = """
    CREATE TABLE IF NOT EXISTS emails (
        email_id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER,
        linkedin_profile_url TEXT,
        email_text TEXT,
        email_status TEXT,
        error_message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
    )
    """
    cursor.execute(create_emails_table_query)

    connection.commit()
    connection.close()
    print('SQLite database setup complete')
