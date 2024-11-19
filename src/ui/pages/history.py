import sqlite3

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

DB_PATH = 'run_history.db'


class HistoryPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.load_history()

    def create_widgets(self):
        # Title Label
        label_title = ttk.Label(self, text='Run History', font=('Arial', 16))
        label_title.pack(pady=10)

        # Treeview to display history
        self.tree = ttk.Treeview(
            self, columns=(
                'id', 'timestamp', 'file_name', 'status', 'error_message',
            ), show='headings',
        )
        self.tree.heading('id', text='ID')
        self.tree.heading('timestamp', text='Timestamp')
        self.tree.heading('file_name', text='File Name')
        self.tree.heading('status', text='Status')
        self.tree.heading('error_message', text='Error Message')

        self.tree.column('id', width=50)
        self.tree.column('timestamp', width=150)
        self.tree.column('file_name', width=200)
        self.tree.column('status', width=100)
        self.tree.column('error_message', width=300)

        self.tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

    def load_history(self):
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        select_query = 'SELECT * FROM run_history ORDER BY timestamp DESC'
        cursor.execute(select_query)
        records = cursor.fetchall()

        # Clear existing data in the treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Insert new records into the treeview
        for record in records:
            self.tree.insert('', END, values=record)

        connection.close()
