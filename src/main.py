import os
import sys

from src.ui.main_window import LinkedInAutomationApp

# Add the parent directory to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


if __name__ == '__main__':

    app = LinkedInAutomationApp()
    app.mainloop()
