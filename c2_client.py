"""
C2 Agent Simulation / HTTP Client

This file implements a minimal agent that communicates with the companion 
Flask-based C2 server. The agent periodically checks in, retrieves tasks, 
executes simple simulated commands, and uploads results back to the server.

The purpose of this file is to demonstrate the command-and-control flow 
for SOC learning, threat emulation labs, and detection engineering practice. As such,
it is simple and does not execute real system commands. It focuses strictly on 
demonstrating communication patterns and C2 mechanics. 
All communication occurs inside the OS networking stack, no real network is involved.

1. Check-In:
    POST /api/v1/checkin
    The agent announces that it is alive and provides its agent_id.

2. Fetch Tasks:
    GET /api/v1/tasks/<agent_id>
    The agent retrieves any pending tasks that the operator has assigned.

3. Execute Tasks:
    The agent runs toy commands (e.g., "hello") inside perform_task().

4. Send Results:
    POST /api/v1/results
    The agent uploads command output back to the server.

Main Loop
The agent_loop() function simulates continuous beaconing behavior found in 
real-world implant/C2 frameworks. After each cycle, the agent sleeps for a 
random period to mimic jitter and reduce detection likelihood.
"""

import time
import requests
from datetime import datetime, timezone
import random

# this ip loops back to any device used to run this code. 
# no packets leave the network card, everything is internal.
SERVER = "http://127.0.0.1:8080"            
AGENT_ID = f"agent-123"

# this function does not execute any commands. it simply returns descriptive output
def perform_task(task_text):

    if task_text == "hello":
        return "world"

    if task_text == "time":
        return f"Current time: {datetime.now(timezone.utc).isoformat()}"
    
    # unknown task
    return f"Unknown task: {task_text}"

# agent checks in with the c2 server
def checkin():
    url = f"{SERVER}/api/v1/checkin"
    payload = {"agent_id": AGENT_ID}
    try:
        r = requests.post(url, json=payload, timeout=5)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

##################################################################

# agent gets their to do tasks from the server
def fetch_tasks():
    url = f"{SERVER}/api/v1/tasks/{AGENT_ID}"
    try:
        r = requests.get(url, timeout=5)
        return r.json().get("tasks", [])
    except Exception as e:
        return []

##################################################################

# agent sends back results to the server
def send_results(task_id, output):
    url = f"{SERVER}/api/v1/results"
    payload = {
        "agent_id": AGENT_ID,
        "task_id": task_id,
        "output": output
    }

    try:
        r = requests.post(url, json=payload, timeout=5)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

##################################################################

# main loop for the agent, simulates it never turning off and beaconing to c2 server
def agent_loop():
    print(f"Agent started with ID: {AGENT_ID}")

    while True:

        # beacon by checking in with server
        resp = checkin()
        print(f"Check-in response: {resp}")

        # get tasks, if any, and carry them out
        tasks = fetch_tasks()
        if tasks:
            print(f"Received {len(tasks)} task(s)")

            for t in tasks:
                task_id = t.get("task_id")
                task_text = t.get("task")

                print(f"[+] Executing task {task_id}: {task_text}")

                output = perform_task(task_text)

                # upon finishing taks, send results back to server
                r = send_results(task_id, output)
                print(f"Sent results: {r}")

        else:
            print("No tasks received")

        # go to sleep for random amount of time to avoid detection 
        sleep_time = random.randint(5, 12)
        print(f"Sleeping {sleep_time} seconds...\n")
        time.sleep(sleep_time)

##################################################################

if __name__ == "__main__":
    agent_loop()
