# Network Simulation Log Analyzer

This Python script analyzes NDP sink logs from the csg-htsim network simulation and generates comprehensive visualizations.

## Features

- **Rate Analysis**: Plots network rates over time, distributions, and heatmaps
- **Flow Analysis**: Tracks cumulative ACK evolution and flow completion
- **Network Utilization**: Shows total utilization, active sinks, and congestion patterns
- **Statistical Summary**: Provides detailed statistics and top active sinks

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
python analyze_log.py
```
This will analyze `../small_allreduce_extended.log` by default.

### Specify Log File
```bash
python analyze_log.py /path/to/your/logfile.log
```

## Generated Outputs

The script generates several PNG files:

1. **rate_over_time.png**: Rate evolution for sample sinks over time
2. **rate_heatmap.png**: 2D heatmap of rates by sink and time
3. **cack_evolution.png**: Cumulative ACK evolution showing data transfer progress
4. **rate_distributions.png**: Statistical distributions of rates and reorder buffers
5. **network_utilization.png**: Network-wide utilization metrics

## Understanding the Plots

### Rate Over Time
- Shows how individual sink rates change during the simulation
- Helps identify burst patterns and congestion periods
- Sample of sinks shown for clarity

### Rate Heatmap
- 2D visualization of rates across all sinks and time
- Dark areas = low/no traffic, bright areas = high traffic
- Shows spatial and temporal patterns in the allreduce operation

### CAck Evolution
- Tracks cumulative bytes received by each sink
- Shows flow completion progress
- Steep slopes indicate high throughput periods

### Rate Distributions
- Statistical analysis of rate patterns
- Shows distribution shapes and outliers
- Helps understand traffic characteristics

### Network Utilization
- Total network capacity usage over time
- Number of active sinks (congestion indicator)
- Average and maximum rates per sink

## Interpreting Results

### Allreduce Pattern
- **Bursty Traffic**: Allreduce typically shows bursty patterns as nodes exchange data
- **High Utilization**: Look for periods of high total utilization
- **Flow Completion**: CAck evolution shows when flows complete

### Congestion Indicators
- **Rate Drops**: Sudden drops in rates may indicate congestion
- **Reorder Buffers**: Non-zero reorder buffer sizes indicate packet reordering
- **Active Sinks**: Fewer active sinks during congestion

### Performance Metrics
- **Throughput**: Total rate over time
- **Fairness**: Distribution of rates across sinks
- **Efficiency**: How well the network is utilized

## Troubleshooting

1. **Parse Error**: Ensure the log file is a valid NDP sink log
2. **Missing Dependencies**: Install requirements.txt
3. **Empty Plots**: Check if the log contains actual traffic data
4. **Memory Issues**: For large logs, the script samples data for visualization

## Customization

You can modify the script to:
- Change sampling rates for large datasets
- Add new analysis metrics
- Customize plot styles and colors
- Export data to CSV for further analysis
