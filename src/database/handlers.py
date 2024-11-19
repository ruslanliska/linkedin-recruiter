import sqlite3

DB_PATH = 'run_history.db'


# src/modules/history_handler.py


DB_PATH = 'run_history.db'


def log_run_start(file_name):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    insert_query = """
    INSERT INTO runs (file_name, status)
    VALUES (?, ?)
    """
    cursor.execute(insert_query, (file_name, 'Running'))
    run_id = cursor.lastrowid  # Get the ID of the inserted run
    connection.commit()
    connection.close()
    return run_id  # Return the run_id to associate emails with this run


def log_run_end(run_id, status, error_message=None):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    update_query = """
    UPDATE runs
    SET status = ?, error_message = ?
    WHERE run_id = ?
    """
    cursor.execute(update_query, (status, error_message, run_id))
    connection.commit()
    connection.close()


def log_email(
    run_id, linkedin_profile_url,
    email_text, email_status,
    error_message=None,
):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    insert_query = """
    INSERT INTO emails (
        run_id,
        linkedin_profile_url,
        email_text,
        email_status,
        error_message
    ) VALUES (?, ?, ?, ?, ?)
    """
    cursor.execute(
        insert_query, (
            run_id,
            linkedin_profile_url,
            email_text,
            email_status,
            error_message,
        ),
    )
    connection.commit()
    connection.close()
