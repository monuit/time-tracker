import pandas as pd
import pygetwindow as gw
import time
from datetime import datetime

class WindowTracker:
    def __init__(self):
        self.df = pd.DataFrame(columns=['Timestamp', 'Application', 'Window_Title'])
        self.df.to_parquet('window_data.parquet', engine='pyarrow')

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
        elif "Jira" in title:
            return "Jira"
        elif "Confluence" in title:
            return "Confluence"
        else:
            return "Other"

    def update_data(self, timestamp, app, title):
        new_row = {'Timestamp': timestamp, 'Application': app, 'Window_Title': title}
        self.df = pd.read_parquet('window_data.parquet', engine='pyarrow')
        self.df = self.df.append(new_row, ignore_index=True)
        self.df.to_parquet('window_data.parquet', engine='pyarrow')

    def run(self):
        while True:
            timestamp, app, title = self.capture_window_title()
            if timestamp:
                print(f"Captured {app} at {timestamp}")
                self.update_data(timestamp, app, title)
            time.sleep(5)

if __name__ == '__main__':
    tracker = WindowTracker()
    tracker.run()
