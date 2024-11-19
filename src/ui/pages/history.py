import sqlite3
from tkinter import BOTH
from tkinter import END
from tkinter import LEFT
from tkinter import RIGHT
from tkinter import Scrollbar
from tkinter import Text
from tkinter import Y

import ttkbootstrap as ttk

DB_PATH = 'run_history.db'


class HistoryPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()

    def create_widgets(self):
        # Title Label
        label_title = ttk.Label(self, text='Run History', font=('Arial', 16))
        label_title.pack(pady=10)

        # Frame for Runs and Emails Treeviews
        frame_trees = ttk.Frame(self)
        frame_trees.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Treeview to display runs
        columns = (
            'run_id', 'timestamp', 'file_name',
            'status', 'error_message',
        )
        self.tree_runs = ttk.Treeview(
            frame_trees, columns=columns, show='headings', height=10,
        )
        for col in columns:
            self.tree_runs.heading(col, text=col.replace('_', ' ').title())
            self.tree_runs.column(col, width=100, anchor='center')
        self.tree_runs.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))

        # Bind the selection event for runs
        self.tree_runs.bind('<<TreeviewSelect>>', self.on_run_selected)

        # Frame for Emails Treeview and Email Text
        frame_emails = ttk.Frame(frame_trees)
        frame_emails.pack(side=LEFT, fill=BOTH, expand=True)

        # Treeview to display emails for the selected run
        columns_emails = (
            'email_id',
            'run_id',
            'linkedin_profile_url',
            'email_text',
            'email_status',
            'error_message',
            'timestamp',
        )
        self.tree_emails = ttk.Treeview(
            frame_emails,
            columns=columns_emails,
            show='headings',
            height=10,
        )
        for col in columns_emails:
            self.tree_emails.heading(col, text=col.replace('_', ' ').title())
            # Set appropriate column widths
            if col == 'email_text':
                self.tree_emails.column(col, width=200, anchor='w')
            elif col == 'linkedin_profile_url':
                self.tree_emails.column(col, width=150, anchor='w')
            else:
                self.tree_emails.column(col, width=100, anchor='center')

        self.tree_emails.pack(fill=BOTH, expand=True, padx=(0, 5))

        # Bind the selection event for emails
        self.tree_emails.bind('<<TreeviewSelect>>', self.on_email_selected)

        # Text widget to display full email text
        frame_email_text = ttk.Frame(self)
        frame_email_text.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))

        label_email_text = ttk.Label(
            frame_email_text, text='Full Email Text:', font=('Arial', 12),
        )
        label_email_text.pack(anchor='w')

        self.text_email = Text(
            frame_email_text, wrap='word', height=10, state='disabled',
        )
        scrollbar = Scrollbar(frame_email_text, command=self.text_email.yview)
        self.text_email.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.text_email.pack(fill=BOTH, expand=True)

        self.load_runs()

    def load_runs(self):
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        select_query = 'SELECT * FROM runs ORDER BY timestamp DESC'
        cursor.execute(select_query)
        records = cursor.fetchall()

        # Clear existing data in the treeview
        for row in self.tree_runs.get_children():
            self.tree_runs.delete(row)

        # Insert new records into the treeview
        for record in records:
            self.tree_runs.insert('', END, values=record)

        connection.close()

    def on_run_selected(self, event):
        selected_item = self.tree_runs.selection()
        if selected_item:
            # Assuming run_id is the first column
            run_id = self.tree_runs.item(selected_item)['values'][0]
            self.load_emails_for_run(run_id)

    def load_emails_for_run(self, run_id):
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        select_query = 'SELECT * FROM emails WHERE run_id = ? ORDER BY timestamp DESC'  # noqa: E501
        cursor.execute(select_query, (run_id,))
        records = cursor.fetchall()

        # Clear existing data in the Treeview
        for row in self.tree_emails.get_children():
            self.tree_emails.delete(row)

        # Insert new records into the Treeview
        for record in records:
            self.tree_emails.insert('', 'end', values=record)

        connection.close()

        # Clear the email text display when a new run is selected
        self.clear_email_text()

    def on_email_selected(self, event):
        selected_item = self.tree_emails.selection()
        if selected_item:
            # Assuming email_text is the fourth column
            email_text = self.tree_emails.item(selected_item)['values'][3]
            self.display_full_email_text(email_text)

    def display_full_email_text(self, email_text):
        self.text_email.config(state='normal')
        self.text_email.delete(1.0, END)
        self.text_email.insert(END, email_text)
        self.text_email.config(state='disabled')

    def clear_email_text(self):
        self.text_email.config(state='normal')
        self.text_email.delete(1.0, END)
        self.text_email.config(state='disabled')
