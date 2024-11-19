# src/ui/main_window.py
import logging
from tkinter import messagebox

import ttkbootstrap as ttk
from PIL import Image
from PIL import ImageTk

from src.ui.pages.history import HistoryPage
from src.ui.pages.home import HomePage

# Configure logging (ensure this is at the top of your script)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler('application.log'),  # Log to a file
    ],
)


class LinkedInAutomationApp(ttk.Window):
    def __init__(self):
        super().__init__(themename='superhero')  # Choose a theme
        self.title('InMail Automation')
        self.geometry('900x600')

        self.load_images()
        self.create_styles()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.create_left_menu()
        self.create_pages()

        # Override the window close protocol
        self.protocol('WM_DELETE_WINDOW', self.on_close)

    def load_images(self):
        try:
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
        except Exception as e:
            logging.error(f"Error loading images: {e}")
            # Use default images or handle the error as needed
            self.main_icon = None
            self.history_icon = None

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
            text=' Home',
            command=lambda: self.show_page('main'),
            image=self.main_icon,
            compound='left',
            bootstyle='secondary',
            style='Custom.TButton',
        )
        button_main.pack(pady=(5, 2), fill='x', padx=10)

        button_history = ttk.Button(
            self.menu_frame,
            text=' History',
            command=lambda: self.show_page('history'),
            image=self.history_icon,
            compound='left',
            bootstyle='secondary',
            style='Custom.TButton',
        )
        button_history.pack(pady=(2, 5), fill='x', padx=10)

    def create_pages(self):
        self.pages = {}

        self.page_container = ttk.Frame(self)
        self.page_container.grid(row=0, column=1, sticky='nsew')
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        # Instantiate pages and store them in self.pages
        main_page = HomePage(
            self.page_container,
            upload_callback=self.on_upload,
        )
        self.pages['main'] = main_page
        main_page.grid(row=0, column=0, sticky='nsew')

        history_page = HistoryPage(self.page_container)
        self.pages['history'] = history_page
        history_page.grid(row=0, column=0, sticky='nsew')

        self.show_page('main')

    def show_page(self, page_name):
        page = self.pages[page_name]
        page.tkraise()

    def on_upload(self, data, run_id):
        # Handle the uploaded data if needed
        pass

    def on_close(self):
        """
        Handles the window close event.
        Signals the automation thread to stop and waits for it to terminate.
        """
        if messagebox.askokcancel(
            'Quit',
            'Do you want to quit the application?',
        ):
            logging.info(
                'Quit signal received. Attempting to stop automation.',
            )

            # Wait for the automation thread to finish

            self.destroy()
