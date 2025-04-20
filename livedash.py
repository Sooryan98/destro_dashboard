import streamlit as st
import time
import pandas as pd
import natsort
import altair as alt 
from collections import defaultdict
from logreader import log_data, robot_destro_data,lock, start_destro_thread,start_fms_thread,robot_fms_data,progress,log_data,cases_per_hour,robot_total_cases, progress_track,uph_tracker
from logreader import flag_event
from datetime import datetime
DESTRO_PATH = "/home/soorya/destro_yusen/cross-docking/logs/yusen_2025-04-20.log"
FMS_PATH="/home/soorya/destro_python/yunsen/logs/FMS_2025-04-20.log"
st.set_page_config(page_title="destro", layout="wide")

start_destro_thread(DESTRO_PATH)
start_fms_thread(FMS_PATH)


# st.title("destro - Yusen sim")

placeholder = st.empty()
data=[]
uph=0
robot_cases={}
robot_dist={}
total_cases=0
total_run_time=0
uph=0
start_time=0
ctime=0
flag_begin=False
current_time=0
for i in range (0,16):
    robot_cases[f"Robot{i+1}"]=0
    robot_dist[f"Robot{i+1}"] =0
def clock_formating(current_time):
    hrs = current_time // 3600
    mins = (current_time % 3600) // 60
    sec = current_time % 60
    return f"{int(hrs)} : {int(mins)} : {int(sec)}"

while True:
    with lock:
        # print(robot_destro_data)
        

        rows = []
        for robot, items in robot_destro_data.items():
            for item_id, data in items.items():
                if int(data["case_num"])>0:
                    robot_cases[robot]= int(data["case_num"])
                rows.append({
                    "Robot": robot,
                    "Item ID": item_id,
                    "Batch": data["batch"],
                    "Case Num": data["case_num"],
                    "Total Cases": data["total_cases"],
                })
        # total_cases=sum(robot_cases.values())
        if flag_event.is_set():
            if not flag_begin:

                start_time=time.time()
                flag_begin=True
                print("FMS HAS BEEN STARTED")
            
            
            current_time=time.time()-start_time
            ctime=clock_formating(current_time)
        
            uph=int(log_data['total_cases'])/(current_time/3600)
        else:
            uph=0
            current_time=0
        if not rows:
            df = pd.DataFrame(columns=["Robot", "Item ID", "Batch", "Case Number", "Total Cases"])
        else:
            df = pd.DataFrame(rows)
# -------------cases -------------------
        robot_cases_df = pd.DataFrame(list(robot_cases.items()), columns=["Robot", "Case Number"])
        # robot_cases_df["Robot"] = robot_cases_df["Robot"].astype(str)
        # robot_cases_df=robot_cases_df.sort_values(by="Robot",ascending=True)
        # robot_cases_df = robot_cases_df.loc[natsort.index_natsorted(robot_cases_df["Robot"])]
        # robot_cases_df["Robot_Num"] = robot_cases_df["Robot"].str.extract('(\d+)').astype(int)
# 
# Sort by the extracted number
        # robot_cases_df = robot_cases_df.sort_values(by="Robot_Num").drop(columns="Robot_Num")
       

# -------------=dist-----------------------
        for robot,dist in robot_fms_data.items():
            robot_dist[robot] = dist
        robot_dist_df = pd.DataFrame(list(robot_dist.items()), columns=["Robot", "Distance"])
        # robot_dist_df=robot_dist_df.sort_values(by="Robot",ascending=True)
        robot_dist_df["Robot_Num"] = robot_dist_df["Robot"].str.extract(r'(\d+)').astype(int)
        robot_dist_df = robot_dist_df.sort_values(by="Robot_Num")






        cases_ph_df = pd.DataFrame(cases_per_hour).T.fillna(0).astype(int)

        cases_ph_df= cases_ph_df.reindex(sorted(cases_ph_df.columns), axis=1)

        cases_ph_df["Total cases overall"] = cases_ph_df.sum(axis=1)
        progress_df=pd.DataFrame(list(progress.items()), columns=["Hour", "Cases"])
        uph_tracker_df=pd.DataFrame(list(uph_tracker.items()), columns=["Hour", "UPH"])
        robot_uph_df=pd.DataFrame(list(robot_total_cases.items()), columns=["Robot", "Total Cases"])
        robot_uph_df["Robot_Num"] = robot_uph_df["Robot"].str.extract(r'(\d+)').astype(int)
        robot_uph_df = robot_uph_df.sort_values(by="Robot_Num")

        # df=pd.DataFrame(rows)
    with placeholder.container():
        # print(progress)
       
        st.image("/home/soorya/destro_dashboard/destro_dashboard/destro_logo.jpg", width=400)
        st.metric(label="Time", value=ctime)
        st.metric(label="Total Cases Picked ", value=log_data['total_cases'])
        st.metric(label="UPH", value=uph)


        # chart_cases = alt.Chart(robot_cases_df).mark_bar().encode(
        #     x=alt.X('Robot:N', sort='ascending'),  # Ensure robots are in ascending order
        #     y='Case Number:Q'
        # ).properties(width=2000,height=400,
        #     title="Robot vs Total Cases"
        # )
        chart_dist = alt.Chart(robot_dist_df).mark_bar().encode(
            x=alt.X('Robot:N',sort=robot_dist_df["Robot"].tolist()),  # Ensure robots are in ascending order
            y='Distance:Q'
        ).properties(width=2000,height=400,
            title="Robot vs Distance [m]")
        
        chart_botuph = alt.Chart(robot_uph_df).mark_bar().encode(
            x=alt.X('Robot:N', sort=robot_uph_df["Robot"].tolist()),
            y='Total Cases:Q'
        ).properties(width=2000, height=400, title="Robot vs Total Cases")


        st.altair_chart(chart_dist, use_container_width=False)
        st.title("Robot Unloading Cases per Hour")
        st.dataframe(cases_ph_df , use_container_width=True)
        st.altair_chart(chart_botuph, use_container_width=False)

        st.write("### Robot Unloading Status")
        st.dataframe(df, use_container_width=True)
        st.write("### Progress per hour")
        st.dataframe(progress_df, use_container_width=True)

        st.write("### UPH breakdown")
        st.dataframe(uph_tracker_df, use_container_width=True)


    time.sleep(0.1)
