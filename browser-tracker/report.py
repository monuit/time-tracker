import sys
import os
import subprocess
import re
import time
from datetime import datetime, date, timedelta
import json

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def process_intervals(time_intervals):
	'''
	Closes open intervals and converts strings to datetime objects
	Returns sum of the intervals
	'''
	total_time = ZERO_TIME
	for interval in time_intervals:
		for i, time_str in enumerate(interval):
			if time_str is None:
				interval[i] = CUR_TIME
			elif isinstance(time_str, str):
				interval[i] = datetime.strptime(time_str, TIME_FORMAT)
		total_time += interval[1] - interval[0]
	return total_time

def process_paths_dict(paths_dict):
	max_entry_dict = None
	max_time_spent = ZERO_TIME
	for entry_dict, time_intervals in paths_dict.values():
		time_spent = process_intervals(time_intervals)
		if time_spent > max_time_spent:
			max_time_spent = time_spent
			max_entry_dict = entry_dict
	return max_entry_dict, max_time_spent

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
CUR_TIME = datetime.now().replace(microsecond=0)
ZERO_TIME = CUR_TIME - CUR_TIME

todays_folder = os.path.join('data', str(date.today()))
record_filename = os.path.join(todays_folder, 'record.json')

# record_filename = 'data/2019-11-11/record.json'

with open(record_filename) as f:
	domains_dict = json.load(f)

labels = []
times = []
interval_counts = []
for domain, (paths_dict, domain_time_intervals) in domains_dict.items():
	time_spent = process_intervals(domain_time_intervals)
	print('Spent {} on {}.'.format(time_spent, domain))
	max_entry_dict, max_time_spent = process_paths_dict(paths_dict)
	print('Most time, {}, spent on page title | {}.'
		  '\n'.format(max_time_spent, max_entry_dict['title']))
	labels.append(domain)
	times.append(time_spent.total_seconds())
	interval_counts.append(sum([len(intervals) for _, intervals 
								in paths_dict.values()]))

data = pd.DataFrame(list(zip(labels, times, interval_counts)),
					columns=['Site', 'Time', 'Visits'])

fig, ax = plt.subplots()
sns.barplot(
		x='Site', y='Visits', data=data.sort_values('Visits', ascending=False), ax=ax
	).set(title='Number of Pages Opened on Site (Includes Duplicates)', 
		  ylabel='Number of Pages')
plt.xticks(
    rotation=45, 
    horizontalalignment='right',
    # fontweight='light',
    fontsize=8  
)
fig.subplots_adjust(bottom=0.2)
plt.show()

# fig, ax = plt.subplots()
# sns.barplot(
# 		x='Site', y='Time', data=data.sort_values('Time', ascending=False), ax=ax
# 	).set(title='Time Spent', ylabel='Time (s)')
# plt.xticks(
#     rotation=45, 
#     horizontalalignment='right',
#     # fontweight='light',
#     fontsize=8  
# )
# fig.subplots_adjust(bottom=0.2)
# plt.show()