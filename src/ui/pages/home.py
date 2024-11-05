from tkinter import filedialog
from tkinter import messagebox

import pandas as pd
import ttkbootstrap as ttk


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
        # Label for CSV File
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

        self.visible_mode_var = ttk.BooleanVar(value=False)
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
        # Start Button at the Bottom
        # -----------------------------
        button_start = ttk.Button(
            form_frame, text='Start Process',
            command=self.start_process,
            bootstyle='primary',
        )
        button_start.pack(pady=20)

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
                        "CSV must contain 'LinkedIn URL' and 'Email' columns.",
                    )
            except Exception as e:
                messagebox.showerror('Error', f"Failed to read CSV: {e}")

    def start_process(self):
        if self.csv_data is None:
            messagebox.showwarning(
                'No CSV File', 'Please upload a CSV file before starting.',
            )
            return

        num_items = self.num_items_var.get()
        visible_mode = self.visible_mode_var.get()

        # Process the data based on user inputs
        if num_items == 0 or num_items > len(self.csv_data):
            num_items = len(self.csv_data)

        data_to_process = self.csv_data.head(num_items)

        # Here you can start your processing logic
        # For example, pass data_to_process and
        # visible_mode to your automation script

        messagebox.showinfo(
            'Process Started', f'Started processing {num_items} items in {
                'visible' if visible_mode else 'invisible'
            } mode.',
        )
