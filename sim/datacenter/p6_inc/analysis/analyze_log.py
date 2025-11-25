#!/usr/bin/env python3
"""
Network Simulation Log Analyzer
Analyzes NDP sink logs from csg-htsim network simulation and generates visualization plots.

Usage: python analyze_log.py [log_file_path]
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

class LogAnalyzer:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.parsed_data = None
        self.object_mappings = {}
        self.sink_data = None
        
    def parse_log_file(self):
        """Parse the binary log file using parse_output tool"""
        print("Parsing log file...")
        
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
                        except (ValueError, IndexError) as e:
                            # Try alternative parsing for different format
                            try:
                                timestamp = float(parts[0])
                                sink_id = int(parts[4])
                                cack = int(parts[7])
                                reorder_buffer = 0
                                rate = 0
                                
                                # Look for rate and reorder buffer in the line
                                for i, part in enumerate(parts):
                                    if part == "Rate" and i + 1 < len(parts):
                                        rate = int(parts[i + 1])
                                    elif part == "ReorderBuffer" and i + 1 < len(parts):
                                        reorder_buffer = int(parts[i + 1])
                                
                                data.append({
                                    'timestamp': timestamp,
                                    'sink_id': sink_id,
                                    'cack': cack,
                                    'reorder_buffer': reorder_buffer,
                                    'rate': rate
                                })
                            except (ValueError, IndexError):
                                continue
                    elif len(parts) >= 8 and "NDP_SINK" in line:
                        # Handle cases where format might be slightly different
                        try:
                            timestamp = float(parts[0])
                            sink_id = int(parts[4])
                            cack = int(parts[7])
                            reorder_buffer = 0
                            rate = 0
                            
                            # Look for rate and reorder buffer in the line
                            for i, part in enumerate(parts):
                                if part == "Rate" and i + 1 < len(parts):
                                    rate = int(parts[i + 1])
                                elif part == "ReorderBuffer" and i + 1 < len(parts):
                                    reorder_buffer = int(parts[i + 1])
                            
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
                    if line.startswith(': ndp_sink_'):
                        # Parse: : ndp_sink_X_Y=ID
                        parts = line.split('=')
                        if len(parts) == 2:
                            name = parts[0][2:]  # Remove ': '
                            sink_id = int(parts[1])
                            self.object_mappings[sink_id] = name
                            
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
                        if line.startswith(': ndp_sink_'):
                            parts = line.split('=')
                            if len(parts) == 2:
                                name = parts[0][2:]
                                sink_id = int(parts[1])
                                self.object_mappings[sink_id] = name
            except Exception as e2:
                print(f"Warning: Could not load object mappings from binary: {e2}")
    
    def analyze_sink_data(self):
        """Analyze the sink data and compute statistics"""
        if self.parsed_data is None:
            print("Error: No parsed data available")
            return
        
        print("Analyzing sink data...")
        
        # Convert rate from bps to Gbps
        self.parsed_data['rate_gbps'] = self.parsed_data['rate'] / 1e9
        
        # Convert cack from bytes to MB
        self.parsed_data['cack_mb'] = self.parsed_data['cack'] / 1e6
        
        # Convert timestamp to milliseconds
        self.parsed_data['time_ms'] = self.parsed_data['timestamp'] * 1000
        
        # Group by sink_id for analysis
        self.sink_data = self.parsed_data.groupby('sink_id').agg({
            'rate_gbps': ['max', 'mean', 'std'],
            'cack_mb': ['max', 'mean'],
            'reorder_buffer': ['max', 'mean'],
            'time_ms': ['min', 'max']
        }).round(3)
        
        # Flatten column names
        self.sink_data.columns = ['_'.join(col).strip() for col in self.sink_data.columns]
        
        # Add object names if available
        if self.object_mappings:
            self.sink_data['object_name'] = self.sink_data.index.map(self.object_mappings)
        
        print(f"Analyzed {len(self.sink_data)} unique sinks")
    
    def plot_rate_over_time(self):
        """Plot rate over time for all sinks"""
        plt.figure(figsize=(15, 8))
        
        # Sample sinks for visibility (plot every 10th sink)
        sample_sinks = self.parsed_data['sink_id'].unique()[::10]
        
        for sink_id in sample_sinks:
            sink_data = self.parsed_data[self.parsed_data['sink_id'] == sink_id]
            plt.plot(sink_data['time_ms'], sink_data['rate_gbps'], 
                    alpha=0.7, linewidth=1, label=f'Sink {sink_id}')
        
        plt.xlabel('Time (ms)')
        plt.ylabel('Rate (Gbps)')
        plt.title('NDP Sink Rates Over Time (Sample of Sinks)')
        plt.grid(True, alpha=0.3)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig('rate_over_time.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_rate_heatmap(self):
        """Create a heatmap of rates by sink and time"""
        plt.figure(figsize=(20, 10))
        
        # Create pivot table for heatmap
        pivot_data = self.parsed_data.pivot_table(
            values='rate_gbps', 
            index='sink_id', 
            columns='time_ms', 
            fill_value=0
        )
        
        # Sample data for visibility
        sample_sinks = pivot_data.index[::20]  # Every 20th sink
        sample_times = pivot_data.columns[::5]  # Every 5th time point
        
        heatmap_data = pivot_data.loc[sample_sinks, sample_times]
        
        sns.heatmap(heatmap_data, cmap='viridis', cbar_kws={'label': 'Rate (Gbps)'})
        plt.xlabel('Time (ms)')
        plt.ylabel('Sink ID')
        plt.title('Rate Heatmap: Sink vs Time')
        plt.tight_layout()
        plt.savefig('rate_heatmap.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_cack_evolution(self):
        """Plot cumulative ACK evolution over time"""
        plt.figure(figsize=(15, 8))
        
        # Sample sinks for visibility
        sample_sinks = self.parsed_data['sink_id'].unique()[::15]
        
        for sink_id in sample_sinks:
            sink_data = self.parsed_data[self.parsed_data['sink_id'] == sink_id]
            if sink_data['cack_mb'].max() > 0:  # Only plot sinks with data
                plt.plot(sink_data['time_ms'], sink_data['cack_mb'], 
                        alpha=0.8, linewidth=2, label=f'Sink {sink_id}')
        
        plt.xlabel('Time (ms)')
        plt.ylabel('Cumulative ACK (MB)')
        plt.title('Cumulative ACK Evolution Over Time')
        plt.grid(True, alpha=0.3)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig('cack_evolution.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_rate_distribution(self):
        """Plot distribution of rates"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Overall rate distribution
        rates = self.parsed_data['rate_gbps']
        axes[0, 0].hist(rates[rates > 0], bins=50, alpha=0.7, edgecolor='black')
        axes[0, 0].set_xlabel('Rate (Gbps)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].set_title('Rate Distribution (Non-zero rates)')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Rate distribution by time
        time_bins = np.linspace(self.parsed_data['time_ms'].min(), 
                               self.parsed_data['time_ms'].max(), 10)
        for i in range(len(time_bins)-1):
            time_data = self.parsed_data[
                (self.parsed_data['time_ms'] >= time_bins[i]) & 
                (self.parsed_data['time_ms'] < time_bins[i+1])
            ]
            if len(time_data) > 0:
                axes[0, 1].hist(time_data['rate_gbps'][time_data['rate_gbps'] > 0], 
                               bins=20, alpha=0.5, 
                               label=f'{time_bins[i]:.2f}-{time_bins[i+1]:.2f}ms')
        axes[0, 1].set_xlabel('Rate (Gbps)')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title('Rate Distribution by Time Window')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Box plot of rates by sink (top 20 most active sinks)
        top_sinks = self.parsed_data.groupby('sink_id')['rate_gbps'].max().nlargest(20).index
        top_sink_data = self.parsed_data[self.parsed_data['sink_id'].isin(top_sinks)]
        sns.boxplot(data=top_sink_data, x='sink_id', y='rate_gbps', ax=axes[1, 0])
        axes[1, 0].set_xlabel('Sink ID')
        axes[1, 0].set_ylabel('Rate (Gbps)')
        axes[1, 0].set_title('Rate Distribution by Top 20 Most Active Sinks')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Reorder buffer distribution
        reorder_data = self.parsed_data['reorder_buffer']
        axes[1, 1].hist(reorder_data, bins=20, alpha=0.7, edgecolor='black')
        axes[1, 1].set_xlabel('Reorder Buffer Size')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].set_title('Reorder Buffer Distribution')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('rate_distributions.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_network_utilization(self):
        """Plot network utilization metrics"""
        plt.figure(figsize=(15, 10))
        
        # Calculate utilization over time
        time_groups = self.parsed_data.groupby('time_ms')
        
        total_utilization = time_groups['rate_gbps'].sum()
        active_sinks = time_groups['rate_gbps'].apply(lambda x: (x > 0).sum())
        avg_rate = time_groups['rate_gbps'].mean()
        max_rate = time_groups['rate_gbps'].max()
        
        # Plot 1: Total network utilization
        plt.subplot(2, 2, 1)
        plt.plot(total_utilization.index, total_utilization.values, linewidth=2)
        plt.xlabel('Time (ms)')
        plt.ylabel('Total Rate (Gbps)')
        plt.title('Total Network Utilization')
        plt.grid(True, alpha=0.3)
        
        # Plot 2: Number of active sinks
        plt.subplot(2, 2, 2)
        plt.plot(active_sinks.index, active_sinks.values, linewidth=2, color='orange')
        plt.xlabel('Time (ms)')
        plt.ylabel('Number of Active Sinks')
        plt.title('Active Sinks Over Time')
        plt.grid(True, alpha=0.3)
        
        # Plot 3: Average rate per sink
        plt.subplot(2, 2, 3)
        plt.plot(avg_rate.index, avg_rate.values, linewidth=2, color='green')
        plt.xlabel('Time (ms)')
        plt.ylabel('Average Rate per Sink (Gbps)')
        plt.title('Average Rate per Sink')
        plt.grid(True, alpha=0.3)
        
        # Plot 4: Maximum rate
        plt.subplot(2, 2, 4)
        plt.plot(max_rate.index, max_rate.values, linewidth=2, color='red')
        plt.xlabel('Time (ms)')
        plt.ylabel('Maximum Rate (Gbps)')
        plt.title('Maximum Rate Over Time')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('network_utilization.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_summary_report(self):
        """Generate a summary report of the analysis"""
        print("\n" + "="*60)
        print("NETWORK SIMULATION ANALYSIS SUMMARY")
        print("="*60)
        
        if self.parsed_data is not None:
            print(f"Total Records: {len(self.parsed_data):,}")
            print(f"Unique Sinks: {self.parsed_data['sink_id'].nunique():,}")
            print(f"Time Range: {self.parsed_data['time_ms'].min():.3f} - {self.parsed_data['time_ms'].max():.3f} ms")
            print(f"Duration: {self.parsed_data['time_ms'].max() - self.parsed_data['time_ms'].min():.3f} ms")
            
            # Rate statistics
            rates = self.parsed_data['rate_gbps']
            non_zero_rates = rates[rates > 0]
            print(f"\nRate Statistics:")
            print(f"  Max Rate: {rates.max():.2f} Gbps")
            print(f"  Mean Rate (non-zero): {non_zero_rates.mean():.2f} Gbps")
            print(f"  Std Rate (non-zero): {non_zero_rates.std():.2f} Gbps")
            print(f"  Sinks with non-zero rate: {len(non_zero_rates)} / {len(rates)}")
            
            # CAck statistics
            cacks = self.parsed_data['cack_mb']
            non_zero_cacks = cacks[cacks > 0]
            print(f"\nCumulative ACK Statistics:")
            print(f"  Max CAck: {cacks.max():.2f} MB")
            print(f"  Mean CAck (non-zero): {non_zero_cacks.mean():.2f} MB")
            print(f"  Sinks with data: {len(non_zero_cacks)} / {len(cacks)}")
            
            # Reorder buffer statistics
            reorder = self.parsed_data['reorder_buffer']
            print(f"\nReorder Buffer Statistics:")
            print(f"  Max Reorder Buffer: {reorder.max()}")
            print(f"  Mean Reorder Buffer: {reorder.mean():.2f}")
            print(f"  Sinks with reordering: {(reorder > 0).sum()}")
        
        if self.sink_data is not None:
            print(f"\nTop 10 Most Active Sinks (by max rate):")
            top_sinks = self.sink_data.nlargest(10, 'rate_gbps_max')
            for idx, row in top_sinks.iterrows():
                name = row.get('object_name', f'Sink {idx}')
                print(f"  {name}: {row['rate_gbps_max']:.2f} Gbps max, {row['cack_mb_max']:.2f} MB total")
        
        print("\n" + "="*60)
    
    def run_analysis(self):
        """Run the complete analysis"""
        print("Starting Network Simulation Log Analysis")
        print("="*50)
        
        # Parse the log file
        if not self.parse_log_file():
            return False
        
        # Load object mappings
        self.load_object_mappings()
        
        # Analyze the data
        self.analyze_sink_data()
        
        # Generate plots
        print("\nGenerating plots...")
        self.plot_rate_over_time()
        self.plot_rate_heatmap()
        self.plot_cack_evolution()
        self.plot_rate_distribution()
        self.plot_network_utilization()
        
        # Generate summary report
        self.generate_summary_report()
        
        print("\nAnalysis complete! Check the generated PNG files for visualizations.")
        return True

def main():
    parser = argparse.ArgumentParser(description='Analyze NDP sink logs from csg-htsim')
    parser.add_argument('log_file', nargs='?', 
                       default='../small_allreduce_extended.log',
                       help='Path to the log file to analyze')
    
    args = parser.parse_args()
    
    # Check if log file exists
    if not os.path.exists(args.log_file):
        print(f"Error: Log file '{args.log_file}' not found")
        return 1
    
    # Create analyzer and run analysis
    analyzer = LogAnalyzer(args.log_file)
    success = analyzer.run_analysis()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
