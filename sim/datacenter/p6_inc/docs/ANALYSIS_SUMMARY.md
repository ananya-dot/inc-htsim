# Network Simulation Log Analysis Summary

## Overview
The `analyze_log.py` script provides comprehensive analysis and visualization of NDP sink logs from the csg-htsim network simulation.

## Key Features

### 1. **Rate Analysis**
- **Rate Over Time**: Shows how individual sink rates change during the simulation
- **Rate Heatmap**: 2D visualization of rates across all sinks and time periods
- **Rate Distributions**: Statistical analysis of rate patterns and outliers

### 2. **Flow Analysis**
- **Cumulative ACK Evolution**: Tracks data transfer progress for each sink
- **Flow Completion**: Shows when flows complete and how much data was transferred

### 3. **Network Utilization**
- **Total Utilization**: Network-wide capacity usage over time
- **Active Sinks**: Number of sinks actively transmitting data
- **Congestion Indicators**: Identifies periods of network congestion

### 4. **Statistical Summary**
- **Performance Metrics**: Max, mean, and standard deviation of rates
- **Flow Statistics**: Data transfer volumes and completion rates
- **Top Active Sinks**: Most active sinks by throughput

## Generated Visualizations

1. **`rate_over_time.png`**: Rate evolution for sample sinks over time
2. **`rate_heatmap.png`**: 2D heatmap of rates by sink and time
3. **`cack_evolution.png`**: Cumulative ACK evolution showing data transfer progress
4. **`rate_distributions.png`**: Statistical distributions of rates and reorder buffers
5. **`network_utilization.png`**: Network-wide utilization metrics

## Sample Analysis Results

From the `small_allreduce_extended.log` analysis:

- **Total Records**: 18,432 sink log entries
- **Unique Sinks**: 2,048 different sink endpoints
- **Time Range**: 0.1 - 0.9 ms (0.8 ms duration)
- **Max Rate**: 10.08 Gbps
- **Mean Rate**: 4.72 Gbps (non-zero rates)
- **Active Sinks**: 1,888 out of 18,432 records had non-zero rates
- **Data Transferred**: Up to 1.01 MB per sink
- **Reorder Events**: 125 sinks experienced packet reordering

## Interpreting the Results

### Allreduce Pattern
- **Bursty Traffic**: The allreduce operation shows bursty patterns as nodes exchange data
- **High Utilization**: Periods of high total network utilization indicate active data exchange
- **Flow Completion**: Steep slopes in CAck evolution show high throughput periods

### Congestion Indicators
- **Rate Drops**: Sudden drops in rates may indicate network congestion
- **Reorder Buffers**: Non-zero reorder buffer sizes indicate packet reordering
- **Active Sinks**: Fewer active sinks during congestion periods

### Performance Metrics
- **Throughput**: Total rate over time shows network capacity utilization
- **Fairness**: Distribution of rates across sinks shows fairness of the protocol
- **Efficiency**: How well the network is utilized during the allreduce operation

## Usage

```bash
# Basic usage
python3 analyze_log.py

# Specify log file
python3 analyze_log.py /path/to/your/logfile.log

# Run example
python3 example_usage.py
```

## Requirements

- Python 3.6+
- pandas >= 1.3.0
- numpy >= 1.21.0
- matplotlib >= 3.5.0
- seaborn >= 0.11.0

## Installation

```bash
pip install -r requirements.txt
```

## Troubleshooting

1. **Parse Error**: Ensure the log file is a valid NDP sink log
2. **Missing Dependencies**: Install requirements.txt
3. **Empty Plots**: Check if the log contains actual traffic data
4. **Memory Issues**: For large logs, the script samples data for visualization
