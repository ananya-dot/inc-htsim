#!/usr/bin/env python3
"""
Combined Network Log Analyzer
Analyzes both sink and switch logs from csg-htsim network simulation for comprehensive network understanding.

Usage: python analyze_combined_logs.py [sink_log] [switch_log]
"""

import os
import sys
import subprocess
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import argparse
from pathlib import Path

class CombinedLogAnalyzer:
    def __init__(self, sink_log_path, switch_log_path):
        self.sink_log_path = sink_log_path
        self.switch_log_path = switch_log_path
        self.sink_data = None
        self.switch_data = None
        
    def parse_sink_log(self):
        """Parse the sink log file"""
        print("Parsing sink log file...")
        
        parse_tool = "../../parse_output"
        if not os.path.exists(parse_tool):
            print(f"Error: parse_output tool not found at {parse_tool}")
            return False
            
        try:
            result = subprocess.run([parse_tool, self.sink_log_path, "-ascii"], 
                                  capture_output=True, text=True, check=True)
            
            lines = result.stdout.strip().split('\n')
            data = []
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 13 and parts[1] == "Type" and parts[2] == "NDP_SINK":
                        try:
                            timestamp = float(parts[0])
                            sink_id = int(parts[4])
                            cack = int(parts[8])
                            reorder_buffer = int(parts[10])
                            rate = int(parts[12])
                            
                            data.append({
                                'timestamp': timestamp,
                                'sink_id': sink_id,
                                'cack': cack,
                                'reorder_buffer': reorder_buffer,
                                'rate': rate
                            })
                        except (ValueError, IndexError):
                            continue
            
            if not data:
                print("No valid sink data found")
                return False
                
            self.sink_data = pd.DataFrame(data)
            self.sink_data['rate_gbps'] = self.sink_data['rate'] / 1e9
            self.sink_data['cack_mb'] = self.sink_data['cack'] / 1e6
            self.sink_data['time_ms'] = self.sink_data['timestamp'] * 1000
            
            print(f"Parsed {len(self.sink_data)} sink records")
            return True
            
        except Exception as e:
            print(f"Error parsing sink log: {e}")
            return False
    
    def parse_switch_log(self):
        """Parse the switch log file"""
        print("Parsing switch log file...")
        
        parse_tool = "../../parse_output"
        if not os.path.exists(parse_tool):
            print(f"Error: parse_output tool not found at {parse_tool}")
            return False
            
        try:
            result = subprocess.run([parse_tool, self.switch_log_path, "-ascii"], 
                                  capture_output=True, text=True, check=True)
            
            lines = result.stdout.strip().split('\n')
            data = []
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 8 and parts[1] == "Type" and parts[2] == "QUEUE_APPROX":
                        try:
                            timestamp = float(parts[0])
                            queue_id = int(parts[4])
                            last_q = int(parts[7])
                            min_q = int(parts[9])
                            max_q = int(parts[11])
                            
                            data.append({
                                'timestamp': timestamp,
                                'queue_id': queue_id,
                                'last_q': last_q,
                                'min_q': min_q,
                                'max_q': max_q
                            })
                        except (ValueError, IndexError):
                            continue
            
            if not data:
                print("No valid switch data found")
                return False
                
            self.switch_data = pd.DataFrame(data)
            self.switch_data['last_q_kb'] = self.switch_data['last_q'] / 1024
            self.switch_data['max_q_kb'] = self.switch_data['max_q'] / 1024
            self.switch_data['utilization'] = self.switch_data['last_q'] / (self.switch_data['max_q'] + 1e-6) * 100
            self.switch_data['time_ms'] = self.switch_data['timestamp'] * 1000
            
            print(f"Parsed {len(self.switch_data)} switch records")
            return True
            
        except Exception as e:
            print(f"Error parsing switch log: {e}")
            return False
    
    def plot_correlation_analysis(self):
        """Plot correlation between sink rates and switch congestion"""
        plt.figure(figsize=(15, 10))
        
        # Calculate time-aligned metrics
        sink_time_groups = self.sink_data.groupby('time_ms')
        switch_time_groups = self.switch_data.groupby('time_ms')
        
        # Get common time points
        common_times = set(sink_time_groups.groups.keys()) & set(switch_time_groups.groups.keys())
        common_times = sorted(list(common_times))
        
        if not common_times:
            print("No common time points found between sink and switch logs")
            return
        
        # Calculate metrics for common times
        sink_rates = []
        switch_utilizations = []
        times = []
        
        for time_ms in common_times:
            sink_group = sink_time_groups.get_group(time_ms)
            switch_group = switch_time_groups.get_group(time_ms)
            
            avg_rate = sink_group['rate_gbps'].mean()
            avg_utilization = switch_group['utilization'].mean()
            
            sink_rates.append(avg_rate)
            switch_utilizations.append(avg_utilization)
            times.append(time_ms)
        
        # Plot 1: Rate vs Utilization over time
        plt.subplot(2, 2, 1)
        plt.plot(times, sink_rates, 'b-', label='Avg Sink Rate (Gbps)', linewidth=2)
        plt.plot(times, switch_utilizations, 'r-', label='Avg Switch Utilization (%)', linewidth=2)
        plt.xlabel('Time (ms)')
        plt.ylabel('Rate (Gbps) / Utilization (%)')
        plt.title('Sink Rates vs Switch Utilization Over Time')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot 2: Scatter plot of rate vs utilization
        plt.subplot(2, 2, 2)
        plt.scatter(sink_rates, switch_utilizations, alpha=0.6)
        plt.xlabel('Average Sink Rate (Gbps)')
        plt.ylabel('Average Switch Utilization (%)')
        plt.title('Rate vs Utilization Correlation')
        plt.grid(True, alpha=0.3)
        
        # Calculate correlation
        correlation = np.corrcoef(sink_rates, switch_utilizations)[0, 1]
        plt.text(0.05, 0.95, f'Correlation: {correlation:.3f}', 
                transform=plt.gca().transAxes, bbox=dict(boxstyle="round", facecolor='wheat'))
        
        # Plot 3: Total network throughput vs total queue occupancy
        total_rates = []
        total_occupancy = []
        
        for time_ms in common_times:
            sink_group = sink_time_groups.get_group(time_ms)
            switch_group = switch_time_groups.get_group(time_ms)
            
            total_rate = sink_group['rate_gbps'].sum()
            total_occupancy_kb = switch_group['last_q_kb'].sum()
            
            total_rates.append(total_rate)
            total_occupancy.append(total_occupancy_kb)
        
        plt.subplot(2, 2, 3)
        plt.plot(times, total_rates, 'g-', label='Total Network Rate (Gbps)', linewidth=2)
        plt.plot(times, total_occupancy, 'm-', label='Total Queue Occupancy (KB)', linewidth=2)
        plt.xlabel('Time (ms)')
        plt.ylabel('Rate (Gbps) / Occupancy (KB)')
        plt.title('Total Network Throughput vs Queue Occupancy')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot 4: Congestion analysis
        plt.subplot(2, 2, 4)
        high_util_times = [t for t, u in zip(times, switch_utilizations) if u > 80]
        high_rate_times = [t for t, r in zip(times, sink_rates) if r > sink_rates[np.argmax(sink_rates)] * 0.8]
        
        plt.hist(high_util_times, bins=20, alpha=0.7, label='High Utilization Times', color='red')
        plt.hist(high_rate_times, bins=20, alpha=0.7, label='High Rate Times', color='blue')
        plt.xlabel('Time (ms)')
        plt.ylabel('Frequency')
        plt.title('Congestion vs High Throughput Periods')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('correlation_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_network_performance_overview(self):
        """Plot comprehensive network performance overview"""
        plt.figure(figsize=(20, 12))
        
        # Calculate time-aligned metrics
        sink_time_groups = self.sink_data.groupby('time_ms')
        switch_time_groups = self.switch_data.groupby('time_ms')
        
        common_times = sorted(list(set(sink_time_groups.groups.keys()) & set(switch_time_groups.groups.keys())))
        
        if not common_times:
            print("No common time points found")
            return
        
        # Calculate metrics
        metrics = {
            'time': [],
            'total_rate': [],
            'avg_rate': [],
            'active_sinks': [],
            'total_occupancy': [],
            'avg_utilization': [],
            'max_utilization': [],
            'active_queues': []
        }
        
        for time_ms in common_times:
            sink_group = sink_time_groups.get_group(time_ms)
            switch_group = switch_time_groups.get_group(time_ms)
            
            metrics['time'].append(time_ms)
            metrics['total_rate'].append(sink_group['rate_gbps'].sum())
            metrics['avg_rate'].append(sink_group['rate_gbps'].mean())
            metrics['active_sinks'].append(len(sink_group[sink_group['rate_gbps'] > 0]))
            metrics['total_occupancy'].append(switch_group['last_q_kb'].sum())
            metrics['avg_utilization'].append(switch_group['utilization'].mean())
            metrics['max_utilization'].append(switch_group['utilization'].max())
            metrics['active_queues'].append(len(switch_group[switch_group['last_q_kb'] > 0]))
        
        # Plot 1: Network throughput
        plt.subplot(3, 3, 1)
        plt.plot(metrics['time'], metrics['total_rate'], 'b-', linewidth=2)
        plt.xlabel('Time (ms)')
        plt.ylabel('Total Rate (Gbps)')
        plt.title('Total Network Throughput')
        plt.grid(True, alpha=0.3)
        
        # Plot 2: Average rate per sink
        plt.subplot(3, 3, 2)
        plt.plot(metrics['time'], metrics['avg_rate'], 'g-', linewidth=2)
        plt.xlabel('Time (ms)')
        plt.ylabel('Avg Rate per Sink (Gbps)')
        plt.title('Average Sink Rate')
        plt.grid(True, alpha=0.3)
        
        # Plot 3: Active sinks
        plt.subplot(3, 3, 3)
        plt.plot(metrics['time'], metrics['active_sinks'], 'r-', linewidth=2)
        plt.xlabel('Time (ms)')
        plt.ylabel('Number of Active Sinks')
        plt.title('Active Sinks Over Time')
        plt.grid(True, alpha=0.3)
        
        # Plot 4: Total queue occupancy
        plt.subplot(3, 3, 4)
        plt.plot(metrics['time'], metrics['total_occupancy'], 'm-', linewidth=2)
        plt.xlabel('Time (ms)')
        plt.ylabel('Total Queue Occupancy (KB)')
        plt.title('Total Queue Occupancy')
        plt.grid(True, alpha=0.3)
        
        # Plot 5: Average utilization
        plt.subplot(3, 3, 5)
        plt.plot(metrics['time'], metrics['avg_utilization'], 'orange', linewidth=2)
        plt.xlabel('Time (ms)')
        plt.ylabel('Average Utilization (%)')
        plt.title('Average Queue Utilization')
        plt.grid(True, alpha=0.3)
        
        # Plot 6: Maximum utilization
        plt.subplot(3, 3, 6)
        plt.plot(metrics['time'], metrics['max_utilization'], 'purple', linewidth=2)
        plt.xlabel('Time (ms)')
        plt.ylabel('Max Utilization (%)')
        plt.title('Maximum Queue Utilization')
        plt.grid(True, alpha=0.3)
        
        # Plot 7: Active queues
        plt.subplot(3, 3, 7)
        plt.plot(metrics['time'], metrics['active_queues'], 'brown', linewidth=2)
        plt.xlabel('Time (ms)')
        plt.ylabel('Number of Active Queues')
        plt.title('Active Queues Over Time')
        plt.grid(True, alpha=0.3)
        
        # Plot 8: Rate vs Utilization scatter
        plt.subplot(3, 3, 8)
        plt.scatter(metrics['total_rate'], metrics['avg_utilization'], alpha=0.6)
        plt.xlabel('Total Rate (Gbps)')
        plt.ylabel('Average Utilization (%)')
        plt.title('Throughput vs Congestion')
        plt.grid(True, alpha=0.3)
        
        # Plot 9: Network efficiency
        plt.subplot(3, 3, 9)
        efficiency = [r / (u + 1e-6) for r, u in zip(metrics['total_rate'], metrics['avg_utilization'])]
        plt.plot(metrics['time'], efficiency, 'k-', linewidth=2)
        plt.xlabel('Time (ms)')
        plt.ylabel('Efficiency (Rate/Utilization)')
        plt.title('Network Efficiency Over Time')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('network_performance_overview.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_combined_summary(self):
        """Generate a comprehensive summary of both logs"""
        print("\n" + "="*70)
        print("COMBINED NETWORK LOG ANALYSIS SUMMARY")
        print("="*70)
        
        if self.sink_data is not None:
            print(f"Sink Log Analysis:")
            print(f"  Total Records: {len(self.sink_data):,}")
            print(f"  Unique Sinks: {self.sink_data['sink_id'].nunique():,}")
            print(f"  Time Range: {self.sink_data['time_ms'].min():.3f} - {self.sink_data['time_ms'].max():.3f} ms")
            print(f"  Max Rate: {self.sink_data['rate_gbps'].max():.2f} Gbps")
            print(f"  Mean Rate: {self.sink_data['rate_gbps'][self.sink_data['rate_gbps'] > 0].mean():.2f} Gbps")
        
        if self.switch_data is not None:
            print(f"\nSwitch Log Analysis:")
            print(f"  Total Records: {len(self.switch_data):,}")
            print(f"  Unique Queues: {self.switch_data['queue_id'].nunique():,}")
            print(f"  Time Range: {self.switch_data['time_ms'].min():.3f} - {self.switch_data['time_ms'].max():.3f} ms")
            print(f"  Max Queue Size: {self.switch_data['last_q_kb'].max():.2f} KB")
            print(f"  Mean Queue Size: {self.switch_data['last_q_kb'][self.switch_data['last_q_kb'] > 0].mean():.2f} KB")
            print(f"  Max Utilization: {self.switch_data['utilization'].max():.2f}%")
            print(f"  Mean Utilization: {self.switch_data['utilization'][self.switch_data['utilization'] > 0].mean():.2f}%")
        
        # Combined analysis
        if self.sink_data is not None and self.switch_data is not None:
            print(f"\nCombined Analysis:")
            
            # Find common time range
            sink_times = set(self.sink_data['time_ms'])
            switch_times = set(self.switch_data['time_ms'])
            common_times = sink_times & switch_times
            
            if common_times:
                print(f"  Common Time Points: {len(common_times)}")
                print(f"  Overlap Duration: {min(common_times):.3f} - {max(common_times):.3f} ms")
                
                # Calculate correlation
                sink_time_groups = self.sink_data.groupby('time_ms')
                switch_time_groups = self.switch_data.groupby('time_ms')
                
                sink_rates = []
                switch_utilizations = []
                
                for time_ms in sorted(common_times):
                    sink_group = sink_time_groups.get_group(time_ms)
                    switch_group = switch_time_groups.get_group(time_ms)
                    
                    avg_rate = sink_group['rate_gbps'].mean()
                    avg_utilization = switch_group['utilization'].mean()
                    
                    sink_rates.append(avg_rate)
                    switch_utilizations.append(avg_utilization)
                
                correlation = np.corrcoef(sink_rates, switch_utilizations)[0, 1]
                print(f"  Rate-Utilization Correlation: {correlation:.3f}")
                
                if correlation > 0.5:
                    print("  → Strong positive correlation: Higher rates lead to higher congestion")
                elif correlation < -0.5:
                    print("  → Strong negative correlation: Higher rates lead to lower congestion")
                else:
                    print("  → Weak correlation: Rate and congestion are largely independent")
        
        print("\n" + "="*70)
    
    def run_analysis(self):
        """Run the complete combined analysis"""
        print("Starting Combined Network Log Analysis")
        print("="*50)
        
        # Parse both log files
        if not self.parse_sink_log():
            print("Failed to parse sink log")
            return False
        
        if not self.parse_switch_log():
            print("Failed to parse switch log")
            return False
        
        # Generate plots
        print("\nGenerating combined analysis plots...")
        self.plot_correlation_analysis()
        self.plot_network_performance_overview()
        
        # Generate summary
        self.generate_combined_summary()
        
        print("\nCombined analysis complete! Check the generated PNG files for visualizations.")
        return True

def main():
    parser = argparse.ArgumentParser(description='Analyze both sink and switch logs from csg-htsim')
    parser.add_argument('sink_log', nargs='?', 
                       default='../small_allreduce_extended.log',
                       help='Path to the sink log file')
    parser.add_argument('switch_log', nargs='?', 
                       default='../small_allreduce_extended_switch.log',
                       help='Path to the switch log file')
    
    args = parser.parse_args()
    
    # Check if log files exist
    if not os.path.exists(args.sink_log):
        print(f"Error: Sink log file '{args.sink_log}' not found")
        return 1
    
    if not os.path.exists(args.switch_log):
        print(f"Error: Switch log file '{args.switch_log}' not found")
        return 1
    
    # Create analyzer and run analysis
    analyzer = CombinedLogAnalyzer(args.sink_log, args.switch_log)
    success = analyzer.run_analysis()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
