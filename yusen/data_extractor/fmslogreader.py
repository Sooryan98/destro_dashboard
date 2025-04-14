import re

# Read your second log file
with open("/home/soorya/destro_python/yunsen/logs/FMS_2025-04-10.log", "r") as f:
    lines = f.readlines()

# Regex pattern
pattern = r"CODE (?P<code>\w+) at (?P<time>[\d.]+) number of cases finished is (?P<cases_finished>\d+)"

# Output lines
output_lines = []

for line in lines:
    match = re.search(pattern, line)
    if match:
        code = match.group("code")
        time = match.group("time")
        cases_finished = match.group("cases_finished")
        output_lines.append(f"{code}\t{time}\t{cases_finished}")

# Write to TXT file
with open("cases_finished_log.txt", "w") as f:
    f.write("Code\tTime\tCasesFinished\n")  # Header
    for line in output_lines:
        f.write(line + "\n")

print("Extracted data written to cases_finished_log.txt")
