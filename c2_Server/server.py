"""
C2 Server Simulation, Flask REST API

This file implements a lightweight command-and-control (C2) server used for
SOC practice / red-team simulation labs / personal learning. This server is 
simple and file-backed to keep the C2 workflow transparent studying the basics of c2. 
It implements a set of REST endpoints that allow agents to:

1. Check in with the server and announce their presence.
2. Retrieve queued tasks/commands assigned to them.
3. Upload execution results after completing tasks.

Data Persistence
All state is stored in two JSON files:

1. tasks.json   : Maps agent_id to list of task objects. Each task contains { task_id, task, issued timestamp }.
2. esults.json : Maps agent_id to list of result objects. Each result contains { task_id, output, received timestamp }.

Endpoints
1. POST /api/v1/checkin
    Agents call this periodically to announce that they are alive.
    Returns a status message and a UTC timestamp.

2. GET /api/v1/tasks/<agent_id>
    Returns all pending tasks for the specified agent.

3. POST /api/v1/tasks
    Allows an operator to assign a new task to an agent.
    Expects JSON with { agent_id, task }.
    Generates a unique task_id and stores it.

4. POST /api/v1/results
    Agents post execution results here.
    Expects JSON with { agent_id, task_id, output }.
"""


from flask import Flask, request, jsonify
import json
import uuid
from datetime import datetime, timezone


app = Flask(__name__)                     # initialize web server

TASKS_FILE = "c2_Server/tasks.json"       # stores persistent simulation data
RESULTS_FILE = "c2_Server/results.json"   # stores persistent simulation data

# the following are helper functions to load/save data from/to the json files above
def load_tasks():
    # read tasks file to get tasks/commands
    try:
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_tasks(tasks):
    # open tasks file and write to it. indent = 4 to make it readable
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=4)       # dumps the python dictionary into json format

def load_results():
    # read resuls file to get results stored in it
    try:
        with open(RESULTS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_results(results):
    # open results file and write to it. indent = 4 to make it readable
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=4)     # dumps the python dictionary into json format

###########################################################################

# this creates an endpoint that accepts only POST. agents call this every interval/cycle
@app.route("/api/v1/checkin", methods=["POST"])
def checkin():
    # read the json sent by agent
    data = request.json
    agent_id = data.get("agent_id")

    # return a response including status, message and timestamp
    return jsonify({
        "status": "ok",
        "message": f"Agent {agent_id} checked in",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

###########################################################################

# dynamic url for every agent that connects
@app.route("/api/v1/tasks/<agent_id>", methods=["GET"])
def fetch_tasks(agent_id):
    # checks database if theres a task for this specific agent. if not, returns nothing
    tasks = load_tasks()
    agent_tasks = tasks.get(agent_id, [])
    return jsonify({"tasks": agent_tasks})

###########################################################################
# add tasks using POST method
@app.route("/api/v1/tasks", methods=["POST"])
def add_task():
    #reads data from the json file. it must contain agent id and task 
    data = request.json
    agent_id = data.get("agent_id")
    task_text = data.get("task")

    # load current task database
    tasks = load_tasks()

    #if this is a new agent, initialize empty tasks
    if agent_id not in tasks:
        tasks[agent_id] = []

    # create a unique task id
    task_id = str(uuid.uuid4())
    
    # append new task object to the database
    tasks[agent_id].append({
        "task_id": task_id,
        "task": task_text,
        "issued": datetime.now(timezone.utc).isoformat()
    })

    # save it to the tasks.json
    save_tasks(tasks)

    return jsonify({"status": "task_queued", "task_id": task_id})

###########################################################################

# agents post here after completing their tasks/commands
@app.route("/api/v1/results", methods=["POST"])
def upload_results():
    # read data and extract all fields
    data = request.json
    agent_id = data.get("agent_id")
    task_id = data.get("task_id")
    output = data.get("output")

    # load the current result database
    results = load_results()

    # if this is a new agent, initialize empty results
    if agent_id not in results:
        results[agent_id] = []

    # append the results to the database
    results[agent_id].append({
        "task_id": task_id,
        "output": output,
        "received": datetime.utcnow().isoformat()
    })

    # update the database
    save_results(results)

    return jsonify({"status": "results_saved"})

###########################################################################

# server start
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
