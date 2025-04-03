import sqlite3
import threading
import time
from datetime import datetime
from datetime import timedelta
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

import pytz
import ttkbootstrap as ttk

from src.inmail.personalized_email import run_selenium_automation_with_retries
from src.ui.pages.utils import proccess_search_variable

DB_PATH = 'run_history.db'


class HomePage(ttk.Frame):
    def __init__(self, parent, upload_callback=None):
        super().__init__(parent)
        self.upload_callback = upload_callback
        self.run_id = None  # To store the current run_id

        # Thread reference for Selenium automation
        self.automation_thread = None

        # Initialize variables for daily limit and emails sent today
        self.daily_limit_var = ttk.IntVar()
        self.emails_sent_today_var = ttk.IntVar()

        # Load daily limit and update emails sent today
        self.load_daily_limit()
        self.update_emails_sent_today()
        self.job_titles_var = ttk.StringVar()
        self.locations_var = ttk.StringVar()
        self.skills_assessments_var = ttk.StringVar()
        self.companies_var = ttk.StringVar()
        self.schools_var = ttk.StringVar()
        self.industries_var = ttk.StringVar()
        self.keywords_var = ttk.StringVar()
        self.create_widgets()

    def show_field_info(self):
        messagebox.showinfo(
            'Multiple Values',
            'Separate multiple values with a semicolon (;).',
        )

    def create_widgets(self):
        # Main frame for the form
        # --- Scrollable container ---
        canvas = ttk.Canvas(self)
        scrollbar = ttk.Scrollbar(
            self, orient='vertical', command=canvas.yview,
        )
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            '<Configure>', lambda e: canvas.configure(
                scrollregion=canvas.bbox('all'),
            ),
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        form_frame = scrollable_frame
        # Use a LabelFrame to group form fields with a title
        form = ttk.Labelframe(
            form_frame,
            text='Automation Settings',
            padding=(20, 10),
        )
        form.pack(fill='both', expand=True)

        # Configure grid columns for alignment (simple approach)
        for col_index in range(6):
            if col_index == 1:
                form.columnconfigure(col_index, weight=1)
            else:
                form.columnconfigure(col_index, weight=0)

        # -----------------------------
        # Daily Limit / Emails Sent
        # -----------------------------
        label_daily_limit = ttk.Label(
            form,
            text='Daily Limit:',
            font=('Helvetica', 12),
        )
        label_daily_limit.grid(row=1, column=0, sticky='e', padx=5, pady=10)

        entry_daily_limit = ttk.Entry(
            form,
            textvariable=self.daily_limit_var,
            width=10,
        )
        entry_daily_limit.grid(row=1, column=1, sticky='w', padx=5, pady=10)

        # Bind the daily limit variable to save when changed
        self.daily_limit_var.trace_add('write', self.on_daily_limit_changed)

        label_emails_sent_today = ttk.Label(
            form,
            text='Emails sent today:',
            font=('Helvetica', 12),
        )
        label_emails_sent_today.grid(
            row=1,
            column=2,
            sticky='e',
            padx=5,
            pady=10,
        )

        label_emails_sent_today_value = ttk.Label(
            form,
            textvariable=self.emails_sent_today_var,
            font=('Helvetica', 12),
        )
        label_emails_sent_today_value.grid(
            row=1,
            column=3,
            sticky='w',
            padx=5,
            pady=10,
        )
        # -----------------------------
        # Row 5: Reference Email (ScrolledText)
        # -----------------------------
        label_reference_email = ttk.Label(
            form,
            text='Reference Email:',
            font=('Helvetica', 12),
        )
        label_reference_email.grid(
            row=5,
            column=0,
            sticky='ne',
            padx=5,
            pady=10,
        )

        self.reference_email_text = ScrolledText(
            form,
            wrap='word',
            width=50,
            height=10,
            font=('Helvetica', 12),
        )
        self.reference_email_text.grid(
            row=5,
            column=1,
            sticky='nsew',
            padx=5,
            pady=10,
            columnspan=4,
        )
        self.reference_email_text.configure(state='normal')

        # -----------------------------
        # Visible Mode Toggle
        # -----------------------------
        label_visible_mode = ttk.Label(
            form,
            text='Visible Mode:',
            font=('Helvetica', 12),
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
            row=2,
            column=1,
            sticky='w',
            padx=5,
            pady=10,
            columnspan=2,
        )

        # -----------------------------
        # Prompt (ScrolledText)
        # -----------------------------
        label_prompt = ttk.Label(
            form,
            text='Prompt:',
            font=('Helvetica', 12),
        )
        label_prompt.grid(row=3, column=0, sticky='ne', padx=5, pady=10)

        self.prompt_text = ScrolledText(
            form,
            wrap='word',
            width=50,
            height=4,
            font=('Helvetica', 12),
        )
        self.prompt_text.grid(
            row=3,
            column=1,
            sticky='nsew',
            padx=5,
            pady=10,
            columnspan=4,
        )
        # -----------------------------
        # Row 7: Job Titles
        # -----------------------------
        label_job_titles = ttk.Label(
            form,
            text='Job Titles:',
            font=('Helvetica', 12),
        )
        label_job_titles.grid(row=7, column=0, sticky='e', padx=5, pady=10)

        entry_job_titles = ttk.Entry(
            form,
            textvariable=self.job_titles_var,
            width=40,  # Increase width if you prefer
        )
        entry_job_titles.grid(
            row=7,
            column=1,
            sticky='ew',
            padx=5,
            pady=10,
            columnspan=3,
        )

        info_button_job_titles = ttk.Button(
            form,
            text='?',
            command=self.show_field_info,
            bootstyle='info-outline',
        )
        info_button_job_titles.grid(
            row=7,
            column=4,
            sticky='w',
            padx=5,
            pady=10,
        )

        # -----------------------------
        # Row 8: Locations
        # -----------------------------
        label_locations = ttk.Label(
            form,
            text='Locations:',
            font=('Helvetica', 12),
        )
        label_locations.grid(row=8, column=0, sticky='e', padx=5, pady=10)

        entry_locations = ttk.Entry(
            form,
            textvariable=self.locations_var,
            width=40,
        )
        entry_locations.grid(
            row=8,
            column=1,
            sticky='ew',
            padx=5,
            pady=10,
            columnspan=3,
        )

        info_button_locations = ttk.Button(
            form,
            text='?',
            command=self.show_field_info,
            bootstyle='info-outline',
        )
        info_button_locations.grid(
            row=8,
            column=4,
            sticky='w',
            padx=5,
            pady=10,
        )

        # -----------------------------
        # Row 9: Skills and Assessments
        # -----------------------------
        label_skills = ttk.Label(
            form,
            text='Skills and Assessments:',
            font=('Helvetica', 12),
        )
        label_skills.grid(row=9, column=0, sticky='e', padx=5, pady=10)

        entry_skills = ttk.Entry(
            form,
            textvariable=self.skills_assessments_var,
            width=40,
        )
        entry_skills.grid(
            row=9,
            column=1,
            sticky='ew',
            padx=5,
            pady=10,
            columnspan=3,
        )

        info_button_skills = ttk.Button(
            form,
            text='?',
            command=self.show_field_info,
            bootstyle='info-outline',
        )
        info_button_skills.grid(row=9, column=4, sticky='w', padx=5, pady=10)

        # -----------------------------
        # Row 10: Companies
        # -----------------------------
        label_companies = ttk.Label(
            form,
            text='Companies:',
            font=('Helvetica', 12),
        )
        label_companies.grid(row=10, column=0, sticky='e', padx=5, pady=10)

        entry_companies = ttk.Entry(
            form,
            textvariable=self.companies_var,
            width=40,
        )
        entry_companies.grid(
            row=10,
            column=1,
            sticky='ew',
            padx=5,
            pady=10,
            columnspan=3,
        )

        info_button_companies = ttk.Button(
            form,
            text='?',
            command=self.show_field_info,
            bootstyle='info-outline',
        )
        info_button_companies.grid(
            row=10,
            column=4,
            sticky='w',
            padx=5,
            pady=10,
        )

        # -----------------------------
        # Row 11: Schools
        # -----------------------------
        label_schools = ttk.Label(
            form,
            text='Schools:',
            font=('Helvetica', 12),
        )
        label_schools.grid(row=11, column=0, sticky='e', padx=5, pady=10)

        entry_schools = ttk.Entry(
            form,
            textvariable=self.schools_var,
            width=40,
        )
        entry_schools.grid(
            row=11,
            column=1,
            sticky='ew',
            padx=5,
            pady=10,
            columnspan=3,
        )

        info_button_schools = ttk.Button(
            form,
            text='?',
            command=self.show_field_info,
            bootstyle='info-outline',
        )
        info_button_schools.grid(row=11, column=4, sticky='w', padx=5, pady=10)

        # -----------------------------
        # Row 13: Industries
        # -----------------------------
        label_industries = ttk.Label(
            form,
            text='Industries:',
            font=('Helvetica', 12),
        )
        label_industries.grid(row=13, column=0, sticky='e', padx=5, pady=10)

        entry_industries = ttk.Entry(
            form,
            textvariable=self.industries_var,
            width=40,
        )
        entry_industries.grid(
            row=13,
            column=1,
            sticky='ew',
            padx=5,
            pady=10,
            columnspan=3,
        )

        info_button_industries = ttk.Button(
            form,
            text='?',
            command=self.show_field_info,
            bootstyle='info-outline',
        )
        info_button_industries.grid(
            row=13,
            column=4,
            sticky='w',
            padx=5,
            pady=10,
        )

        # -----------------------------
        # Row 14: Keywords
        # -----------------------------
        label_keywords = ttk.Label(
            form,
            text='Keywords:',
            font=('Helvetica', 12),
        )
        label_keywords.grid(row=14, column=0, sticky='e', padx=5, pady=10)

        entry_keywords = ttk.Entry(
            form,
            textvariable=self.keywords_var,
            width=40,
        )
        entry_keywords.grid(
            row=14,
            column=1,
            sticky='ew',
            padx=5,
            pady=10,
            columnspan=3,
        )

        info_button_keywords = ttk.Button(
            form,
            text='?',
            command=self.show_field_info,
            bootstyle='info-outline',
        )
        info_button_keywords.grid(
            row=14,
            column=4,
            sticky='w',
            padx=5,
            pady=10,
        )

        # -----------------------------
        # Row 6: Control Email Sending Checkbox
        # -----------------------------
        label_control_email_sending = ttk.Label(
            form,
            text='Control Email Sending:',
            font=('Helvetica', 12),
        )
        label_control_email_sending.grid(
            row=6,
            column=0,
            sticky='e',
            padx=5,
            pady=10,
        )

        self.control_email_sending_var = ttk.BooleanVar(value=False)
        checkbox_control_email_sending = ttk.Checkbutton(
            form,
            text='',
            variable=self.control_email_sending_var,
            bootstyle='success-round-toggle',
        )
        checkbox_control_email_sending.grid(
            row=6,
            column=1,
            sticky='w',
            padx=5,
            pady=10,
            columnspan=2,
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
        form.rowconfigure(5, weight=1)

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
            "SELECT COUNT(*) FROM emails WHERE DATE(timestamp) = DATE('now', 'localtime')",  # noqa: E501
        )
        result = cursor.fetchone()
        emails_sent_today = result[0] if result else 0
        connection.close()
        self.emails_sent_today_var.set(emails_sent_today)

    def on_daily_limit_changed(self, *args):
        self.save_daily_limit()

    def disable_start_button(self):
        self.start_button.config(state='disabled')

    def start_process(self):
        """
        Start processing the entire CSV, respecting the daily limit.
        We do not ask for partial runs or a start row anymore.
        """
        print('Started')
        print(f"{self.__dict__=}")
        print(f"{self.job_titles_var.get()=}")
        # return

        # Disable the Start and Upload buttons to prevent multiple clicks
        self.disable_start_button()

        # Gather user input
        visible_mode = self.visible_mode_var.get()
        prompt_text = self.prompt_text.get('1.0', 'end').strip()
        prompt = prompt_text if prompt_text else None

        control_email_sending = self.control_email_sending_var.get()
        job_titles = proccess_search_variable(self.job_titles_var.get())
        locations = proccess_search_variable(self.locations_var.get())
        skills_assessments = proccess_search_variable(
            self.skills_assessments_var.get(),
        )
        companies = proccess_search_variable(self.companies_var.get())
        schools = proccess_search_variable(self.schools_var.get())
        industries = proccess_search_variable(self.industries_var.get())
        keywords = proccess_search_variable(self.keywords_var.get())
        print(f"{job_titles=}")
        print(f"{locations=}")
        print(f"{skills_assessments=}")
        print(f"{companies=}")
        print(f"{schools=}")
        print(f"{industries=}")
        print(f"{keywords=}")
        # We run everything in a separate thread
        self.automation_thread = threading.Thread(
            target=self.run_selenium_thread,
            args=(
                visible_mode,
                prompt,
                control_email_sending,
                self.run_id,
                job_titles,
                locations,
                skills_assessments,
                companies,
                schools,
                industries,
                keywords,
            ),
            daemon=True,
        )
        self.automation_thread.start()

    def run_selenium_thread(
        self,
        visible_mode,
        prompt,
        control_email_sending,
        run_id,
        job_titles,
        locations,
        skills_assessments,
        companies,
        schools,
        industries,
        keywords,
    ):
        """
        Process all rows in 'data' chunk by chunk.
        For each day:
          - Send up to (daily_limit - emails_sent_today) rows.
          - If more rows remain, sleep until next day, then continue.
        We do NOT modify run_selenium_automation;
        we just pass in subsets of data.
        """
        print(f"{job_titles=}")
        print(f"{locations=}")
        print(f"{skills_assessments=}")
        print(f"{companies=}")
        print(f"{schools=}")
        print(f"{industries=}")
        print(f"{keywords=}")
        try:
            # We'll define a callback that runs
            # after run_selenium_automation finishes
            # but to keep the flow simpler
            # we can pass a callback that does nothing special:
            def automation_callback(success, message):
                if not success:
                    self.show_error_message('Automation Error', message)

            # Pass the chunk to run_selenium_automation
            run_selenium_automation_with_retries(
                visible_mode=visible_mode,
                prompt=prompt,
                control_email_sending=control_email_sending,
                run_id=run_id,
                callback=automation_callback,
                job_titles=job_titles,
                locations=locations,
                skills_assessments=skills_assessments,
                companies=companies,
                schools=schools,
                industries=industries,
                keywords=keywords,
            )
        except Exception as e:
            self.show_error_message('Process Error', str(e))
        finally:
            # Re-enable the buttons once we're done
            self.enable_start_button()

    def wait_until_next_day(self):
        """
        Sleep (block) until 9 AM CET.
        This stops processing in this thread until the specified time.
        """
        # Get current time in UTC
        now_utc = datetime.now(pytz.utc)

        # Convert to CET
        cet_timezone = pytz.timezone('CET')
        now_cet = now_utc.astimezone(cet_timezone)

        # Calculate next 5 AM CET
        if now_cet.hour >= 5:
            # If it's past 6 AM today, set to 5 AM next day
            next_cet = (now_cet + timedelta(days=1)).replace(
                hour=5,
                minute=0,
                second=0,
                microsecond=0,
            )
        else:
            # If it's before 5 AM today, set to 5 AM today
            next_cet = now_cet.replace(
                hour=5,
                minute=0,
                second=0,
                microsecond=0,
            )

        # Convert the target time back to UTC
        next_utc = next_cet.astimezone(pytz.utc)

        # Calculate the time to wait in seconds
        seconds_to_wait = (next_utc - now_utc).total_seconds()
        print(f"{next_cet=}")
        print(f"{seconds_to_wait=}")
        time.sleep(seconds_to_wait)

    def show_info_message(self, title, message):
        """Show a messagebox info from the main thread."""
        self.after(0, lambda: messagebox.showinfo(title, message))

    def show_error_message(self, title, message):
        """Show a messagebox error from the main thread."""
        self.after(0, lambda: messagebox.showerror(title, message))

    def enable_start_button(self):
        self.start_button.config(state='normal')
