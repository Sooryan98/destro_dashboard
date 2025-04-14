
import os
import time
import threading
from threading import Event 
import re
from collections import defaultdict

robot_destro_data = defaultdict(lambda: defaultdict(list))
progress= defaultdict(int)
log_data={}
log_data['total_cases']=0
robot_fms_data={}
for i in range (0,17):
    robot_fms_data[f"Robot {i}"]=0
start_clock=0

flag=False
lock = threading.Lock()
flag_event= Event()

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
                        progress[hour]= cases
                        
                    

                elif "CODE 000" in line :
                    print("FMS CAN START NOW")
                    flag_event.set()

                else:
                    pattern = re.compile(r"Robot robot_(\d+)\s+has travelled\s+([\d\.]+)\s+m")


                    match = pattern.search(line)
                    if match:
                        robot_id, dist = match.groups()
                        robot_key = f"Robot {robot_id}"
                        robot_fms_data[robot_key]= dist
                        
                    


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
