#!/usr/bin/env python3
"""
Generate a tree-based allreduce traffic matrix:
1. Upward reduction phase (leaves → root)
2. Downward broadcast phase (root → leaves)

Usage:
  python gen_allreduce_tree.py <filename> <nodes> <branch_factor> <flowsize> <randseed>
"""

import sys
from random import seed, shuffle

if len(sys.argv) != 6:
    print("Usage: python gen_allreduce_tree.py <filename> <nodes> <branch_factor> <flowsize> <randseed>")
    sys.exit()

filename = sys.argv[1]
nodes = int(sys.argv[2])
branch_factor = int(sys.argv[3])
flowsize = int(sys.argv[4])
randseed = int(sys.argv[5])

print(f"Generating tree-based AllReduce")
print(f"Nodes: {nodes}, Branch factor: {branch_factor}, Flow size: {flowsize} bytes, Seed: {randseed}")

if randseed != 0:
    seed(randseed)

# Output file setup
f = open(filename, "w")
print("Nodes", nodes, file=f)

# Compute parent-child relationships
children = {}
parents = {}
for i in range(nodes):
    children[i] = []
for i in range(1, nodes):
    parent = (i - 1) // branch_factor
    parents[i] = parent
    children[parent].append(i)

# Count connections (each link used twice: up & down)
connections = (nodes - 1) * 2
triggers = (nodes - 1) * 2
print(f"Connections {connections}", file=f)
print(f"Triggers {triggers}", file=f)

id = 0
trig_id = 1

# ------------------------
# Phase 1: Upward reduction
# ------------------------
print("# Phase 1: Upward Reduction", file=f)
for i in range(nodes - 1, 0, -1):  # leaves to root
    src = i
    dst = parents[i]
    id += 1
    out = f"{src}->{dst} id {id} start 0 size {flowsize}"
    out += f" send_done_trigger {trig_id}"
    print(out, file=f)
    trig_id += 1

# ------------------------
# Phase 2: Downward broadcast
# ------------------------
print("# Phase 2: Downward Broadcast", file=f)
for parent in range(nodes):
    for child in children[parent]:
        id += 1
        out = f"{parent}->{child} id {id} trigger {trig_id - (nodes - 1)} size {flowsize}"
        if child != children[parent][-1]:
            out += f" send_done_trigger {trig_id}"
            trig_id += 1
        print(out, file=f)

# ------------------------
# Trigger section
# ------------------------
print("# Trigger Section", file=f)
for t in range(1, trig_id + 1):
    print(f"trigger id {t} oneshot", file=f)

f.close()
print(f"Tree-based allreduce connection matrix written to {filename}")
