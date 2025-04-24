import threading
import time
from datetime import datetime
from datetime import timedelta
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

import pytz
import ttkbootstrap as ttk

from brouse.main import run_agents

# from src

DB_PATH = 'run_history.db'


class HomePage(ttk.Frame):
    def __init__(self, parent, upload_callback=None):
        super().__init__(parent)
        self.upload_callback = upload_callback
        self.run_id = None  # To store the current run_id

        # Thread reference for Selenium automation
        self.automation_thread = None

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
            self,
            orient='vertical',
            command=canvas.yview,
        )
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(
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

    def disable_start_button(self):
        self.start_button.config(state='disabled')

    def start_process(self):
        """
        Start processing the entire CSV, respecting the daily limit.
        We do not ask for partial runs or a start row anymore.
        """
        print('Started')
        print(f"{self.__dict__=}")
        # return

        # Disable the Start and Upload buttons to prevent multiple clicks
        self.disable_start_button()

        # Gather user input
        prompt_text = self.prompt_text.get('1.0', 'end').strip()
        prompt = prompt_text if prompt_text else None
        reference_email_text = self.reference_email_text.get(
            '1.0',
            'end',
        ).strip()
        reference_email = (
            reference_email_text if reference_email_text else None
        )  # noqa: E501
        # We run everything in a separate thread
        self.automation_thread = threading.Thread(
            target=self.run_selenium_thread,
            args=(
                prompt,
                self.run_id,
                reference_email,
            ),
            daemon=True,
        )
        self.automation_thread.start()

    def run_selenium_thread(
        self,
        prompt,
        run_id,
        reference_email,
    ):
        """
        Process all rows in 'data' chunk by chunk.
        For each day:
          - Send up to (daily_limit - emails_sent_today) rows.
          - If more rows remain, sleep until next day, then continue.
        We do NOT modify run_selenium_automation;
        we just pass in subsets of data.
        """
        print(f"{reference_email=}")
        try:
            # We'll define a callback that runs
            # after run_selenium_automation finishes
            # but to keep the flow simpler
            # we can pass a callback that does nothing special:
            def automation_callback(success, message):
                if not success:
                    self.show_error_message('Automation Error', message)

            # Pass the chunk to run_selenium_automation
            # run_selenium_automation_with_retries(
            #     visible_mode=visible_mode,
            #     prompt=prompt,
            #     control_email_sending=control_email_sending,
            #     run_id=run_id,
            #     callback=automation_callback,
            #     job_titles=job_titles,
            #     locations=locations,
            #     skills_assessments=skills_assessments,
            #     companies=companies,
            #     schools=schools,
            #     industries=industries,
            #     keywords=keywords,
            #     reference_email=reference_email,
            #     past_companies=past_companies,
            #     job_functions=job_functions,
            #     company_sizes=company_sizes,
            #     seniority=seniority,
            # )
            print(f"{reference_email=}")
            print(f"{prompt=}")
            run_agents(reference_email=reference_email, prompt=prompt)
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
