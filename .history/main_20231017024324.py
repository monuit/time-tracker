import pandas as pd
import pygetwindow as gw
import time
import yaml
from datetime import datetime
from pynput import keyboard, mouse

class WindowTracker:
    def __init__(self):
        self.df = pd.DataFrame(columns=['Timestamp', 'Application', 'Window_Title', 'Time_Spent', 'Key_Strokes', 'Mouse_Clicks'])
        self.load_config()
        self.prev_time = datetime.now()
        self.key_count = 0
        self.mouse_clicks = 0

    def load_config(self):
        with open("config.yaml", 'r') as stream:
            self.config = yaml.safe_load(stream)
        self.save_data = self.config['save_data']

    def on_key_press(self, key):
        self.key_count += 1

    def on_click(self, x, y, button, pressed):
        if pressed:
            self.mouse_clicks += 1

    def capture_window_title(self):
        window = gw.getActiveWindow()
        current_time = datetime.now()
        time_spent = (current_time - self.prev_time).seconds
        self.prev_time = current_time

        if window:
            title = window.title
            app = self.identify_application(title)
            return current_time, app, title, time_spent, self.key_count, self.mouse_clicks
        return None, None, None, None, None, None

    def identify_application(self, title):
        if "Outlook" in title:
            return "Outlook"
        elif "Teams" in title:
            return "Teams"
        elif self.browser in title:
            if "Jira" in title:
                return "Jira"
            elif "Confluence" in title:
                return "Confluence"
        else:
            return "Other"

    def update_data(self, timestamp, app, title, time_spent, key_strokes, mouse_clicks):
        new_row = pd.DataFrame([[timestamp, app, title, time_spent, key_strokes, mouse_clicks]], columns=self.df.columns)
        self.df = pd.concat([self.df, new_row]).reset_index(drop=True)

    def save_to_parquet(self):
        if self.save_data:
            filename = f"{datetime.now().strftime('%Y-%m-%d')}-window_data.parquet"
            self.df.to_parquet(filename, engine='pyarrow')
            print(f"Saved data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def run(self):
        print(f"Tracking started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        next_save = time.time() + 15  # 15 minutes in seconds

        with keyboard.Listener(on_press=self.on_key_press) as kl, mouse.Listener(on_click=self.on_click) as ml:
            while True:
                timestamp, app, title, time_spent, key_strokes, mouse_clicks = self.capture_window_title()
                if timestamp:
                    self.update_data(timestamp, app, title, time_spent, key_strokes, mouse_clicks)
                
                if time.time() >= next_save:
                    self.save_to_parquet()
                    next_save = time.time() + 15

if __name__ == '__main__':
    tracker = WindowTracker()
    tracker.run()
