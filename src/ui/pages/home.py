import sqlite3
import threading
import time
from datetime import datetime
from datetime import timedelta
from tkinter import filedialog
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

import pandas as pd
import ttkbootstrap as ttk

from src.database.handlers import log_run_end
from src.database.handlers import log_run_start
from src.inmail.personalized_email import run_selenium_automation

DB_PATH = 'run_history.db'


class HomePage(ttk.Frame):
    def __init__(self, parent, upload_callback=None):
        super().__init__(parent)
        self.upload_callback = upload_callback
        self.csv_data = None  # To store the loaded CSV data
        self.run_id = None    # To store the current run_id

        # Thread reference for Selenium automation
        self.automation_thread = None

        # Initialize variables for daily limit and emails sent today
        self.daily_limit_var = ttk.IntVar()
        self.emails_sent_today_var = ttk.IntVar()

        # Load daily limit and update emails sent today
        self.load_daily_limit()
        self.update_emails_sent_today()

        self.create_widgets()

    def create_widgets(self):
        # Main frame for the form
        form_frame = ttk.Frame(self)
        form_frame.pack(pady=20, padx=20, fill='both', expand=True)

        # Use a LabelFrame to group form fields with a title
        form = ttk.Labelframe(
            form_frame, text='Automation Settings', padding=(20, 10),
        )
        form.pack(fill='both', expand=True)

        # Configure grid columns for alignment (simple approach)
        for col_index in range(6):
            form.columnconfigure(col_index, weight=0)

        # -----------------------------
        # Row 0: CSV File Selection
        # -----------------------------
        label_file = ttk.Label(form, text='CSV File:', font=('Helvetica', 12))
        label_file.grid(row=0, column=0, sticky='e', padx=5, pady=10)

        # Entry to display selected file path
        self.file_path_var = ttk.StringVar(value='')
        entry_file = ttk.Entry(
            form, textvariable=self.file_path_var,
            state='readonly', width=40,
        )
        entry_file.grid(row=0, column=1, sticky='ew', padx=5, pady=10)

        # Button to upload CSV
        self.button_upload = ttk.Button(
            form, text='Browse',
            command=self.upload_csv,
            bootstyle='success-outline',
        )
        self.button_upload.grid(row=0, column=2, sticky='w', padx=5, pady=10)

        # -----------------------------
        # Daily Limit / Emails Sent
        # -----------------------------
        label_daily_limit = ttk.Label(
            form, text='Daily Limit:', font=('Helvetica', 12),
        )
        label_daily_limit.grid(row=1, column=0, sticky='e', padx=5, pady=10)

        entry_daily_limit = ttk.Entry(
            form, textvariable=self.daily_limit_var, width=10,
        )
        entry_daily_limit.grid(row=1, column=1, sticky='w', padx=5, pady=10)

        # Bind the daily limit variable to save when changed
        self.daily_limit_var.trace_add('write', self.on_daily_limit_changed)

        label_emails_sent_today = ttk.Label(
            form, text='Emails sent today:', font=('Helvetica', 12),
        )
        label_emails_sent_today.grid(
            row=1, column=2, sticky='e', padx=5, pady=10,
        )

        label_emails_sent_today_value = ttk.Label(
            form,
            textvariable=self.emails_sent_today_var,
            font=('Helvetica', 12),
        )
        label_emails_sent_today_value.grid(
            row=1, column=3, sticky='w', padx=5, pady=10,
        )

        # -----------------------------
        # Visible Mode Toggle
        # -----------------------------
        label_visible_mode = ttk.Label(
            form, text='Visible Mode:', font=('Helvetica', 12),
        )
        label_visible_mode.grid(row=2, column=0, sticky='e', padx=5, pady=10)

        self.visible_mode_var = ttk.BooleanVar(value=True)  # Default: True
        switch_visible_mode = ttk.Checkbutton(
            form,
            text='',
            variable=self.visible_mode_var,
            bootstyle='success-round-toggle',
        )
        switch_visible_mode.grid(
            row=2, column=1, sticky='w', padx=5, pady=10, columnspan=2,
        )

        # -----------------------------
        # Prompt (ScrolledText)
        # -----------------------------
        label_prompt = ttk.Label(
            form, text='Prompt:', font=('Helvetica', 12),
        )
        label_prompt.grid(row=3, column=0, sticky='ne', padx=5, pady=10)

        self.prompt_text = ScrolledText(
            form, wrap='word', width=50, height=4, font=('Helvetica', 12),
        )
        self.prompt_text.grid(
            row=3, column=1, sticky='nsew', padx=5, pady=10, columnspan=4,
        )

        # -----------------------------
        # Reference Email (ScrolledText)
        # -----------------------------
        label_reference_email = ttk.Label(
            form, text='Reference Email:', font=('Helvetica', 12),
        )
        label_reference_email.grid(
            row=4, column=0, sticky='ne', padx=5, pady=10,
        )

        self.reference_email_text = ScrolledText(
            form, wrap='word', width=50, height=10, font=('Helvetica', 12),
        )
        self.reference_email_text.grid(
            row=4, column=1, sticky='nsew', padx=5, pady=10, columnspan=4,
        )
        self.reference_email_text.configure(state='normal')

        # -----------------------------
        # Control Email Sending Checkbox
        # -----------------------------
        label_control_email_sending = ttk.Label(
            form, text='Control Email Sending:',
            font=('Helvetica', 12),
        )
        label_control_email_sending.grid(
            row=5, column=0, sticky='e', padx=5, pady=10,
        )

        self.control_email_sending_var = ttk.BooleanVar(value=False)
        checkbox_control_email_sending = ttk.Checkbutton(
            form,
            text='',
            variable=self.control_email_sending_var,
            bootstyle='success-round-toggle',
        )
        checkbox_control_email_sending.grid(
            row=5, column=1, sticky='w', padx=5, pady=10, columnspan=2,
        )

        # -----------------------------
        # Start Button
        # -----------------------------
        self.start_button = ttk.Button(
            form_frame,
            text='Start Process',
            command=self.start_process,
            bootstyle='primary',
        )
        self.start_button.pack(pady=20)

        # Let the reference email text area expand if the window is resized
        form.rowconfigure(4, weight=1)

    def load_daily_limit(self):
        """Load the daily limit from the database (settings table)."""
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'daily_limit'")
        result = cursor.fetchone()
        if result:
            self.daily_limit_var.set(int(result[0]))
        else:
            # If not set, default to 100 (or any default you want)
            self.daily_limit_var.set(100)
        connection.close()

    def save_daily_limit(self):
        """Save the daily limit to the database (settings table)."""
        daily_limit = self.daily_limit_var.get()
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
            ('daily_limit', str(daily_limit)),
        )
        connection.commit()
        connection.close()

    def update_emails_sent_today(self):
        """Get the number of emails sent today from the emails table."""
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM emails WHERE DATE(timestamp) = DATE('now', 'localtime')",
        )
        result = cursor.fetchone()
        emails_sent_today = result[0] if result else 0
        connection.close()
        self.emails_sent_today_var.set(emails_sent_today)

    def on_daily_limit_changed(self, *args):
        self.save_daily_limit()

    def upload_csv(self):
        """Let user select a CSV and validate it."""
        file_path = filedialog.askopenfilename(
            filetypes=[('CSV files', '*.csv')],
        )
        if file_path:
            self.file_path_var.set(file_path)
            try:
                data = pd.read_csv(file_path)

                # We check required column(s); in your example, "Person Linkedin Url"
                if 'Person Linkedin Url' in data.columns:
                    messagebox.showinfo('Success', 'CSV file is valid.')
                    self.csv_data = data  # Store the data

                    # Log the start of the run and get run_id
                    run_id = log_run_start(file_name=file_path)
                    self.run_id = run_id

                    # Call the upload callback if needed
                    if self.upload_callback:
                        self.upload_callback(data, run_id)
                else:
                    messagebox.showwarning(
                        'Validation Error',
                        "CSV must contain 'Person Linkedin Url' column.",
                    )
                    # Log the run as Error due to missing columns
                    run_id = log_run_start(file_name=file_path)
                    log_run_end(
                        run_id, status='Error',
                        error_message='Missing required columns.',
                    )
            except Exception as e:
                messagebox.showerror(
                    'Error',
                    f"Failed to read CSV: {e}",
                )
                # Log the run as Error due to exception
                run_id = log_run_start(file_name=file_path)
                log_run_end(run_id, status='Error', error_message=str(e))

    def start_process(self):
        """
        Start processing the entire CSV, respecting the daily limit.
        We do not ask for partial runs or a start row anymore.
        """
        if self.csv_data is None:
            messagebox.showwarning(
                'No CSV File', 'Please upload a CSV file before starting.',
            )
            return

        # Disable the Start and Upload buttons to prevent multiple clicks/changes
        self.disable_start_button()

        # Gather user input
        visible_mode = self.visible_mode_var.get()
        prompt_text = self.prompt_text.get('1.0', 'end').strip()
        prompt = prompt_text if prompt_text else None

        reference_email_text = self.reference_email_text.get(
            '1.0', 'end',
        ).strip()
        reference_email = reference_email_text if reference_email_text else None

        control_email_sending = self.control_email_sending_var.get()

        # We run everything in a separate thread
        self.automation_thread = threading.Thread(
            target=self.run_selenium_thread,
            args=(
                self.csv_data,               # the entire data
                visible_mode,
                prompt,
                reference_email,
                control_email_sending,
                self.run_id,
            ),
            daemon=True,
        )
        self.automation_thread.start()

    def run_selenium_thread(
        self,
        data,
        visible_mode,
        prompt,
        reference_email,
        control_email_sending,
        run_id,
    ):
        """
        Process all rows in 'data' chunk by chunk.
        For each day:
          - Send up to (daily_limit - emails_sent_today) rows.
          - If more rows remain, sleep until next day, then continue.
        We do NOT modify run_selenium_automation; we just pass in subsets of data.
        """
        total_rows = len(data)
        current_index = 0
        print(f'{total_rows=}')
        print(f'{current_index=}')

        try:
            while current_index < total_rows:
                # Refresh how many emails we've sent today
                self.after(0, self.update_emails_sent_today)
                # Wait a tiny bit to ensure emails_sent_today_var is updated
                time.sleep(0.1)

                emails_sent_today = self.emails_sent_today_var.get()
                daily_limit = self.daily_limit_var.get()

                # If we are already at or above today's limit, wait until next day
                if emails_sent_today >= daily_limit:
                    self.show_info_message(
                        'Daily Limit Reached',
                        f"You've reached today's limit of {daily_limit}. "
                        'Waiting until next day to continue...',
                    )
                    self.wait_until_next_day()
                    continue

                # Figure out how many rows we can process "today"
                chunk_size = daily_limit - emails_sent_today
                print(f'{chunk_size=}')
                remaining = total_rows - current_index
                print(f'{remaining=}')
                if chunk_size > remaining:
                    chunk_size = remaining
                print(f'{chunk_size=}')

                # Slice the data for today's chunk
                chunk_data = data.iloc[current_index: current_index + chunk_size]

                # We'll define a callback that runs after run_selenium_automation finishes
                # but to keep the flow simpler, we can pass a callback that does nothing special:
                def automation_callback(success, message):
                    if not success:
                        self.show_error_message('Automation Error', message)

                # Pass the chunk to run_selenium_automation
                run_selenium_automation(
                    data=chunk_data,
                    visible_mode=visible_mode,
                    prompt=prompt,
                    reference_email=reference_email,
                    control_email_sending=control_email_sending,
                    run_id=run_id,
                    callback=automation_callback,
                )

                # Now we've used chunk_size rows for today
                current_index += chunk_size

                # Update "emails_sent_today" label (the DB is updated by run_selenium_automation)
                self.after(0, self.update_emails_sent_today)
                time.sleep(0.1)

                # If we still have more rows to go and we've used up today's limit, sleep
                if current_index < total_rows:
                    # Check how many we have now (in case chunk < daily_limit)
                    self.after(0, self.update_emails_sent_today)
                    time.sleep(0.1)
                    if self.emails_sent_today_var.get() >= daily_limit:
                        print(
                            "Today's limit is fully used. Waiting until next day...",
                        )
                        self.wait_until_next_day()

            # All rows processed
            self.show_info_message(
                'Process Completed',
                f'Successfully processed all {total_rows} rows.',
            )

        except Exception as e:
            self.show_error_message('Process Error', str(e))
        finally:
            # Re-enable the buttons once we're done
            self.enable_start_button()

    def wait_until_next_day(self):
        """
        Sleep (block) until midnight local time.
        This stops processing in this thread until next day.
        """
        now = datetime.now()
        # Next day at 00:00:00
        next_day = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0,
        )
        print(f'{next_day=}')
        seconds_to_wait = (next_day - now).total_seconds()
        print(f'{seconds_to_wait=}')
        time.sleep(seconds_to_wait)

    def disable_start_button(self):
        self.start_button.config(state='disabled')
        self.button_upload.config(state='disabled')

    def enable_start_button(self):
        self.start_button.config(state='normal')
        self.button_upload.config(state='normal')

    def show_info_message(self, title, message):
        """Show a messagebox info from the main thread."""
        self.after(0, lambda: messagebox.showinfo(title, message))

    def show_error_message(self, title, message):
        """Show a messagebox error from the main thread."""
        self.after(0, lambda: messagebox.showerror(title, message))
