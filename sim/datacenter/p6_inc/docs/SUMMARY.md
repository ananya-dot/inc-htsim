# p6_inc Folder Summary

## Overview

The `p6_inc` folder is a comprehensive toolkit for generating traffic patterns and analyzing simulation results for the NDP (Network Data Plane) network simulator. It focuses on collective communication patterns, particularly **allreduce** operations commonly used in distributed machine learning training.

## Purpose

This folder provides tools to:
1. **Generate traffic matrices** for various network communication patterns
2. **Analyze simulation logs** to understand network behavior and performance
3. **Visualize results** through comprehensive plotting and statistical analysis

---

## Directory Structure

### 📝 Traffic Matrix Generators

Python scripts that generate connection matrix (`.cm`) files for network simulations:

- **`gen_allreduce.py`** - Generates ring-based allreduce traffic patterns
  - Creates sequential ring communication where each node sends to the next
  - Parameters: nodes, connections, group size, flow size, locality, random seed

- **`gen_allreduce_extended.py`** - Generates hierarchical multi-ring allreduce
  - **Phase 1**: Intra-ring reduction (nodes reduce data within their ring)
  - **Phase 2**: Inter-ring leader aggregation (ring leaders exchange data)
  - **Phase 3**: Intra-ring broadcast (results propagate back to all nodes)
  - More complex pattern simulating real distributed training scenarios

- **`gen_allreduce_tree_extended.py`** - Tree-based allreduce pattern generator

- **`gen_incast.py`** - Generates incast traffic (many-to-one communication)
  - Useful for testing network congestion scenarios

- **`gen_outcast_incast.py`** - Generates both outcast and incast patterns

- **`gen_permutation.py`** - Generates permutation traffic patterns

### 📊 Connection Matrix Files

Pre-generated traffic patterns in `.cm` format:

- **`allreduce.cm`** - Small example (32 nodes, 224 connections)
- **`allreduce_extended.cm`** - Extended example (8 nodes, 58 connections)
- **`small_allreduce_extended.cm`** - Medium test case (3,965 lines)
- **`large_allreduce_extended.cm`** - Large-scale test case (31,685 lines)

**Connection Matrix Format:**
```
Nodes <N>
Connections <M>
Triggers <T>
<src>-><dst> id <id> [start <time>] [trigger <trigger_id>] size <bytes> [send_done_trigger <trigger_id>]
trigger id <id> oneshot
```

### 🔍 Analysis Tools

Python scripts for analyzing simulation output logs:

- **`analyze_log.py`** - Main NDP sink log analyzer
  - Rate analysis over time
  - Flow completion tracking
  - Network utilization metrics
  - Cumulative ACK evolution
  - Generates 5+ visualization plots

- **`analyze_traffic_log.py`** - Traffic-level log analysis
  - Packet-level event tracking
  - Flow statistics
  - Traffic pattern visualization

- **`analyze_switch_log.py`** - Switch-level log analysis
  - Queue occupancy tracking
  - Switch utilization
  - Congestion analysis
  - Queue distribution statistics

- **`analyze_combined_logs.py`** - Combined analysis of multiple log types
  - Correlates sink, traffic, and switch data
  - Comprehensive network-wide analysis

### 📚 Example Scripts

Usage examples for the analysis tools:

- **`example_usage.py`** - Example for using the log analyzer
- **`example_traffic_usage.py`** - Example for traffic log analysis
- **`example_switch_usage.py`** - Example for switch log analysis

### 📖 Documentation

Located in `docs/` folder:

- **`ANALYSIS_SUMMARY.md`** - Overview of analysis capabilities
- **`README_analyzer.md`** - Detailed documentation for log analyzer
- **`README_switch_analyzer.md`** - Documentation for switch analyzer
- **`SWITCH_ANALYSIS_SUMMARY.md`** - Switch analysis summary

### 🎨 Analysis Output

The `analysis/` folder contains generated visualization plots:
- Rate heatmaps and time series
- Queue occupancy and utilization
- Network congestion indicators
- Traffic event distributions
- Flow completion statistics

### ⚙️ Configuration

- **`requirements.txt`** - Python dependencies:
  - pandas >= 1.3.0
  - numpy >= 1.21.0
  - matplotlib >= 3.5.0
  - seaborn >= 0.11.0

---

## Typical Workflow

### 1. Generate Traffic Matrix
```bash
python gen_allreduce_extended.py output.cm 8 4 4 1000000 1 42
# Parameters: filename, nodes, conns, groupsize, flowsize, locality, randseed
```

### 2. Run Simulation
```bash
./main_ndp -strat ecmp_host -nodes 8 -tm output.cm -log sink -o results.log
```

### 3. Analyze Results
```bash
python analyze_log.py results.log
# Generates visualization plots in current directory
```

---

## Key Features

### Allreduce Pattern Generation

The extended allreduce generator creates realistic distributed training communication:

1. **Intra-ring Reduction**: Nodes in each ring sequentially reduce their data
2. **Inter-ring Aggregation**: Ring leaders exchange aggregated results
3. **Intra-ring Broadcast**: Final results propagate back to all nodes

This mimics real-world collective operations in frameworks like PyTorch DDP or Horovod.

### Analysis Capabilities

- **Rate Visualization**: Time series plots, 2D heatmaps
- **Flow Tracking**: Completion times, data transfer volumes
- **Network Metrics**: Utilization, congestion detection
- **Statistical Analysis**: Distributions, outliers, percentiles
- **Reorder Buffer Analysis**: Packet reordering detection

### Generated Visualizations

1. `rate_over_time.png` - Rate evolution for sample sinks
2. `rate_heatmap.png` - 2D heatmap of rates by sink and time
3. `cack_evolution.png` - Cumulative ACK evolution
4. `rate_distributions.png` - Statistical distributions
5. `network_utilization.png` - Network-wide utilization metrics
6. `queue_heatmap.png` - Switch queue occupancy (switch logs)
7. `traffic_event_heatmap.png` - Traffic event patterns (traffic logs)

---

## Use Cases

1. **Research on Collective Communication**
   - Study allreduce performance under different network conditions
   - Compare routing strategies (ECMP, adaptive routing, etc.)

2. **Protocol Testing**
   - Test NDP behavior with various traffic patterns
   - Evaluate congestion control mechanisms

3. **Performance Analysis**
   - Analyze network topology efficiency
   - Identify bottlenecks in communication patterns

4. **Distributed Training Simulation**
   - Model real ML training communication patterns
   - Optimize network configurations for training workloads

---

## Dependencies

- Python 3.x
- pandas, numpy, matplotlib, seaborn (see `requirements.txt`)
- Network simulator binary (`main_ndp`)
- Log parsing tool (`parse_output`) for binary log conversion

---

## Notes

- Connection matrices use trigger-based dependencies to model sequential communication
- Allreduce patterns are designed to simulate realistic distributed training scenarios
- Analysis tools support both sink-level and switch-level log analysis
- Generated visualizations help identify network bottlenecks and performance issues

---

## Related Files

- `main_ndp.cpp` - Main NDP simulation program
- `ndp.h` / `ndp.cpp` - NDP protocol implementation
- Connection matrix files are consumed by the simulator via `-tm` parameter

