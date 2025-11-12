# Network Switch Log Analyzer

This Python script analyzes queue logs from the csg-htsim network simulation and generates comprehensive visualizations for understanding switch behavior and network congestion.

## Features

- **Queue Analysis**: Tracks queue occupancy, utilization, and capacity over time
- **Congestion Detection**: Identifies periods of high queue utilization and network congestion
- **Network Metrics**: Provides network-wide statistics and performance indicators
- **Visualization**: Generates multiple plots for different aspects of queue behavior

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
python analyze_switch_log.py
```
This will analyze `../small_allreduce_extended_switch.log` by default.

### Specify Log File
```bash
python analyze_switch_log.py /path/to/your/switch_logfile.log
```

## Generated Outputs

The script generates several PNG files:

1. **queue_occupancy_over_time.png**: Queue occupancy evolution for sample queues
2. **queue_heatmap.png**: 2D heatmap of queue occupancy by queue and time
3. **queue_utilization.png**: Queue utilization percentage over time
4. **queue_distributions.png**: Statistical distributions of queue metrics
5. **network_congestion.png**: Network-wide congestion and utilization metrics
6. **queue_evolution.png**: Detailed queue size evolution (min, current, max)

## Understanding the Plots

### Queue Occupancy Over Time
- Shows how individual queue sizes change during the simulation
- Helps identify burst patterns and congestion periods
- Sample of queues shown for clarity

### Queue Heatmap
- 2D visualization of queue occupancy across all queues and time
- Dark areas = low occupancy, bright areas = high occupancy
- Shows spatial and temporal patterns in queue usage

### Queue Utilization
- Tracks percentage of queue capacity being used
- Values close to 100% indicate potential congestion
- Helps identify bottlenecks in the network

### Queue Distributions
- Statistical analysis of queue size patterns
- Shows distribution shapes and outliers
- Helps understand queue behavior characteristics

### Network Congestion
- Total and average queue occupancy over time
- Number of active queues (congestion indicator)
- Average and maximum utilization metrics

### Queue Evolution
- Detailed view of individual queue behavior
- Shows min, current, and max queue sizes
- Helps understand queue dynamics

## Interpreting Results

### Switch Behavior
- **Queue Occupancy**: High values indicate buffering
- **Utilization**: Values >80% suggest potential congestion
- **Active Queues**: More active queues during high traffic

### Congestion Indicators
- **High Utilization**: Queues consistently >80% full
- **Queue Growth**: Increasing queue sizes over time
- **Active Queues**: Many queues active simultaneously

### Performance Metrics
- **Throughput**: How well queues handle traffic
- **Latency**: Higher queue occupancy = higher latency
- **Efficiency**: How well the network utilizes queue capacity

## Sample Analysis Results

From the `small_allreduce_extended_switch.log` analysis:

- **Total Records**: 3,920 queue log entries
- **Unique Queues**: 80 different switch queues
- **Time Range**: 0.02 - 0.98 ms (0.96 ms duration)
- **Max Queue Size**: 203.77 KB
- **Mean Queue Size**: 43.93 KB
- **Max Utilization**: 100% (some queues fully utilized)
- **Mean Utilization**: 52.96%
- **Congestion Rate**: 10.18% of records show >80% utilization

## Troubleshooting

1. **Parse Error**: Ensure the log file is a valid queue log
2. **Missing Dependencies**: Install requirements.txt
3. **Empty Plots**: Check if the log contains actual queue data
4. **Memory Issues**: For large logs, the script samples data for visualization

## Customization

You can modify the script to:
- Change sampling rates for large datasets
- Add new analysis metrics
- Customize plot styles and colors
- Export data to CSV for further analysis
- Focus on specific time periods or queues

## Comparison with Sink Logs

- **Sink Logs**: Show end-to-end flow performance
- **Switch Logs**: Show intermediate network behavior
- **Combined Analysis**: Use both for complete network understanding

## Queue Types

The analyzer handles different queue types:
- **Input Queues**: Queues at switch input ports
- **Output Queues**: Queues at switch output ports
- **Internal Queues**: Queues within switch fabric
