import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

import pandas as pd
A = 'test'


class LinkedInAutomationApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Configure main window properties
        self.title('LinkedIn Automation Tool')
        self.geometry('900x500')

        # Initialize UI elements
        self.create_widgets()

    def create_widgets(self):
        # Title Label
        label_title = tk.Label(
            self, text='LinkedIn Automation Tool', font=('Arial', 16),
        )
        label_title.pack(pady=10)

        # Upload CSV Button
        button_upload = tk.Button(
            self, text='Upload CSV', command=self.upload_csv,
        )
        button_upload.pack(pady=10)

        # Label to display selected file path
        self.label_file = tk.Label(self, text='No file selected', fg='gray')
        self.label_file.pack(pady=10)

    def upload_csv(self):
        # Open file dialog
        file_path = filedialog.askopenfilename(
            filetypes=[('CSV files', '*.csv')],
        )
        if file_path:
            # Update label with file path
            self.label_file.config(text=file_path)
            try:
                # Load and validate the CSV
                data = pd.read_csv(file_path)
                if 'LinkedIn URL' in data.columns and 'Email' in data.columns:
                    messagebox.showinfo('Success', 'CSV file is valid.')
                else:
                    messagebox.showwarning(
                        'Validation Error',
                        "CSV must contain 'LinkedIn URL' and 'Email' columns.",
                    )
            except Exception as e:
                messagebox.showerror('Error', f"Failed to read CSV: {e}")
