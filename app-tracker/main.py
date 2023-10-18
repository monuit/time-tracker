import psutil
import pandas as pd
import time
from datetime import datetime

class ApplicationTracker:
    def __init__(self):
        self.df = pd.DataFrame(columns=['Timestamp', 'Application', 'Time_Spent'])
        self.prev_time = datetime.now()

    def get_running_applications(self):
        app_list = []
        for process in psutil.process_iter(attrs=['name']):
            app_list.append(process.info['name'])
        return list(set(app_list))

    def update_data(self, timestamp, apps):
        for app in apps:
            new_row = pd.DataFrame([[timestamp, app, 1]], columns=self.df.columns)
            self.df = pd.concat([self.df, new_row]).reset_index(drop=True)

    def save_to_parquet(self):
        filename = f"{datetime.now().strftime('%Y-%m-%d')}-app_data.parquet"
        self.df.to_parquet(filename, engine='pyarrow')
        print(f"Saved data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def run(self):
        print(f"Tracking started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        next_save = time.time() + 15  # 15 minutes in seconds

        try:
            while True:
                timestamp = datetime.now()
                running_apps = self.get_running_applications()
                self.update_data(timestamp, running_apps)

                if time.time() >= next_save:
                    self.save_to_parquet()
                    next_save = time.time() + 15

        except KeyboardInterrupt:
            print(f"Tracking stopped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    tracker = ApplicationTracker()
    tracker.run()
