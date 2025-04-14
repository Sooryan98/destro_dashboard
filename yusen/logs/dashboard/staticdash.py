import streamlit as st
import pandas as pd
import altair as alt
import re
import os
from collections import defaultdict
from datetime import datetime
DESTRO_PATH = "yusen/logs/inputlog/yusen_2025-04-10.log"
FMS_PATH = "yusen/logs/inputlog/FMS_2025-04-10.log"

st.set_page_config(page_title="destro", layout="wide")

# ---------------- Data Structures ----------------
robot_destro_data = defaultdict(lambda: defaultdict(dict))
progress = defaultdict(int)
task_id_tracker=[]
log_data = {"total_cases": 0}
robot_fms_data = {f"Robot {i}": 0 for i in range(17)}
robot_total_cases={f"Robot {i}" : 0 for i in range(17)}
cases_per_hour = defaultdict(lambda: defaultdict(int))
log_time_format = "%Y-%m-%d %H:%M:%S,%f"
# ---------------- DESTRO Log Parser ----------------
def parse_destro_log(path):
    if not os.path.exists(path):
        return

    with open(path, "r") as file:
        for line in file:
            line = re.sub(r'\x1b\[[0-9;]*m', '', line)
            

            if "CODE 201" in line:
                timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)', line)
                if timestamp_match:
                        log_time_str = timestamp_match.group(1)
                        log_time = datetime.strptime(log_time_str, log_time_format)

                        # Round down to the hour
                        log_hour_str = log_time.strftime("%Y-%m-%d %H:00")
                pattern = re.compile(
                    r"CODE 201 \[Batch (\d+)] Robot (\d+) unloading case (\d+) of (\d+) for item (\d+)"
                )
                match = pattern.search(line)
                if match:
                 
                    batch, robot_id, case_num, total_cases, item_id = match.groups()
                    robot_key = f"Robot {robot_id}"
                    robot_destro_data[robot_key][item_id] = {
                        "batch": int(batch),
                        "case_num": int(case_num),
                        "total_cases": int(total_cases),
                    }
                    # if  item_id not in task_id_tracker:
                    #     task_id_tracker.append(item_id)
                    robot_total_cases[f'Robot {robot_id}'] +=1
                    cases_per_hour[robot_key][log_hour_str] += 1
                    

            elif "CODE 101" in line:
                pattern = re.compile(r"CODE 101 --------------- (\d+)")
                match = pattern.search(line)
                if match:
                    cases = match.groups()
                    log_data["total_cases"] = int(cases[0])

# ---------------- FMS Log Parser ----------------
def parse_fms_log(path):
    if not os.path.exists(path):
        return

    with open(path, "r") as file:
        for line in file:
            line = re.sub(r'\x1b\[[0-9;]*m', '', line)

            if "CODE F01" in line:
                pattern = re.compile(r"CODE F01 at (\d+\.\d+) number of cases finished is (\d+)")
                match = pattern.search(line)
                if match:
                    hour, cases = match.groups()
                    progress[hour] = int(cases)

            else:
                pattern = re.compile(r"Robot robot_(\d+)\s+has travelled\s+([\d\.]+)\s+m")
                match = pattern.search(line)
                if match:
                    robot_id, dist = match.groups()
                    if int(robot_id)<17:

                        robot_key = f"Robot {robot_id}"
                        robot_fms_data[robot_key] = float(dist)

# ---------------- Run Parsers ----------------
parse_destro_log(DESTRO_PATH)
parse_fms_log(FMS_PATH)

# ---------------- Prepare DataFrames ----------------
rows = []
for robot, items in robot_destro_data.items():
    for item_id, data in items.items():
        rows.append({
            "Robot": robot,
            "Item ID": item_id,
            "Batch": data["batch"],
            "Case Num": data["case_num"],
            "Total Cases": data["total_cases"]
        })

df = pd.DataFrame(rows)
# robot_cases_df = (
#     df.groupby("Robot")["Case Num"].max().reset_index().sort_values(by="Robot")
# )
cases_ph_df = pd.DataFrame(cases_per_hour).T.fillna(0).astype(int)

cases_ph_df= cases_ph_df.reindex(sorted(cases_ph_df.columns), axis=1)

cases_ph_df["Total cases overall"] = cases_ph_df.sum(axis=1)
robot_dist_df = pd.DataFrame(list(robot_fms_data.items()), columns=["Robot", "Distance"]).sort_values(by="Robot")
progress_df=pd.DataFrame(list(progress.items()), columns=["Hour", "Cases"])
robot_uph_df=pd.DataFrame(list(robot_total_cases.items()), columns=["Robot", "Total Cases"])
# ---------------- Display Dashboard ----------------
st.image("yusen/logs/destro_logo.png", width=400)
st.metric(label="Total Cases Picked", value=log_data['total_cases'])

# chart_cases = alt.Chart(robot_cases_df).mark_bar().encode(
#     x=alt.X('Robot:N', sort='ascending'),
#     y='Case Num:Q'
# ).properties(width=2000, height=400, title="Robot vs Cases Unloaded in this Trip")

chart_dist = alt.Chart(robot_dist_df).mark_bar().encode(
    x=alt.X('Robot:N', sort='ascending'),
    y='Distance:Q'
).properties(width=2000, height=400, title="Robot vs  Distance Travelled")
chart_botuph = alt.Chart(robot_uph_df).mark_bar().encode(
    x=alt.X('Robot:N', sort='ascending'),
    y='Total Cases:Q'
).properties(width=2000, height=400, title="Robot vs Total Cases")


# st.altair_chart(chart_cases, use_container_width=False)
st.altair_chart(chart_dist, use_container_width=False)
st.title("Robot Unloading Cases per Hour")
st.dataframe(cases_ph_df , use_container_width=True)
st.altair_chart(chart_botuph, use_container_width=False)

st.write("### Robot Unloading Status")
st.dataframe(df, use_container_width=True)
st.write("### Progress over time")
st.dataframe(progress_df, use_container_width=True)
