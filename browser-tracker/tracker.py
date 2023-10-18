import sys
import os
import subprocess
import re
import time
from datetime import datetime, date
import json

import lz4.block
from glob import glob

class Tracker():
    def __init__(self):
        tilde_path = os.path.expanduser('~/')
        firefox_filename = glob(tilde_path+'/.mozilla/firefox/*default/'
                                'sessionstore-backups/recovery.json*')[0]
        assert os.path.exists(firefox_filename), ('Firefox file not found.'
            ' See README.md for more information.')
        self.firefox_filename = firefox_filename
        todays_folder = os.path.join('data', str(date.today()))
        if not os.path.exists(todays_folder):
            os.makedirs(todays_folder)
        self.data_filename = os.path.join(todays_folder, 'data.json')
        self.record_filename = os.path.join(todays_folder, 'record.json')
        self.time_format = '%Y-%m-%d %H:%M:%S'
        self.delay_time = 1

        # TODO: smart comparison of previous run
        # Currently overwriting or accepting data from previous run
        if not os.path.exists(self.data_filename):
            # domains_dict = self._get_cur_domains_dict()
            # self._save(self.data_filename, domains_dict)
            self._save(self.data_filename, {})
        if not os.path.exists(self.record_filename):
            self._save(self.record_filename, {})

    def _close_entry(self, old_entry_dict, cur_time):
        old_title = old_entry_dict['title']
        start_time_str = old_entry_dict['time']
        start_time = datetime.strptime(start_time_str, self.time_format)
        delta = str(cur_time - start_time)
        print('Page \"{}\" closed, was first opened at {}, opened' 
              ' for {}\n'.format(old_title, start_time_str, delta))

        record_domains_dict = self._get_saved(self.record_filename)
        domain = old_entry_dict['domain']
        path = old_entry_dict['path']
        record_paths_dict, domain_time_intervals = record_domains_dict[domain]

        record_entry_dict, path_time_intervals = record_paths_dict[path]
        assert path_time_intervals[-1][-1] is None, 'Closing closed path'
        path_time_intervals[-1][-1] = str(cur_time)

        if all(path_time_intervals[-1][-1] is not None for
                _, path_time_intervals in record_paths_dict.values()):
            # all domains paths are closed, therefore close the domain
            assert domain_time_intervals[-1][-1] is None, \
                    'Closing closed domain'
            domain_time_intervals[-1][-1] = str(cur_time)

        record_paths_dict[path] = (record_entry_dict, path_time_intervals)
        record_domains_dict[domain] = (record_paths_dict, 
                                       domain_time_intervals)
        self._save(self.record_filename, record_domains_dict)

    def _open_entry(self, new_entry_dict, cur_time):
        new_title = new_entry_dict['title']
        print('Page \"{}\" opened at {}\n'.format(new_title, cur_time))

        record_domains_dict = self._get_saved(self.record_filename)
        domain = new_entry_dict['domain']
        path = new_entry_dict['path']
        this_interval = [str(cur_time), None]
        if domain in record_domains_dict:
            (record_paths_dict, 
            domain_time_intervals) = record_domains_dict[domain]
            if domain_time_intervals[-1][-1] is not None:
                # domain seen but not open in tab
                domain_time_intervals.append(this_interval)
        else:
            record_paths_dict = {}
            domain_time_intervals = [this_interval]

        if path in record_paths_dict:
            (record_entry_dict, 
            path_time_intervals) = record_paths_dict[path]
            path_time_intervals.append(this_interval)
        else:
            record_entry_dict = new_entry_dict
            path_time_intervals = [this_interval]

        record_paths_dict[path] = (record_entry_dict, path_time_intervals)
        record_domains_dict[domain] = (record_paths_dict, 
                                       domain_time_intervals)
        self._save(self.record_filename, record_domains_dict)

    def _close_intervals(self):
        record_domains_dict = self._get_saved(self.record_filename)
        cur_time_str = str(datetime.now().replace(microsecond=0))
        for paths_dict, domain_time_intervals in record_domains_dict.values():
            if domain_time_intervals[-1][-1] is None:
                domain_time_intervals[-1][-1] = cur_time_str
            for _, path_time_intervals in paths_dict.values():
                if path_time_intervals[-1][-1] is None:
                    path_time_intervals[-1][-1] = cur_time_str
        self._save(self.record_filename, record_domains_dict)

    def _get_saved(self, filename):
        with open(filename) as f:
            D = json.load(f)
        return D

    def _save(self, filename, D):
        with open(filename, 'w') as f:
            json.dump(D, f)

    def _get_cur_domains_dict(self):
        with open(self.firefox_filename, 'rb') as f:
            f.read(8)
            firefox_data = json.loads(lz4.block.decompress(f.read()))
        cur_time = datetime.now().replace(microsecond=0)
        cur_time_str = str(cur_time)
        sites_dict = {}
        for window in firefox_data.get('windows'):
            for tab in window.get('tabs'):
                if 'index' not in tab:
                    # bug fix: some tab's entries are empty
                    continue
                page_dict = {}
                idx = int(tab.get('index')) - 1
                entry = tab.get('entries')[idx]
                page_dict = self._get_entry_dict(entry, cur_time_str)
                domain = page_dict['domain']
                path = page_dict['path']
                if domain in sites_dict:
                    sites_dict[domain][path] = page_dict
                else:
                    sites_dict[domain] = {path: page_dict}
        return sites_dict

    def _get_entry_dict(self, entry, cur_time_str):
        page_dict = {}
        page_dict['title'] = entry.get('title')
        page_dict['time'] = cur_time_str
        url = re.sub('www.', '' , re.sub('https*://', '', entry.get('url')))
        temp = re.split('/', url, 1)
        domain = temp[0]
        page_dict['domain'] = domain
        if len(temp) == 1 or temp[1] == '':
            page_dict['path'] = ''
        else:
            page_dict['path'] = '/' + temp[1]
        return page_dict

    def update(self):
        old_domains_dict = self._get_saved(self.data_filename)
        new_domains_dict = self._get_cur_domains_dict()
        updated_domains_dict = {}
        cur_time = datetime.now().replace(microsecond=0)
        # check if old tabs are closed, add to updated_ if not
        for old_domain, old_paths_dict in old_domains_dict.items():
            # domain closed
            if old_domain not in new_domains_dict:
                print('Domain \"{}\" closed.'.format(old_domain))
                for old_path, old_entry_dict in old_paths_dict.items():
                    self._close_entry(old_entry_dict, cur_time)
            else:
                updated_paths_dict = {}
                new_paths_dict = new_domains_dict[old_domain]
                for old_path, old_entry_dict in old_paths_dict.items():
                    if old_path not in new_paths_dict:
                        self._close_entry(old_entry_dict, cur_time)
                    else:
                        updated_paths_dict[old_path] = old_entry_dict
                updated_domains_dict[old_domain] = updated_paths_dict

        # check if new paths are opened
        for new_domain, new_paths_dict in new_domains_dict.items():
            if new_domain not in old_domains_dict:
                print('Domain \"{}\" opened.'.format(new_domain))
                updated_domains_dict[new_domain] = new_paths_dict
                for new_path, new_entry_dict in new_paths_dict.items():
                    self._open_entry(new_entry_dict, cur_time)
            else:
                if new_domain in updated_domains_dict:
                    updated_paths_dict = updated_domains_dict[new_domain]
                else:
                    updated_paths_dict = {}
                old_paths_dict = old_domains_dict[new_domain]
                for new_path, new_entry_dict in new_paths_dict.items():
                    if new_path not in old_paths_dict:
                        self._open_entry(new_entry_dict, cur_time)
                        updated_paths_dict[new_path] = new_entry_dict
                updated_domains_dict[new_domain] = updated_paths_dict

        self._save(self.data_filename, updated_domains_dict)

    def run(self):
        try:
            while True:
                if not os.path.exists(self.firefox_filename):
                    count += 1
                    if count > 2:
                        sys.exit('Firefox file not found for more than {} '
                                 'seconds.'.format(2*self.delay_time))
                else:
                    count = 0
                    agent.update()
                time.sleep(self.delay_time)

        except KeyboardInterrupt:
            # close all tab intervals
            self._close_intervals()
            print('\nUser ended run.')

agent = Tracker()
agent.run()



# with open('delete.json', 'w') as f:
#     json.dump(agent.serialize(), f)



# from selenium import webdriver
# driver = webdriver.Firefox()