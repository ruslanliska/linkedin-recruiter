import os
import sys
# Add the parent directory to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from src.ui.main_window import LinkedInAutomationApp



if __name__ == '__main__':

    app = LinkedInAutomationApp()
    app.mainloop()
