#!/usr/bin/env python
import collections
import glob
import numpy as np
import os
import rosbag
import sys
import math
import tf.transformations
import copy
from spataps_msgs.msg import GlobalState, AgentState, Task


def dist(a, b):
    return math.sqrt(math.pow(a[0] - b[0], 2) + math.pow(a[1] - b[1], 2))


def get_yaw(pose):
    q = [pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w]
    alpha = tf.transformations.euler_from_quaternion(q)[2]
    return alpha


def twist_to_uv((x, pose)):
    q = [pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w]
    alpha = tf.transformations.euler_from_quaternion(q)[2]
    #    alpha += math.pi / 2
    return math.cos(alpha) * abs(x), math.sin(alpha) * abs(x)


def evaluate_dir(dirname):
    bag_files = sorted(glob.glob(os.path.join(dirname, "*.bag")))
    avgs = []
    w_avgs = []
    ts = []
    for idx, bag in enumerate(bag_files):
        print("evaluating run", bag)
        avg, w_avg, t = evalutate_bagfile(bag)
        avgs.append(avg)
        w_avgs.append(w_avg)
        ts.append(t)

    print "means", np.mean(np.array(avgs))
    print "w_means", np.mean(np.array(w_avgs))
    print "times", np.mean(np.array(ts))


def make_agent_tasks_state(msg):
    #assert isinstance(msg, GlobalState)
    agent_loads = set()
    for a in msg.agents:
        #assert isinstance(a, AgentState)
        agent_loads.add((a.id, a.current_load))
    tasks = set()
    for t in msg.tasks:
        #assert isinstance(t, Task)
        tasks.add((t.location, t.id, t.priority))
    return agent_loads, tasks


def evalutate_bagfile(bagfile):
    bag = rosbag.Bag(bagfile)
    #
    # read all messages
    events = []
    cur_state = None
    time = 0.0
    first_task_found = False
    started_task_times = collections.OrderedDict()
    finished_task_times = collections.OrderedDict()
    finished_tasks = set()
    deliverered = 0
    for topic, msg, _ in bag.read_messages(topics=["/global_state"]):
        if topic == "/global_state":
            loads, tasks = make_agent_tasks_state(msg)

            if not first_task_found:
                if len(tasks) == 0:
                    continue
                else:
                    first_task_found = True
                    cur_state = (time, loads, set())

            if not tasks == cur_state[2] or not loads == cur_state[1]:
                for t in tasks:
                    if t not in started_task_times:
                        started_task_times[t] = time

                for t in cur_state[2]:
                    if t not in tasks:
                        finished_task_times[t] = time
                        finished_tasks.add(t)
                for l, old_l in zip(sorted(list(loads)), sorted(list(cur_state[1]))):
                    if l[1] < old_l[1]:
                        deliverered += old_l[1]
                events.append((time, loads, tasks, finished_tasks, deliverered))
                cur_state = (time, loads, tasks, finished_tasks, deliverered)

                finished_tasks = copy.deepcopy(finished_tasks)
            time += 0.2
            #if time > 210:
            #    break

    print "task_times:"
    weighted_avg = []
    avg = []
    last_time = 0
    for t in finished_task_times:
        weighted_avg.append((finished_task_times[t] - started_task_times[t]) * t[2])
        avg.append(finished_task_times[t] - started_task_times[t])
        #print started_task_times[t], finished_task_times[t] - started_task_times[t], t
        last_time = max(last_time, finished_task_times[t])

    unfinished_tasks = [t for t in started_task_times if t not in finished_task_times]
    for t in unfinished_tasks:
        weighted_avg.append((time - started_task_times[t]) * t[2])
        avg.append(time - started_task_times[t])

    print "avg.time", np.mean(np.array(avg))
    print "weighed_avg.time", np.mean(np.array(weighted_avg))
    print "Runtime", last_time
    for e in events:
        print_event(e)
    return np.sum(np.array(avg)), np.sum(np.array(weighted_avg)), last_time


def print_event(e):
    time, inv, tasks, finished_tasks, delivered = e
    sort_inv = [x[1] for x in sorted(list(inv))]
    sorted_tasks = [0] * 7
    for t in tasks:
        sorted_tasks[t[0]-1] += 1
    sorted_finished = [0] * 7
    for t in finished_tasks:
        sorted_finished[t[0] - 1] += 1

    print time
    print "robot_state = ", sort_inv, ";"
    print "task_state = ", sorted_tasks, ";"
    print "picked_state = ", sorted_finished, ";"
    print "depot = ", delivered, ";"


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "usage: evaluate.py <dirname>"
        sys.exit(-1)

    fname = sys.argv[1]

    path = os.path.join(os.getcwd(), fname)
    print "reading %s .." % (path)
    evaluate_dir(path)
