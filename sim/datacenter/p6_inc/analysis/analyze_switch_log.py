#!/usr/bin/env python3
"""
Network Switch Log Analyzer
Analyzes queue logs from csg-htsim network simulation and generates visualization plots.

Usage: python analyze_switch_log.py [log_file_path]
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

class SwitchLogAnalyzer:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.parsed_data = None
        self.object_mappings = {}
        self.queue_data = None
        
    def parse_log_file(self):
        """Parse the binary log file using parse_output tool"""
        print("Parsing switch log file...")
        
        # Check if parse_output tool exists
        parse_tool = "../../parse_output"
        if not os.path.exists(parse_tool):
            print(f"Error: parse_output tool not found at {parse_tool}")
            return False
            
        try:
            # Run parse_output tool
            result = subprocess.run([parse_tool, self.log_file_path, "-ascii"], 
                                  capture_output=True, text=True, check=True)
            
            # Parse the output
            lines = result.stdout.strip().split('\n')
            data = []
            
            print(f"Processing {len(lines)} lines from parse_output")
            
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
                        except (ValueError, IndexError) as e:
                            # Try alternative parsing for different format
                            try:
                                timestamp = float(parts[0])
                                queue_id = int(parts[4])
                                last_q = 0
                                min_q = 0
                                max_q = 0
                                
                                # Look for queue values in the line
                                for i, part in enumerate(parts):
                                    if part == "LastQ" and i + 1 < len(parts):
                                        last_q = int(parts[i + 1])
                                    elif part == "MinQ" and i + 1 < len(parts):
                                        min_q = int(parts[i + 1])
                                    elif part == "MaxQ" and i + 1 < len(parts):
                                        max_q = int(parts[i + 1])
                                
                                data.append({
                                    'timestamp': timestamp,
                                    'queue_id': queue_id,
                                    'last_q': last_q,
                                    'min_q': min_q,
                                    'max_q': max_q
                                })
                            except (ValueError, IndexError):
                                continue
                    elif len(parts) >= 8 and "QUEUE_APPROX" in line:
                        # Handle cases where format might be slightly different
                        try:
                            timestamp = float(parts[0])
                            queue_id = int(parts[4])
                            last_q = 0
                            min_q = 0
                            max_q = 0
                            
                            # Look for queue values in the line
                            for i, part in enumerate(parts):
                                if part == "LastQ" and i + 1 < len(parts):
                                    last_q = int(parts[i + 1])
                                elif part == "MinQ" and i + 1 < len(parts):
                                    min_q = int(parts[i + 1])
                                elif part == "MaxQ" and i + 1 < len(parts):
                                    max_q = int(parts[i + 1])
                            
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
                print("No valid data found in log file")
                return False
                
            self.parsed_data = pd.DataFrame(data)
            print(f"Parsed {len(self.parsed_data)} records")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error running parse_output: {e}")
            return False
        except Exception as e:
            print(f"Error parsing log: {e}")
            return False
    
    def load_object_mappings(self):
        """Load object name to ID mappings from the log file preamble"""
        print("Loading object mappings...")
        
        try:
            # Try to read as text first
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(': ndp_') and '=' in line:
                        # Parse: : ndp_X_Y=ID or : ndp_sink_X_Y=ID
                        parts = line.split('=')
                        if len(parts) == 2:
                            name = parts[0][2:]  # Remove ': '
                            queue_id = int(parts[1])
                            self.object_mappings[queue_id] = name
                            
        except Exception as e:
            print(f"Warning: Could not load object mappings: {e}")
            # Try binary mode as fallback
            try:
                with open(self.log_file_path, 'rb') as f:
                    content = f.read()
                    # Look for text patterns in binary data
                    text_content = content.decode('utf-8', errors='ignore')
                    for line in text_content.split('\n'):
                        line = line.strip()
                        if line.startswith(': ndp_') and '=' in line:
                            parts = line.split('=')
                            if len(parts) == 2:
                                name = parts[0][2:]
                                queue_id = int(parts[1])
                                self.object_mappings[queue_id] = name
            except Exception as e2:
                print(f"Warning: Could not load object mappings from binary: {e2}")
    
    def analyze_queue_data(self):
        """Analyze the queue data and compute statistics"""
        if self.parsed_data is None:
            print("Error: No parsed data available")
            return
        
        print("Analyzing queue data...")
        
        # Convert queue sizes from bytes to KB
        self.parsed_data['last_q_kb'] = self.parsed_data['last_q'] / 1024
        self.parsed_data['min_q_kb'] = self.parsed_data['min_q'] / 1024
        self.parsed_data['max_q_kb'] = self.parsed_data['max_q'] / 1024
        
        # Convert timestamp to milliseconds
        self.parsed_data['time_ms'] = self.parsed_data['timestamp'] * 1000
        
        # Calculate queue utilization (current vs max)
        self.parsed_data['utilization'] = self.parsed_data['last_q'] / (self.parsed_data['max_q'] + 1e-6) * 100
        
        # Group by queue_id for analysis
        self.queue_data = self.parsed_data.groupby('queue_id').agg({
            'last_q_kb': ['max', 'mean', 'std'],
            'min_q_kb': ['min', 'mean'],
            'max_q_kb': ['max', 'mean'],
            'utilization': ['max', 'mean', 'std'],
            'time_ms': ['min', 'max']
        }).round(3)
        
        # Flatten column names
        self.queue_data.columns = ['_'.join(col).strip() for col in self.queue_data.columns]
        
        # Add object names if available
        if self.object_mappings:
            self.queue_data['object_name'] = self.queue_data.index.map(self.object_mappings)
        
        print(f"Analyzed {len(self.queue_data)} unique queues")
    
    def plot_queue_occupancy_over_time(self):
        """Plot queue occupancy over time for sample queues"""
        plt.figure(figsize=(15, 8))
        
        # Sample queues for visibility (plot every 20th queue)
        sample_queues = self.parsed_data['queue_id'].unique()[::20]
        
        for queue_id in sample_queues:
            queue_data = self.parsed_data[self.parsed_data['queue_id'] == queue_id]
            plt.plot(queue_data['time_ms'], queue_data['last_q_kb'], 
                    alpha=0.7, linewidth=1, label=f'Queue {queue_id}')
        
        plt.xlabel('Time (ms)')
        plt.ylabel('Queue Occupancy (KB)')
        plt.title('Queue Occupancy Over Time (Sample of Queues)')
        plt.grid(True, alpha=0.3)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig('queue_occupancy_over_time.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_queue_heatmap(self):
        """Create a heatmap of queue occupancy by queue and time"""
        plt.figure(figsize=(20, 10))
        
        # Create pivot table for heatmap
        pivot_data = self.parsed_data.pivot_table(
            values='last_q_kb', 
            index='queue_id', 
            columns='time_ms', 
            fill_value=0
        )
        
        # Sample data for visibility
        sample_queues = pivot_data.index[::10]  # Every 10th queue
        sample_times = pivot_data.columns[::5]  # Every 5th time point
        
        heatmap_data = pivot_data.loc[sample_queues, sample_times]
        
        sns.heatmap(heatmap_data, cmap='viridis', cbar_kws={'label': 'Queue Occupancy (KB)'})
        plt.xlabel('Time (ms)')
        plt.ylabel('Queue ID')
        plt.title('Queue Occupancy Heatmap: Queue vs Time')
        plt.tight_layout()
        plt.savefig('queue_heatmap.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_queue_utilization(self):
        """Plot queue utilization over time"""
        plt.figure(figsize=(15, 8))
        
        # Sample queues for visibility
        sample_queues = self.parsed_data['queue_id'].unique()[::15]
        
        for queue_id in sample_queues:
            queue_data = self.parsed_data[self.parsed_data['queue_id'] == queue_id]
            if queue_data['utilization'].max() > 0:  # Only plot queues with activity
                plt.plot(queue_data['time_ms'], queue_data['utilization'], 
                        alpha=0.8, linewidth=2, label=f'Queue {queue_id}')
        
        plt.xlabel('Time (ms)')
        plt.ylabel('Queue Utilization (%)')
        plt.title('Queue Utilization Over Time')
        plt.grid(True, alpha=0.3)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig('queue_utilization.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_queue_distributions(self):
        """Plot distribution of queue statistics"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Last queue size distribution
        last_q = self.parsed_data['last_q_kb']
        axes[0, 0].hist(last_q[last_q > 0], bins=50, alpha=0.7, edgecolor='black')
        axes[0, 0].set_xlabel('Last Queue Size (KB)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].set_title('Last Queue Size Distribution (Non-zero)')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Max queue size distribution
        max_q = self.parsed_data['max_q_kb']
        axes[0, 1].hist(max_q[max_q > 0], bins=50, alpha=0.7, edgecolor='black', color='orange')
        axes[0, 1].set_xlabel('Max Queue Size (KB)')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title('Max Queue Size Distribution')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Utilization distribution
        utilization = self.parsed_data['utilization']
        axes[1, 0].hist(utilization[utilization > 0], bins=50, alpha=0.7, edgecolor='black', color='green')
        axes[1, 0].set_xlabel('Queue Utilization (%)')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].set_title('Queue Utilization Distribution')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Box plot of queue sizes by queue (top 20 most active queues)
        top_queues = self.parsed_data.groupby('queue_id')['last_q_kb'].max().nlargest(20).index
        top_queue_data = self.parsed_data[self.parsed_data['queue_id'].isin(top_queues)]
        sns.boxplot(data=top_queue_data, x='queue_id', y='last_q_kb', ax=axes[1, 1])
        axes[1, 1].set_xlabel('Queue ID')
        axes[1, 1].set_ylabel('Last Queue Size (KB)')
        axes[1, 1].set_title('Queue Size Distribution by Top 20 Most Active Queues')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('queue_distributions.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_network_congestion(self):
        """Plot network-wide congestion metrics"""
        plt.figure(figsize=(15, 10))
        
        # Calculate congestion metrics over time
        time_groups = self.parsed_data.groupby('time_ms')
        
        total_occupancy = time_groups['last_q_kb'].sum()
        avg_occupancy = time_groups['last_q_kb'].mean()
        max_occupancy = time_groups['last_q_kb'].max()
        avg_utilization = time_groups['utilization'].mean()
        max_utilization = time_groups['utilization'].max()
        active_queues = time_groups['last_q_kb'].apply(lambda x: (x > 0).sum())
        
        # Plot 1: Total queue occupancy
        plt.subplot(2, 3, 1)
        plt.plot(total_occupancy.index, total_occupancy.values, linewidth=2)
        plt.xlabel('Time (ms)')
        plt.ylabel('Total Queue Occupancy (KB)')
        plt.title('Total Network Queue Occupancy')
        plt.grid(True, alpha=0.3)
        
        # Plot 2: Average queue occupancy
        plt.subplot(2, 3, 2)
        plt.plot(avg_occupancy.index, avg_occupancy.values, linewidth=2, color='orange')
        plt.xlabel('Time (ms)')
        plt.ylabel('Average Queue Occupancy (KB)')
        plt.title('Average Queue Occupancy')
        plt.grid(True, alpha=0.3)
        
        # Plot 3: Maximum queue occupancy
        plt.subplot(2, 3, 3)
        plt.plot(max_occupancy.index, max_occupancy.values, linewidth=2, color='red')
        plt.xlabel('Time (ms)')
        plt.ylabel('Max Queue Occupancy (KB)')
        plt.title('Maximum Queue Occupancy')
        plt.grid(True, alpha=0.3)
        
        # Plot 4: Average utilization
        plt.subplot(2, 3, 4)
        plt.plot(avg_utilization.index, avg_utilization.values, linewidth=2, color='green')
        plt.xlabel('Time (ms)')
        plt.ylabel('Average Utilization (%)')
        plt.title('Average Queue Utilization')
        plt.grid(True, alpha=0.3)
        
        # Plot 5: Maximum utilization
        plt.subplot(2, 3, 5)
        plt.plot(max_utilization.index, max_utilization.values, linewidth=2, color='purple')
        plt.xlabel('Time (ms)')
        plt.ylabel('Max Utilization (%)')
        plt.title('Maximum Queue Utilization')
        plt.grid(True, alpha=0.3)
        
        # Plot 6: Number of active queues
        plt.subplot(2, 3, 6)
        plt.plot(active_queues.index, active_queues.values, linewidth=2, color='brown')
        plt.xlabel('Time (ms)')
        plt.ylabel('Number of Active Queues')
        plt.title('Active Queues Over Time')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('network_congestion.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_queue_evolution(self):
        """Plot queue size evolution (min, max, current) for sample queues"""
        plt.figure(figsize=(15, 10))
        
        # Sample queues for visibility
        sample_queues = self.parsed_data['queue_id'].unique()[::25]
        
        for i, queue_id in enumerate(sample_queues[:4]):  # Show first 4 queues
            queue_data = self.parsed_data[self.parsed_data['queue_id'] == queue_id]
            
            plt.subplot(2, 2, i+1)
            plt.plot(queue_data['time_ms'], queue_data['min_q_kb'], 
                    alpha=0.7, linewidth=1, label='Min Queue', color='blue')
            plt.plot(queue_data['time_ms'], queue_data['last_q_kb'], 
                    alpha=0.8, linewidth=2, label='Current Queue', color='red')
            plt.plot(queue_data['time_ms'], queue_data['max_q_kb'], 
                    alpha=0.7, linewidth=1, label='Max Queue', color='green')
            
            plt.fill_between(queue_data['time_ms'], queue_data['min_q_kb'], 
                           queue_data['max_q_kb'], alpha=0.2, color='gray')
            
            plt.xlabel('Time (ms)')
            plt.ylabel('Queue Size (KB)')
            plt.title(f'Queue {queue_id} Evolution')
            plt.legend()
            plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('queue_evolution.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_summary_report(self):
        """Generate a summary report of the analysis"""
        print("\n" + "="*60)
        print("NETWORK SWITCH LOG ANALYSIS SUMMARY")
        print("="*60)
        
        if self.parsed_data is not None:
            print(f"Total Records: {len(self.parsed_data):,}")
            print(f"Unique Queues: {self.parsed_data['queue_id'].nunique():,}")
            print(f"Time Range: {self.parsed_data['time_ms'].min():.3f} - {self.parsed_data['time_ms'].max():.3f} ms")
            print(f"Duration: {self.parsed_data['time_ms'].max() - self.parsed_data['time_ms'].min():.3f} ms")
            
            # Queue size statistics
            last_q = self.parsed_data['last_q_kb']
            max_q = self.parsed_data['max_q_kb']
            utilization = self.parsed_data['utilization']
            
            print(f"\nQueue Size Statistics:")
            print(f"  Max Last Queue: {last_q.max():.2f} KB")
            print(f"  Mean Last Queue: {last_q[last_q > 0].mean():.2f} KB")
            print(f"  Max Queue Capacity: {max_q.max():.2f} KB")
            print(f"  Mean Queue Capacity: {max_q[max_q > 0].mean():.2f} KB")
            print(f"  Queues with data: {len(last_q[last_q > 0])} / {len(last_q)}")
            
            # Utilization statistics
            print(f"\nQueue Utilization Statistics:")
            print(f"  Max Utilization: {utilization.max():.2f}%")
            print(f"  Mean Utilization: {utilization[utilization > 0].mean():.2f}%")
            print(f"  Queues with utilization: {len(utilization[utilization > 0])} / {len(utilization)}")
            
            # Congestion analysis
            high_util_queues = len(utilization[utilization > 80])
            print(f"\nCongestion Analysis:")
            print(f"  Queues with >80% utilization: {high_util_queues}")
            print(f"  Congestion rate: {high_util_queues/len(utilization)*100:.2f}%")
        
        if self.queue_data is not None:
            print(f"\nTop 10 Most Congested Queues (by max utilization):")
            top_queues = self.queue_data.nlargest(10, 'utilization_max')
            for idx, row in top_queues.iterrows():
                name = row.get('object_name', f'Queue {idx}')
                print(f"  {name}: {row['utilization_max']:.2f}% max, {row['last_q_kb_max']:.2f} KB max")
        
        print("\n" + "="*60)
    
    def run_analysis(self):
        """Run the complete analysis"""
        print("Starting Network Switch Log Analysis")
        print("="*50)
        
        # Parse the log file
        if not self.parse_log_file():
            return False
        
        # Load object mappings
        self.load_object_mappings()
        
        # Analyze the data
        self.analyze_queue_data()
        
        # Generate plots
        print("\nGenerating plots...")
        self.plot_queue_occupancy_over_time()
        self.plot_queue_heatmap()
        self.plot_queue_utilization()
        self.plot_queue_distributions()
        self.plot_network_congestion()
        self.plot_queue_evolution()
        
        # Generate summary report
        self.generate_summary_report()
        
        print("\nAnalysis complete! Check the generated PNG files for visualizations.")
        return True

def main():
    parser = argparse.ArgumentParser(description='Analyze network switch logs from csg-htsim')
    parser.add_argument('log_file', nargs='?', 
                       default='../small_allreduce_extended_switch.log',
                       help='Path to the switch log file to analyze')
    
    args = parser.parse_args()
    
    # Check if log file exists
    if not os.path.exists(args.log_file):
        print(f"Error: Log file '{args.log_file}' not found")
        return 1
    
    # Create analyzer and run analysis
    analyzer = SwitchLogAnalyzer(args.log_file)
    success = analyzer.run_analysis()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
