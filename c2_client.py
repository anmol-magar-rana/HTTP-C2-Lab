import time
import uuid
import requests
from datetime import datetime, timezone
import random

SERVER = "http://127.0.0.1:8080"            # this ip loops back to any device used to run this code. no packets leave the network card, everything is internal.
#AGENT_ID = f"agent-{uuid.uuid4().hex[:6]}"  # generates a random agent id each run
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
    print(f"[+] Agent started with ID: {AGENT_ID}")

    while True:

        # beacon by checking in with server
        resp = checkin()
        print(f"[+] Check-in response: {resp}")

        # get tasks, if any, and carry them out
        tasks = fetch_tasks()
        if tasks:
            print(f"[+] Received {len(tasks)} task(s)")

            for t in tasks:
                task_id = t.get("task_id")
                task_text = t.get("task")

                print(f"[+] Executing task {task_id}: {task_text}")

                output = perform_task(task_text)

                # upon finishing taks, send results back to server
                r = send_results(task_id, output)
                print(f"[+] Sent results: {r}")

        else:
            print("[+] No tasks received")

        # go to sleep for random amount of time to avoid detection 
        sleep_time = random.randint(5, 12)
        print(f"[+] Sleeping {sleep_time} seconds...\n")
        time.sleep(sleep_time)

##################################################################

if __name__ == "__main__":
    agent_loop()
