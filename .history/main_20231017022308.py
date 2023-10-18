import pandas as pd
import pygetwindow as gw
import time
import yaml
from datetime import datetime

class WindowTracker:
    def __init__(self):
        self.df = pd.DataFrame(columns=['Timestamp', 'Application', 'Window_Title'])
        self.load_config()

    def load_config(self):
        with open("config.yaml", 'r') as stream:
            self.config = yaml.safe_load(stream)
        self.browser = self.config['browser']

    def capture_window_title(self):
        window = gw.getActiveWindow()
        if window != None:
            title = window.title
            app = self.identify_application(title)
            timestamp = datetime.now()
            return timestamp, app, title
        return None, None, None

    def identify_application(self, title):
        if "Outlook" in title:
            return "Outlook"
        elif "Teams" in title:
            return "Teams"
        elif "Jira" in title and self.browser in title:
            return "Jira"
        elif "Confluence" in title and self.browser in title:
            return "Confluence"
        else:
            return "Other"

    def update_data(self, timestamp, app, title):
        new_row = pd.DataFrame([[timestamp, app, title]], columns=self.df.columns)
        self.df = pd.concat([self.df, new_row]).reset_index(drop=True)

    def save_to_parquet(self):
        filename = f"{datetime.now().strftime('%Y-%m-%d')}-window_data.parquet"
        self.df.to_parquet(filename, engine='pyarrow')
        print(f"Saved data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def run(self):
        print(f"Tracking started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        next_save = time.time() + 900  # 15 minutes in seconds

        try:
            while True:
                timestamp, app, title = self.capture_window_title()
                if timestamp:
                    self.update_data(timestamp, app, title)
                
                if time.time() >= next_save:
                    self.save_to_parquet()
                    next_save = time.time() + 900

        except KeyboardInterrupt:
            print(f"Tracking stopped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    tracker = WindowTracker()
    tracker.run()
