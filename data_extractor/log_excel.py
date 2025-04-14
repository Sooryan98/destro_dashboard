import pandas as pd
import re

# Read your log file
with open("/home/soorya/destro_core/Destro_Yusen/cross-docking/logs/yusen_2025-04-10.log", "r") as f:
    lines = f.readlines()

# Regex pattern to extract info
pattern = r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - INFO - CODE \d+ \[Batch (?P<batch>\d+)] Robot (?P<robot_id>\d+) unloading case (?P<case_no>\d+) of (?P<total_cases>\d+) for item (?P<item_id>\d+)\."

# Extracted data
data = []

for line in lines:
    match = re.match(pattern, line)
    if match:
        data.append(match.groupdict())

# Convert to DataFrame
df = pd.DataFrame(data)

# Save to Excel
df.to_excel("parsed_log.xlsx", index=False)

print("Log written to parsed_log.xlsx")
