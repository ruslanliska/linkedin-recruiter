from tkinter import filedialog
from tkinter import messagebox

import pandas as pd
import ttkbootstrap as ttk
from PIL import Image
from PIL import ImageTk


class LinkedInAutomationApp(ttk.Window):
    def __init__(self):
        super().__init__(themename='superhero')  # Choose a theme
        self.title('InMail Automation')
        self.geometry('900x500')

        # self.style is provided by ttk.Window; no need to assign it
        # self.style = ttk.Style()

        self.load_images()
        self.create_styles()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.create_left_menu()
        self.create_pages()

    def load_images(self):
        self.main_icon = ImageTk.PhotoImage(
            Image.open('src/ui/static/home.png').resize(
                (16, 16),
                Image.LANCZOS,
            ),
        )
        self.history_icon = ImageTk.PhotoImage(
            Image.open('src/ui/static/history.png').resize(
                (16, 16),
                Image.LANCZOS,
            ),
        )

    def create_styles(self):
        # Use a style name that doesn't include 'Menu' to avoid conflicts
        self.style.configure(
            'Custom.TButton',
            font=('Arial', 12),
            anchor='w',  # Left-align the content
            padding=(10, 5),  # Adjust padding
        )
        self.style.map(
            'Custom.TButton',
            foreground=[('active', 'white')],
            background=[('active', '#1abc9c')],
        )

    def create_left_menu(self):
        self.menu_frame = ttk.Frame(self, width=200, bootstyle='dark')
        self.menu_frame.grid(row=0, column=0, sticky='ns')
        self.menu_frame.grid_propagate(False)

        button_main = ttk.Button(
            self.menu_frame,
            text=' Main Page',
            command=lambda: self.show_page('main'),
            image=self.main_icon,
            compound='left',
            bootstyle='secondary',
            style='Custom.TButton',  # Updated style name
        )
        button_main.pack(pady=(5, 2), fill='x', padx=10)

        button_history = ttk.Button(
            self.menu_frame,
            text=' History',
            command=lambda: self.show_page('history'),
            image=self.history_icon,
            compound='left',
            bootstyle='secondary',
            style='Custom.TButton',  # Updated style name
        )
        button_history.pack(pady=(2, 5), fill='x', padx=10)

    def create_pages(self):
        self.pages = {}

        self.page_container = ttk.Frame(self)
        self.page_container.grid(row=0, column=1, sticky='nsew')
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        main_page = ttk.Frame(self.page_container)
        self.pages['main'] = main_page
        self.create_main_widgets(main_page)

        history_page = ttk.Frame(self.page_container)
        self.pages['history'] = history_page
        self.create_history_widgets(history_page)

        self.show_page('main')

    def show_page(self, page_name):
        page = self.pages[page_name]
        page.tkraise()

    def create_main_widgets(self, frame):
        frame.grid(row=0, column=0, sticky='nsew')

        # Removed the title label

        # Upload CSV Button
        button_upload = ttk.Button(
            frame, text='Upload CSV',
            command=self.upload_csv,
            bootstyle='success',
        )
        button_upload.pack(pady=10)

        self.label_file = ttk.Label(
            frame, text='No file selected', foreground='gray',
        )
        self.label_file.pack(pady=10)

    def create_history_widgets(self, frame):
        frame.grid(row=0, column=0, sticky='nsew')

        # Removed the title label

        label_content = ttk.Label(
            frame, text='This is the history page.',
        )
        label_content.pack(pady=10)

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
                else:
                    messagebox.showwarning(
                        'Validation Error',
                        "CSV must contain 'LinkedIn URL' and 'Email' columns.",
                    )
            except Exception as e:
                messagebox.showerror('Error', f"Failed to read CSV: {e}")
