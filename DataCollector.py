import csv

import os
class DataCollector:
    def __init__(self):
        self.fieldnames = ['key_count', 'avg_gap', 'variance', 'label']
        desktop = os.path.join(os.path.expanduser("~"), "Desktop", "output.csv")
        self.filepath = desktop
        if not os.path.exists('output.csv'):
            with open('output.csv', 'a', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()

    def save(self, key_count, avg_gap, variance, label=0):
        if key_count == 0:
            return
        with open('output.csv', 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            writer.writerow({
                'key_count': key_count,
                'avg_gap': avg_gap,
                'variance': variance,
                'label': label
            })