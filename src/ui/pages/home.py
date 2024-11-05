# main_page.py
from tkinter import filedialog
from tkinter import messagebox

import pandas as pd
import ttkbootstrap as ttk


class HomePage(ttk.Frame):
    def __init__(self, parent, upload_callback):
        super().__init__(parent)
        self.upload_callback = upload_callback
        self.create_widgets()

    def create_widgets(self):
        # Upload CSV Button
        button_upload = ttk.Button(
            self, text='Upload CSV',
            command=self.upload_csv,
            bootstyle='success',
        )
        button_upload.pack(pady=10)

        # Label to display selected file path
        self.label_file = ttk.Label(
            self, text='No file selected', foreground='gray',
        )
        self.label_file.pack(pady=10)

    def upload_csv(self):
        file_path = filedialog.askopenfilename(
            filetypes=[('CSV files', '*.csv')],
        )
        if file_path:
            self.label_file.config(text=file_path)
            try:
                data = pd.read_csv(file_path)
                if 'LinkedIn URL' in data.columns and 'Email' in data.columns:
                    messagebox.showinfo('Success', 'CSV file is valid.')
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
