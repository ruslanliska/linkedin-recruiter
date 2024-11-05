# history_page.py
import ttkbootstrap as ttk


class HistoryPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()

    def create_widgets(self):
        label_content = ttk.Label(
            self, text='This is the history page.',
        )
        label_content.pack(pady=10)
