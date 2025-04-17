
import os
import time
import threading
from threading import Event 
import re
from collections import defaultdict
from datetime import datetime
robot_destro_data = defaultdict(lambda: defaultdict(list))
progress= defaultdict(int)
progress_track={"0.0":0}

log_data={}
log_data['total_cases']=0
robot_fms_data={}
for i in range (0,40):
    robot_fms_data[f"Robot{i+1}"]=0
start_clock=0

flag=False
lock = threading.Lock()
flag_event= Event()
robot_fms_data = {f"Robot{i+1}": 0 for i in range(40)}
robot_total_cases={f"Robot{i+1}" : 0 for i in range(40)}
cases_per_hour = defaultdict(lambda: defaultdict(int))
log_time_format = "%Y-%m-%d %H:%M:%S,%f"
def read_fms_log(fms_log):
    if not os.path.exists(fms_log):
        open(fms_log, 'w').close()


    with open(fms_log, "r") as file:
        file.seek(0, 2)  # Seek to end

        while True:
            line = file.readline()

            if not line:
                time.sleep(0.2)
                continue

            line = re.sub(r'\x1b\[[0-9;]*m', '', line)  # Remove ANSI

            with lock:
                if "CODE 301" in line :
                    pattern = re.compile(
                            r"CODE F01 at (\d+\.\d+) number of cases finished is (\d+)"
)
                    match = pattern.search(line)
                    if match:
                        hour, cases = match.groups()
                        cases_until_now= sum(progress_track.values())
                        progress_track[hour]=int(cases)   
                        
                        progress_track[hour]=progress_track[hour]-cases_until_now
                        progress[hour]=progress_track[hour]
                        
                        
                    

                elif "CODE 000" in line :
                    print("FMS CAN START NOW")
                    flag_event.set()

                else:
                    pattern = re.compile(r"Robot robot_(\d+)\s+has travelled\s+([\d\.]+)\s+m")


                    match = pattern.search(line)
                    if match:
                        robot_id, dist = match.groups()
                        if int(robot_id)<40:
                            robot_key = f"Robot{int(robot_id)+1}"
                            robot_fms_data[robot_key]= float(dist)
                        
                    


def read_destro_log(destro_log):
    if not os.path.exists(destro_log):
        open(destro_log, 'w').close()

    with open(destro_log, "r") as file:
        file.seek(0, 2)  # Seek to end

        while True:
            line = file.readline()

            if not line:
                time.sleep(0.2)
                continue

            line = re.sub(r'\x1b\[[0-9;]*m', '', line)  # Remove ANSI

            with lock:
           
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
                        # print("jiooo")
                        batch, robot_id, case_num, total_cases, item_id = match.groups()
                        robot_key = f"Robot{int(robot_id)+1}"
                        robot_destro_data[robot_key][item_id] = {
                        "batch": int(batch),
                        "case_num": int(case_num),
                        "total_cases": int(total_cases),
                    }
                    robot_total_cases[f'Robot{int(robot_id)+1}'] +=1
                    cases_per_hour[robot_key][log_hour_str] += 1
                elif "CODE 101" in line:
                    pattern =re.compile(r"CODE 101 --------------- (\d+)")
                    match =pattern.search(line)
                    print(match)
                    if match :
                        cases=match.groups()
                        print(f"cases ----{cases}")
                      

                        log_data['total_cases']=int(cases[0])

def start_destro_thread(log_path):
    thread1 = threading.Thread(target=read_destro_log, args=(log_path,), daemon=True)
    thread1.start()


def start_fms_thread(log_path):
    thread2 =threading.Thread(target= read_fms_log, args=(log_path,),daemon= True)
    thread2.start()
