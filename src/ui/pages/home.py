# src/ui/pages/home.py
import threading
from tkinter import filedialog
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

import pandas as pd
import ttkbootstrap as ttk

from src.database.handlers import log_run_end
from src.database.handlers import log_run_start
from src.inmail.personalized_email import run_selenium_automation
# Ensure correct import


class HomePage(ttk.Frame):
    def __init__(self, parent, upload_callback=None):
        super().__init__(parent)
        self.upload_callback = upload_callback
        self.csv_data = None  # To store the loaded CSV data
        self.run_id = None  # To store the current run_id
        self.automation_thread = None  # Initialize automation_thread
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

        # Configure grid columns for alignment
        form.columnconfigure(0, weight=0)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(2, weight=0)

        # -----------------------------
        # Row 0: CSV File Selection
        # -----------------------------
        label_file = ttk.Label(form, text='CSV File:', font=('Helvetica', 12))
        label_file.grid(row=0, column=0, sticky='e', padx=5, pady=10)

        # Entry to display selected file path
        self.file_path_var = ttk.StringVar(value='')
        entry_file = ttk.Entry(
            form, textvariable=self.file_path_var, state='readonly', width=40,
        )
        entry_file.grid(row=0, column=1, sticky='ew', padx=5, pady=10)

        # Button to upload CSV
        button_upload = ttk.Button(
            form, text='Browse',
            command=self.upload_csv,
            bootstyle='success-outline',
        )
        button_upload.grid(row=0, column=2, sticky='w', padx=5, pady=10)

        # -----------------------------
        # Row 1: Number of Items to Run
        # -----------------------------
        label_num_items = ttk.Label(
            form, text='Number of items to run (0 for all):',
            font=('Helvetica', 12),
        )
        label_num_items.grid(row=1, column=0, sticky='e', padx=5, pady=10)

        self.num_items_var = ttk.IntVar(value=0)
        entry_num_items = ttk.Entry(
            form, textvariable=self.num_items_var, width=10,
        )
        entry_num_items.grid(
            row=1, column=1, sticky='w',
            padx=5, pady=10, columnspan=2,
        )

        # -----------------------------
        # Row 1.1: Start Row
        # -----------------------------
        label_start_row = ttk.Label(
            form, text='Start Row:', font=('Helvetica', 12),
        )
        label_start_row.grid(row=1, column=3, sticky='e', padx=5, pady=10)

        # Default to 1 (assuming 1-based indexing)
        self.start_row_var = ttk.IntVar(value=1)
        entry_start_row = ttk.Entry(
            form, textvariable=self.start_row_var, width=10,
        )
        entry_start_row.grid(
            row=1, column=4, sticky='w',
            padx=5, pady=10,
        )

        # Adjust column configuration if necessary
        form.columnconfigure(3, weight=0)
        form.columnconfigure(4, weight=0)

        # -----------------------------
        # Row 2: Visible Mode Toggle
        # -----------------------------
        label_visible_mode = ttk.Label(
            form, text='Visible Mode:', font=('Helvetica', 12),
        )
        label_visible_mode.grid(row=2, column=0, sticky='e', padx=5, pady=10)

        self.visible_mode_var = ttk.BooleanVar(value=True)  # Default to True
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
        # Row 3: Prompt (ScrolledText)
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
        # Allow prompt field to maintain its size
        form.rowconfigure(3, weight=0)

        # -----------------------------
        # Row 4: Reference Email
        # -----------------------------
        label_reference_email = ttk.Label(
            form, text='Reference Email:', font=('Helvetica', 12),
        )
        label_reference_email.grid(
            row=4, column=0, sticky='ne', padx=5, pady=10,
        )

        self.reference_email_text = ScrolledText(
            form, wrap='word', width=50, height=10,
            font=('Helvetica', 12),
        )
        self.reference_email_text.grid(
            row=4, column=1, sticky='nsew', padx=5, pady=10,
            columnspan=4,
        )
        self.reference_email_text.configure(state='normal')

        form.rowconfigure(4, weight=1)

        # -----------------------------
        # Row 5: Control Email Sending Checkbox
        # -----------------------------
        label_control_email_sending = ttk.Label(
            form, text='Control Email Sending:',
            font=('Helvetica', 12),
        )
        label_control_email_sending.grid(
            row=5, column=0, sticky='e', padx=5, pady=10,
        )

        self.control_email_sending_var = ttk.BooleanVar(
            value=False,
        )  # Default to False
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
        # Start Button at the Bottom
        # -----------------------------
        self.start_button = ttk.Button(
            form_frame, text='Start Process',
            command=self.start_process,
            bootstyle='primary',
        )
        self.start_button.pack(pady=20)

    def upload_csv(self):
        file_path = filedialog.askopenfilename(
            filetypes=[('CSV files', '*.csv')],
        )
        if file_path:
            self.file_path_var.set(file_path)
            try:
                data = pd.read_csv(file_path)
                required_columns = {'Person Linkedin Url'}
                if 'Person Linkedin Url' in data.columns:
                    messagebox.showinfo('Success', 'CSV file is valid.')
                    self.csv_data = data  # Store the data

                    # Log the start of the run and get run_id
                    run_id = log_run_start(file_name=file_path)
                    self.run_id = run_id  # Store run_id for later use

                    # Call the upload callback if needed
                    if self.upload_callback:
                        # Pass data and run_id to the callback
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
        if self.csv_data is None:
            messagebox.showwarning(
                'No CSV File', 'Please upload a CSV file before starting.',
            )
            return

        num_items = self.num_items_var.get()
        visible_mode = self.visible_mode_var.get()

        # Retrieve the start row
        start_row = self.start_row_var.get()
        if start_row < 1:
            messagebox.showwarning(
                'Invalid Start Row',
                'Start row must be 1 or greater.',
            )
            return

        total_rows = len(self.csv_data)
        if start_row > total_rows:
            messagebox.showwarning(
                'Start Row Out of Range',
                f'Start row ({start_row}) exceeds total rows in CSV ({
                    total_rows
                }).',
            )
            return

        # Adjust for zero-based indexing in pandas
        start_index = start_row - 1

        # Retrieve the prompt and reference email
        prompt_text = self.prompt_text.get('1.0', 'end').strip()
        prompt = prompt_text if prompt_text else None

        reference_email_text = self.reference_email_text.get(
            '1.0', 'end',
        ).strip()
        reference_email = reference_email_text if reference_email_text else None  # noqa: E501

        # Retrieve the control email sending option
        control_email_sending = self.control_email_sending_var.get()

        # Process the data based on user inputs
        if num_items == 0:
            num_items = total_rows - start_index
        elif num_items > (total_rows - start_index):
            num_items = total_rows - start_index

        data_to_process = self.csv_data.iloc[start_index:start_index + num_items]  # noqa: E501

        # Disable the Start button to prevent multiple clicks
        self.disable_start_button()

        # Start the Selenium automation in a new thread
        self.automation_thread = threading.Thread(
            target=self.run_selenium_thread,
            args=(
                data_to_process, visible_mode, prompt,
                reference_email, control_email_sending, self.run_id,
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
        # Define a callback function to handle completion or errors
        def automation_callback(success, message):
            if success:
                self.show_info_message('Process Completed', message)
            else:
                self.show_error_message('Automation Error', message)
            # Re-enable the Start button
            self.enable_start_button()

        run_selenium_automation(
            data=data,
            visible_mode=visible_mode,
            prompt=prompt,
            reference_email=reference_email,
            control_email_sending=control_email_sending,
            run_id=run_id,
            callback=automation_callback,
        )

    def disable_start_button(self):
        self.start_button.config(state='disabled')

    def enable_start_button(self):
        self.start_button.config(state='normal')

    def show_info_message(self, title, message):
        # Show messagebox from the main thread
        self.after(0, lambda: messagebox.showinfo(title, message))

    def show_error_message(self, title, message):
        # Show messagebox from the main thread
        self.after(0, lambda: messagebox.showerror(title, message))
