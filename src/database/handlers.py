import os
import sqlite3

DB_PATH = 'run_history.db'


def log_run(file_name, status, error_message=None):
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            'Database file not found. Run `create_database()` first.',
        )

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    insert_query = """
    INSERT INTO run_history (file_name, status, error_message)
    VALUES (?, ?, ?)
    """
    cursor.execute(insert_query, (file_name, status, error_message))
    connection.commit()
    connection.close()


if __name__ == '__main__':
    # Test logging
    log_run('test.csv', 'Success', None)
    log_run('error.csv', 'Error', 'Missing required columns')
