import threading
from tkinter import filedialog
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

import pandas as pd
import ttkbootstrap as ttk
from selenium_automation.inmail import run_selenium_automation


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
        # Row 0: LinkedIn Email
        # -----------------------------
        label_email = ttk.Label(
            form, text='LinkedIn Email:', font=('Helvetica', 12),
        )
        label_email.grid(row=0, column=0, sticky='e', padx=5, pady=10)

        self.linkedin_email_var = ttk.StringVar()
        entry_email = ttk.Entry(
            form, textvariable=self.linkedin_email_var, width=40,
        )
        entry_email.grid(
            row=0, column=1, sticky='ew',
            padx=5, pady=10, columnspan=2,
        )

        # -----------------------------
        # Row 1: LinkedIn Password
        # -----------------------------
        label_password = ttk.Label(
            form, text='LinkedIn Password:', font=('Helvetica', 12),
        )
        label_password.grid(row=1, column=0, sticky='e', padx=5, pady=10)

        self.linkedin_password_var = ttk.StringVar()
        entry_password = ttk.Entry(
            form, textvariable=self.linkedin_password_var, width=40, show='*',
        )
        entry_password.grid(
            row=1, column=1, sticky='ew',
            padx=5, pady=10, columnspan=2,
        )

        # -----------------------------
        # Row 2: CSV File Selection
        # -----------------------------
        label_file = ttk.Label(form, text='CSV File:', font=('Helvetica', 12))
        label_file.grid(row=2, column=0, sticky='e', padx=5, pady=10)

        # Entry to display selected file path
        self.file_path_var = ttk.StringVar(value='')
        entry_file = ttk.Entry(
            form, textvariable=self.file_path_var, state='readonly', width=40,
        )
        entry_file.grid(row=2, column=1, sticky='ew', padx=5, pady=10)

        # Button to upload CSV
        button_upload = ttk.Button(
            form, text='Browse',
            command=self.upload_csv,
            bootstyle='success-outline',
        )
        button_upload.grid(row=2, column=2, sticky='w', padx=5, pady=10)

        # -----------------------------
        # Row 3: Number of Items to Run
        # -----------------------------
        label_num_items = ttk.Label(
            form, text='Number of items to run (0 for all):',
            font=('Helvetica', 12),
        )
        label_num_items.grid(row=3, column=0, sticky='e', padx=5, pady=10)

        self.num_items_var = ttk.IntVar(value=0)
        entry_num_items = ttk.Entry(
            form, textvariable=self.num_items_var, width=10,
        )
        entry_num_items.grid(
            row=3, column=1, sticky='w',
            padx=5, pady=10, columnspan=2,
        )

        # -----------------------------
        # Row 4: Visible Mode Toggle
        # -----------------------------
        label_visible_mode = ttk.Label(
            form, text='Visible Mode:', font=('Helvetica', 12),
        )
        label_visible_mode.grid(row=4, column=0, sticky='e', padx=5, pady=10)

        self.visible_mode_var = ttk.BooleanVar(value=False)
        switch_visible_mode = ttk.Checkbutton(
            form,
            text='',
            variable=self.visible_mode_var,
            bootstyle='success-round-toggle',
        )
        switch_visible_mode.grid(
            row=4, column=1, sticky='w', padx=5, pady=10, columnspan=2,
        )

        # -----------------------------
        # Row 5: Email Template Field
        # -----------------------------
        label_email_template = ttk.Label(
            form, text='Email Template:', font=('Helvetica', 12),
        )
        label_email_template.grid(
            row=5, column=0, sticky='ne', padx=5, pady=10,
        )

        self.email_template_text = ScrolledText(
            form, wrap='word', width=50, height=10, font=('Helvetica', 12),
        )
        self.email_template_text.grid(
            row=5, column=1, sticky='nsew', padx=5, pady=10, columnspan=2,
        )
        form.rowconfigure(5, weight=1)  # Allow row 5 to expand vertically

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
                        "CSV must contain 'Person Linkedin Url' and 'Email' columns.",  # noqa: E501
                    )
            except Exception as e:
                messagebox.showerror('Error', f"Failed to read CSV: {e}")

    def start_process(self):
        if self.csv_data is None:
            messagebox.showwarning(
                'No CSV File', 'Please upload a CSV file before starting.',
            )
            return

        linkedin_email = self.linkedin_email_var.get().strip()
        linkedin_password = self.linkedin_password_var.get().strip()
        num_items = self.num_items_var.get()
        visible_mode = self.visible_mode_var.get()
        email_template = self.email_template_text.get('1.0', 'end').strip()

        if not linkedin_email or not linkedin_password:
            messagebox.showwarning(
                'Credentials Missing',
                'Please enter your LinkedIn email and password.',
            )
            return

        if not email_template:
            messagebox.showwarning(
                'No Email Template',
                'Please enter an email template before starting.',
            )
            return

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
                linkedin_email, linkedin_password,
                data_to_process, visible_mode, email_template,
            ),
            daemon=True,
        ).start()

    def run_selenium_thread(
        self,
        linkedin_email,
        linkedin_password,
        data,
        visible_mode,
        email_template,
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
            linkedin_email=linkedin_email,
            linkedin_password=linkedin_password,
            data=data,
            visible_mode=visible_mode,
            email_template=email_template,
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
