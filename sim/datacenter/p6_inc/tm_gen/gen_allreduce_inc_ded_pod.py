#!/usr/bin/env python3
"""
all_reduce_inc.py (FINAL VERSION)

INC-aware all-reduce generator with:
 - multi-iteration rounds
 - balanced chunk → aggregator mapping inside a designated aggregation pod
 - pipeline staggering window
 - trigger-based iteration barriers
 - P4-inspired semantics: agg_op, agg_dir, cid, rid, fid

Usage:
  python all_reduce_inc.py <out_file> <nodes> <k> <flowsize> <chunks> <fid> <iterations> <window> <randseed>
"""

import sys
from random import seed, shuffle

# --------------------------
# Parse Arguments
# --------------------------
if len(sys.argv) != 10:
    print("Usage: python all_reduce_inc.py <out_file> <nodes> <k> <flowsize> <chunks> <fid> <iterations> <window> <randseed>")
    sys.exit(1)

out_file    = sys.argv[1]
nodes       = int(sys.argv[2])
k           = int(sys.argv[3])
flowsize    = int(sys.argv[4])
chunks      = int(sys.argv[5])
fid         = int(sys.argv[6])
iterations  = int(sys.argv[7])
window      = int(sys.argv[8])
randseed    = int(sys.argv[9])

# --------------------------
# Fat-tree derived params
# --------------------------
def nodes_per_pod(k):
    return k * k // 4

POD_SIZE = nodes_per_pod(k)
NPOD = k
AGG_POD = 0
AGG_POD_START = AGG_POD * POD_SIZE
AGG_POD_END   = AGG_POD_START + POD_SIZE - 1
agg_nodes = list(range(AGG_POD_START, AGG_POD_END + 1))

if randseed != 0:
    seed(randseed)

hosts = list(range(nodes))

print(f"OUT={out_file} nodes={nodes} k={k} pods={NPOD}")
print(f"Aggregation pod = {AGG_POD}, aggregator nodes = {agg_nodes}")
print(f"Chunks = {chunks}, Iterations = {iterations}, Window = {window}")

# --------------------------
# Write header
# --------------------------
f = open(out_file, "w")
print(f"Nodes {nodes}", file=f)

flow_id = 0
trig_id = 1
connections = 0

# --------------------------
# Helpers
# --------------------------
def start_or_trigger_str(start_tr):
    if start_tr is None or start_tr == 0:
        return "start 0"
    return f"trigger {start_tr}"

def chunk_to_agg_node(cid):
    return agg_nodes[cid % len(agg_nodes)]

# For pipeline staggering
last_downlink_trigger = [-1] * chunks
iteration_start_trigger = None

# --------------------------
# MAIN: ITERATIONS
# --------------------------
for it in range(iterations):
    rid = it + 1
    print(f"\n# --- ITERATION {rid} ---", file=f)

    for c in range(chunks):

        # -------------------- CHUNK START CONDITION --------------------
        if c < window:
            chunk_start_trigger = iteration_start_trigger
        else:
            prev_t = last_downlink_trigger[c - window]
            chunk_start_trigger = prev_t if prev_t != -1 else iteration_start_trigger

        dst_agg = chunk_to_agg_node(c)

        # -------------------- UPLINK (agg_dir = UP) --------------------
        last_upload_trig = None

        for src in hosts:
            if src == dst_agg:
                continue  # local contribution

            flow_id += 1
            outline = f"{src}->{dst_agg} id {flow_id} "
            outline += start_or_trigger_str(chunk_start_trigger)
            outline += f" size {flowsize} "

            # INC semantics
            outline += (
                f"semantics agg_op SUM agg_dir UP "
                f"fid {fid} rid {rid} cid {c} "
            )

            trig_id += 1
            outline += f"send_done_trigger {trig_id}"
            last_upload_trig = trig_id

            print(outline, file=f)
            connections += 1

        if last_upload_trig is None:
            trig_id += 1
            last_upload_trig = trig_id

        # -------------------- DOWNLINK (agg_dir = DOWN) --------------------
        last_down_trig = None

        for dst in hosts:
            if dst == dst_agg:
                continue

            flow_id += 1
            outline = f"{dst_agg}->{dst} id {flow_id} "
            outline += f"trigger {last_upload_trig} size {flowsize} "

            # INC semantics: DOWN direction
            outline += (
                f"semantics agg_op SUM agg_dir DOWN "
                f"fid {fid} rid {rid} cid {c} "
            )

            trig_id += 1
            outline += f"send_done_trigger {trig_id}"
            last_down_trig = trig_id

            print(outline, file=f)
            connections += 1

        if last_down_trig is None:
            trig_id += 1
            last_down_trig = trig_id

        last_downlink_trigger[c] = last_down_trig

    iteration_start_trigger = last_downlink_trigger[chunks - 1]

# --------------------------
# TRIGGERS SECTION
# --------------------------
print("\n# --- TRIGGERS ---", file=f)
for t in range(1, trig_id + 1):
    print(f"trigger id {t} oneshot", file=f)

f.close()

# summary header
with open(out_file, "r") as ff:
    lines = ff.readlines()

lines.insert(1, f"Connections {connections}\nTriggers {trig_id}\n")

with open(out_file, "w") as ff:
    ff.writelines(lines)

print(f"Generated {connections} flows and {trig_id} triggers → {out_file}")
