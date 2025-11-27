#!/usr/bin/env python3
"""
Generate a supernode-based allreduce traffic matrix where:
1. All regular nodes send their gradients to the supernode
2. Supernode aggregates and sends the result back to all regular nodes

This pattern repeats for multiple iterations.

Usage:
  python gen_allreduce_supernode.py <filename> <nodes> <flowsize> <iterations> <randseed>
  
Where:
  - nodes: Total number of nodes including supernode (e.g., 129 for K=8 fat-tree)
  - flowsize: Size of each gradient in bytes
  - iterations: Number of allreduce iterations
  - randseed: Random seed for shuffling node order (0 for no shuffle)
"""

import sys
from random import seed, shuffle

if len(sys.argv) != 6:
    print("Usage: python gen_allreduce_supernode.py <filename> <nodes> <flowsize> <iterations> <randseed>")
    print("  Example: python gen_allreduce_supernode.py allreduce_supernode.cm 129 1048576 10 42")
    sys.exit(1)

filename = sys.argv[1]
nodes = int(sys.argv[2])
flowsize = int(sys.argv[3])
iterations = int(sys.argv[4])
randseed = int(sys.argv[5])

# Supernode is the last node (node ID = nodes - 1)
supernode_id = nodes - 1
regular_nodes = list(range(supernode_id))

print(f"Nodes: {nodes} (regular: 0-{supernode_id-1}, supernode: {supernode_id})")
print(f"Flowsize: {flowsize} bytes")
print(f"Iterations: {iterations}")
print(f"Random Seed: {randseed}")

f = open(filename, "w")
print("Nodes", nodes, file=f)

# Shuffle regular nodes if seed is provided
if randseed != 0:
    seed(randseed)
    shuffle(regular_nodes)
    print(f"Regular nodes order (shuffled): {regular_nodes[:min(10, len(regular_nodes))]}...")

id = 0
trig_id = 1
connections = 0

# Track the trigger that will start the next iteration
next_iteration_trigger = None

# For each iteration of allreduce
for iteration in range(iterations):
    print(f"\nIteration {iteration + 1}:")
    
    # Phase 1: All regular nodes send gradients to supernode IN PARALLEL
    # All nodes start at the same time (either time 0 or after previous iteration)
    phase1_send_done_triggers = []
    
    for i, node in enumerate(regular_nodes):
        id += 1
        if iteration == 0 and i == 0:
            # First node of first iteration: start at time 0
            out = f"{node}->{supernode_id} id {id} start 0 size {flowsize}"
        elif iteration > 0 and i == 0:
            # First node of subsequent iteration: wait for previous iteration
            out = f"{node}->{supernode_id} id {id} trigger {next_iteration_trigger} size {flowsize}"
        else:
            # Other nodes: start at same time as first node (no trigger, or same trigger)
            if iteration == 0:
                out = f"{node}->{supernode_id} id {id} start 0 size {flowsize}"
            else:
                out = f"{node}->{supernode_id} id {id} trigger {next_iteration_trigger} size {flowsize}"
        
        # Each send creates a done trigger
        trig_id += 1
        out += f" send_done_trigger {trig_id}"
        phase1_send_done_triggers.append(trig_id)
        
        print(out, file=f)
        connections += 1
    
    # Phase 2: Supernode sends aggregated gradient back to all regular nodes
    # Wait for ALL phase 1 sends to complete - use the last trigger from phase 1
    # Actually, we need a trigger that fires when ALL phase 1 sends are done
    # For simplicity, we'll use the last trigger (assuming all sends complete around the same time)
    phase2_start_trigger = phase1_send_done_triggers[-1]
    
    # Supernode sends to all regular nodes sequentially
    phase2_trigger = phase2_start_trigger
    for i, dest in enumerate(regular_nodes):
        id += 1
        out = f"{supernode_id}->{dest} id {id} trigger {phase2_trigger} size {flowsize}"
        
        if i < len(regular_nodes) - 1:
            # Not the last send - create trigger for next send
            trig_id += 1
            out += f" send_done_trigger {trig_id}"
            phase2_trigger = trig_id
        else:
            # Last send in this iteration - create trigger for next iteration (if any)
            if iteration < iterations - 1:
                trig_id += 1
                out += f" send_done_trigger {trig_id}"
                phase2_trigger = trig_id
            else:
                # Last iteration - no need for trigger
                phase2_trigger = None
        
        print(out, file=f)
        connections += 1
    
    # Set trigger for next iteration (if any)
    next_iteration_trigger = phase2_trigger

# -----------------------
# Global trigger section
# -----------------------
trigger_count = 0
for t in range(1, trig_id + 1):
    print(f"trigger id {t} oneshot", file=f)
    trigger_count += 1

f.close()

# Write the number of connections and triggers on lines 2-3
insert_line = f"Connections {connections}\nTriggers {trigger_count}\n"
with open(filename, "r") as f:
    lines = f.readlines()

# Insert at index 1 (0-based indexing)
lines.insert(1, insert_line)

with open(filename, "w") as f:
    f.writelines(lines)

print(f"\nCalculated Connections: {connections}")
print(f"Calculated Triggers: {trigger_count}")
print(f"\nSupernode-based allreduce traffic matrix written to {filename}")
print(f"Pattern: {len(regular_nodes)} nodes -> supernode -> {len(regular_nodes)} nodes (x{iterations} iterations)")

