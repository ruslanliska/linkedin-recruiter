import threading
from tkinter import filedialog
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

import pandas as pd
import ttkbootstrap as ttk

from src.inmail.personalized_email import run_selenium_automation
# Import the Selenium automation function


class HomePage(ttk.Frame):
    def __init__(self, parent, upload_callback=None):
        super().__init__(parent)
        self.upload_callback = upload_callback
        self.csv_data = None  # To store the loaded CSV data
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
            row=3, column=1, sticky='nsew', padx=5, pady=10, columnspan=2,
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
            form, wrap='word', width=50, height=10, font=('Helvetica', 12),
        )
        self.reference_email_text.grid(
            row=4, column=1, sticky='nsew', padx=5, pady=10, columnspan=2,
        )
        form.rowconfigure(4, weight=1)  # Allow reference email field to expand

        # -----------------------------
        # Row 5: Control Email Sending Checkbox
        # -----------------------------
        label_control_email_sending = ttk.Label(
            form, text='Control Email Sending:', font=('Helvetica', 12),
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
                if 'Person Linkedin Url' in data.columns \
                        and 'Email' in data.columns:
                    messagebox.showinfo('Success', 'CSV file is valid.')
                    self.csv_data = data  # Store the data
                    # Call the upload callback if needed
                    if self.upload_callback:
                        self.upload_callback(data)
                else:
                    messagebox.showwarning(
                        'Validation Error',
                        "CSV must contain 'Person Linkedin Url' and 'Email' columns.",
                    )
            except Exception as e:
                messagebox.showerror(
                    'Error',
                    f"Failed to read CSV: {e}",
                )

    def start_process(self):
        if self.csv_data is None:
            messagebox.showwarning(
                'No CSV File', 'Please upload a CSV file before starting.',
            )
            return

        num_items = self.num_items_var.get()
        visible_mode = self.visible_mode_var.get()

        # Retrieve the prompt and reference email
        prompt_text = self.prompt_text.get('1.0', 'end').strip()
        prompt = prompt_text if prompt_text else None

        reference_email_text = self.reference_email_text.get(
            '1.0', 'end',
        ).strip()
        reference_email = reference_email_text if reference_email_text else None

        # Retrieve the control email sending option
        control_email_sending = self.control_email_sending_var.get()

        # Process the data based on user inputs
        if num_items == 0 or num_items > len(self.csv_data):
            num_items = len(self.csv_data)

        data_to_process = self.csv_data.head(num_items)

        # Disable the Start button to prevent multiple clicks
        self.disable_start_button()

        # Start the Selenium automation in a new thread
        threading.Thread(
            target=self.run_selenium_thread,
            args=(
                data_to_process, visible_mode, prompt,
                reference_email, control_email_sending,
            ),
            daemon=True,
        ).start()

    def run_selenium_thread(
        self,
        data,
        visible_mode,
        prompt,
        reference_email,
        control_email_sending,
    ):
        # Define a callback function to handle completion or errors
        def automation_callback(success, message):
            if success:
                self.show_info_message('Process Completed', message)
            else:
                self.show_error_message('Automation Error', message)
            # Re-enable the Start button
            self.enable_start_button()

        # Call the Selenium automation function
        run_selenium_automation(
            data=data,
            visible_mode=visible_mode,
            prompt=prompt,
            reference_email=reference_email,
            control_email_sending=control_email_sending,
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
