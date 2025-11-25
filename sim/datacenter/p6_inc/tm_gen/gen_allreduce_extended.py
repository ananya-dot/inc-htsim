#!/usr/bin/env python3
"""
Generate a hierarchical multi-ring allreduce traffic matrix with:
1. Intra-ring reduction
2. Inter-ring leader aggregation
3. Intra-ring broadcast (propagation)

Usage:
  python gen_allreduce_extended.py <filename> <nodes> <conns> <groupsize> <flowsize> <locality> <randseed>
"""

import sys
from random import seed, shuffle

if len(sys.argv) != 8:
    print("Usage: python gen_allreduce_multiring.py <filename> <nodes> <conns> <groupsize> <flowsize> <locality> <randseed>")
    sys.exit()

filename = sys.argv[1]
nodes = int(sys.argv[2])
conns = int(sys.argv[3])
groupsize = int(sys.argv[4])
flowsize = int(sys.argv[5])
locality = int(sys.argv[6])
randseed = int(sys.argv[7])

print(f"Nodes: {nodes}")
print(f"Connections: {conns}")
print(f"All-reduce group size: {groupsize}")
print(f"Flowsize: {flowsize} bytes")
print(f"Random Seed: {randseed}")

f = open(filename, "w")
srcs = list(range(nodes))
if randseed != 0:
    seed(randseed)
shuffle(srcs)

groups = conns // groupsize
print(f"Groups: {groups}")
print("Nodes", nodes, file=f)

id = 0
trig_id = 1
group_end_triggers = []

# -----------------------------
# Phase 1: Intra-ring reduction
# -----------------------------
connections = 0
for group in range(groups):
    groupsrcs = [srcs[group * groupsize + n] for n in range(groupsize)]
    if locality == 1:
        groupsrcs.sort()

    first_trigger = trig_id
    for s in range(groupsize):
        for d in range(1, groupsize):
            id += 1
            src = (s + d - 1) % groupsize
            dst = (s + d) % groupsize
            out = f"{groupsrcs[src]}->{groupsrcs[dst]} id {id}"
            if d == 1:
                out += " start 0"
            else:
                out += f" trigger {trig_id}"
                trig_id += 1
            out += f" size {flowsize}"
            if d != groupsize - 1:
                out += f" send_done_trigger {trig_id}"
            print(out, file=f)
            connections += 1
    group_end_triggers.append(trig_id - 1)

# --------------------------------------
# Phase 2: Inter-ring leader aggregation
# --------------------------------------
leader_triggers = []
for g in range(groups):
    leader = srcs[g * groupsize]  # leader of each ring
    next_leader = srcs[((g + 1) % groups) * groupsize]
    trig_id += 1
    id += 1
    out = f"{leader}->{next_leader} id {id} trigger {group_end_triggers[g]} size {flowsize // 10}"
    out += f" send_done_trigger {trig_id}"
    print(out, file=f)
    leader_triggers.append(trig_id)
    connections += 1
# ------------------------------------------------------
# Phase 3: Intra-ring broadcast (propagation of gradients)
# ------------------------------------------------------
for g in range(groups):
    groupsrcs = [srcs[g * groupsize + n] for n in range(groupsize)]
    leader = groupsrcs[0]
    leader_done_trigger = leader_triggers[g]
    for s in range(groupsize - 1):
        id += 1
        src = groupsrcs[s]
        dst = groupsrcs[s + 1]
        out = f"{src}->{dst} id {id} trigger {leader_done_trigger} size {flowsize}"
        if s < groupsize - 2:
            trig_id += 1
            out += f" send_done_trigger {trig_id}"
            leader_done_trigger = trig_id
        connections += 1
        print(out, file=f)
        

# -----------------------
# Global trigger section
# -----------------------
trigger_count = 0
for t in range(1, trig_id + 1):
    print(f"trigger id {t} oneshot", file=f)
    trigger_count += 1

f.close()

# write the number of connections on the second line of the file
insert_line = f"Connections {connections}\nTriggers {trigger_count}\n"
with open(filename, "r") as f:
    lines = f.readlines()

# Insert at index 1 (0-based indexing)
lines.insert(1, insert_line)

with open(filename, "w") as f:
    f.writelines(lines)


print(f"Calculated Connections: {connections}")
print(f"\nHierarchical multi-ring allreduce written to {filename}")
