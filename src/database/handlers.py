import logging
import sqlite3


logger = logging.getLogger(__name__)


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


def log_email_deprecated(
    run_id,
    linkedin_profile_url,
    email_text,
    email_status,
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
        insert_query,
        (
            run_id,
            linkedin_profile_url,
            email_text,
            email_status,
            error_message,
        ),
    )
    connection.commit()
    connection.close()


def log_email(
    run_id,
    linkedin_profile_url,
    email_text,
    email_status,
    error_message=None,
    row_number=None,  # <- new parameter
):
    """
    Inserts a new record into 'emails' and optionally updates
    'runs.last_processed_row' if row_number is provided.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # 1) Insert into the emails table
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
        insert_query,
        (
            run_id,
            linkedin_profile_url,
            email_text,
            email_status,
            error_message,
        ),
    )
    logger.info('Email logged')

    # 2) If we have a row_number, update the runs table
    if row_number is not None:
        update_query = """
        UPDATE runs
        SET last_processed_row = ?
        WHERE run_id = ?
        """
        cursor.execute(update_query, (row_number, run_id))
        logger.info('Last row logged')

    connection.commit()
    connection.close()


def get_last_processed_row_by_file(file_name: str) -> int:
    """
    Returns the most recent 'last_processed_row' for this
    file from the 'runs' table.
    If no run is found, returns 0.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    # We'll fetch the latest run for the given file, by ID descending
    query = """
        SELECT last_processed_row
        FROM runs
        WHERE file_name = ?
        ORDER BY run_id DESC
        LIMIT 1
    """
    cursor.execute(query, (file_name,))
    row = cursor.fetchone()
    connection.close()

    if row:
        return row[0] if row[0] else 0
    else:
        return 0
