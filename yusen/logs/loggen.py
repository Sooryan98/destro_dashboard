# log_simulator.py
import time
import random

log_file_path = "test.log"

def generate_log_line():
    codes = [
        lambda: f"[INFO] CODE 101 Total cases processed: {random.randint(100, 500)}",
        # lambda: f"[INFO] CODE 104 Simulated truck unloading delay: {random.randint(10, 50)}",
        # lambda: f"[INFO] CODE 106 bot_id=R{random.randint(1, 3)} task=XYZ {round(random.uniform(1.0, 10.0), 2)}",
        # lambda: f"[INFO] CODE 107 {random.randint(1, 100)}*****",
        # lambda: f"[INFO] CODE 108 picker_id=H{random.randint(1, 2)} task=XYZ {round(random.uniform(1.0, 10.0), 2)}"
    ]
    return random.choice(codes)()

def simulate_log():
    with open(log_file_path, "a") as f:
        while True:
            log_line = generate_log_line()
            print(f"Writing log: {log_line}")
            f.write(log_line + "\n")
            f.flush()
            time.sleep(random.uniform(0.5, 2.5))  # vary the frequency

if __name__ == "__main__":
    simulate_log()
