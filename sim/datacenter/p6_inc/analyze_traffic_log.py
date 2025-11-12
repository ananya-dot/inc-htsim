#!/usr/bin/env python3
"""
Network Traffic Log Analyzer
Analyzes packet-level traffic logs from csg-htsim network simulation and generates visualization plots.

This analyzer processes TRAFFIC events (packet creation, send, receive, drop, etc.) and provides:
- Packet flow statistics (arrivals, departures, drops)
- Event type distribution
- Flow-level analysis
- Time-series visualizations
- Packet lifecycle tracking

Usage: python analyze_traffic_log.py [log_file_path]
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

class TrafficLogAnalyzer:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.parsed_data = None
        self.object_mappings = {}
        self.traffic_data = None
        
    def parse_log_file(self):
        """Parse the binary log file using parse_output tool"""
        print("Parsing traffic log file...")
        
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
                    # Format: timestamp Type TRAFFIC ID <id> Ev <event> FlowID <flow_id> PktID <pkt_id>
                    # Optional: Ptype <type> Seqno/Ackno <num> flag <flag> Psize <size>
                    if len(parts) >= 8 and parts[1] == "Type" and parts[2] == "TRAFFIC":
                        try:
                            timestamp = float(parts[0])
                            location_id = int(parts[4])
                            
                            # Find event type
                            event_type = None
                            flow_id = None
                            pkt_id = None
                            ptype = None
                            seqno_ackno = None
                            flags = []
                            psize = None
                            
                            i = 5
                            while i < len(parts):
                                if parts[i] == "Ev" and i + 1 < len(parts):
                                    event_type = parts[i + 1]
                                    i += 2
                                elif parts[i] == "FlowID" and i + 1 < len(parts):
                                    flow_id = int(parts[i + 1])
                                    i += 2
                                elif parts[i] == "PktID" and i + 1 < len(parts):
                                    pkt_id = int(parts[i + 1])
                                    i += 2
                                elif parts[i] == "Ptype" and i + 1 < len(parts):
                                    ptype = parts[i + 1]
                                    i += 2
                                elif parts[i] in ["Seqno", "Ackno"] and i + 1 < len(parts):
                                    seqno_ackno = int(parts[i + 1])
                                    i += 2
                                elif parts[i] == "flag" and i + 1 < len(parts):
                                    flags.append(parts[i + 1])
                                    i += 2
                                elif parts[i] == "Psize" and i + 1 < len(parts):
                                    psize = parts[i + 1]
                                    i += 2
                                else:
                                    i += 1
                            
                            if event_type and flow_id is not None and pkt_id is not None:
                                data.append({
                                    'timestamp': timestamp,
                                    'location_id': location_id,
                                    'event_type': event_type,
                                    'flow_id': flow_id,
                                    'pkt_id': pkt_id,
                                    'ptype': ptype,
                                    'seqno_ackno': seqno_ackno,
                                    'flags': ','.join(flags) if flags else None,
                                    'psize': psize
                                })
                        except (ValueError, IndexError) as e:
                            continue
                    # Also handle NDPTRAFFIC format if present
                    elif len(parts) >= 8 and parts[1] == "Type" and parts[2] == "NDPTRAFFIC":
                        try:
                            timestamp = float(parts[0])
                            location_id = int(parts[4])
                            
                            event_type = None
                            flow_id = None
                            ptype = None
                            seqno_ackno = None
                            flags = []
                            psize = None
                            
                            i = 5
                            while i < len(parts):
                                if parts[i] == "Ev" and i + 1 < len(parts):
                                    event_type = parts[i + 1]
                                    i += 2
                                elif parts[i] == "FlowID" and i + 1 < len(parts):
                                    flow_id = int(parts[i + 1])
                                    i += 2
                                elif parts[i] == "Ptype" and i + 1 < len(parts):
                                    ptype = parts[i + 1]
                                    i += 2
                                    # Next should be Seqno or Ackno
                                    if i < len(parts) and parts[i] in ["Seqno", "Ackno"]:
                                        seqno_ackno = int(parts[i + 1])
                                        i += 2
                                elif parts[i] == "flag" and i + 1 < len(parts):
                                    flags.append(parts[i + 1])
                                    i += 2
                                elif parts[i] == "Psize" and i + 1 < len(parts):
                                    psize = parts[i + 1]
                                    i += 2
                                else:
                                    i += 1
                            
                            if event_type and flow_id is not None:
                                # For NDPTRAFFIC, we might not have PktID, use seqno/ackno as identifier
                                data.append({
                                    'timestamp': timestamp,
                                    'location_id': location_id,
                                    'event_type': event_type,
                                    'flow_id': flow_id,
                                    'pkt_id': seqno_ackno if seqno_ackno is not None else 0,
                                    'ptype': ptype,
                                    'seqno_ackno': seqno_ackno,
                                    'flags': ','.join(flags) if flags else None,
                                    'psize': psize
                                })
                        except (ValueError, IndexError) as e:
                            continue
            
            if not data:
                print("No valid traffic data found in log file")
                return False
                
            self.traffic_data = pd.DataFrame(data)
            print(f"Parsed {len(self.traffic_data)} traffic events")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error running parse_output: {e}")
            print(f"stderr: {e.stderr}")
            return False
        except Exception as e:
            print(f"Error parsing log: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def analyze_events(self):
        """Perform statistical analysis on traffic events"""
        if self.traffic_data is None or len(self.traffic_data) == 0:
            print("No data to analyze")
            return
        
        print("\n=== Traffic Event Analysis ===")
        print(f"Total events: {len(self.traffic_data)}")
        print(f"Time range: {self.traffic_data['timestamp'].min():.6f} - {self.traffic_data['timestamp'].max():.6f} seconds")
        print(f"Duration: {self.traffic_data['timestamp'].max() - self.traffic_data['timestamp'].min():.6f} seconds")
        
        # Event type distribution
        print("\nEvent type distribution:")
        event_counts = self.traffic_data['event_type'].value_counts()
        for event, count in event_counts.items():
            print(f"  {event}: {count} ({count/len(self.traffic_data)*100:.2f}%)")
        
        # Flow statistics
        print(f"\nUnique flows: {self.traffic_data['flow_id'].nunique()}")
        print(f"Unique locations: {self.traffic_data['location_id'].nunique()}")
        print(f"Unique packets: {self.traffic_data['pkt_id'].nunique()}")
        
        # Packet type distribution (if available)
        if self.traffic_data['ptype'].notna().any():
            print("\nPacket type distribution:")
            ptype_counts = self.traffic_data['ptype'].value_counts()
            for ptype, count in ptype_counts.items():
                print(f"  {ptype}: {count} ({count/len(self.traffic_data)*100:.2f}%)")
        
        # Event rate analysis
        time_bins = pd.cut(self.traffic_data['timestamp'], bins=100)
        event_rate = self.traffic_data.groupby(time_bins, observed=True).size()
        print(f"\nAverage event rate: {len(self.traffic_data) / (self.traffic_data['timestamp'].max() - self.traffic_data['timestamp'].min()):.2f} events/second")
        print(f"Peak event rate: {event_rate.max():.0f} events/bin")
    
    def generate_plots(self, output_dir="."):
        """Generate visualization plots"""
        if self.traffic_data is None or len(self.traffic_data) == 0:
            print("No data to plot")
            return
        
        print("\nGenerating plots...")
        output_path = Path(output_dir)
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 6)
        
        # 1. Event type distribution
        plt.figure()
        event_counts = self.traffic_data['event_type'].value_counts()
        plt.bar(event_counts.index, event_counts.values)
        plt.xlabel('Event Type')
        plt.ylabel('Count')
        plt.title('Traffic Event Type Distribution')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path / 'traffic_event_distribution.png', dpi=300)
        plt.close()
        print(f"  Saved: traffic_event_distribution.png")
        
        # 2. Events over time
        try:
            plt.figure()
            time_bins = pd.cut(self.traffic_data['timestamp'], bins=100)
            event_counts_time = self.traffic_data.groupby(time_bins).size()
            bin_centers = [interval.mid for interval in event_counts_time.index]
            plt.plot(bin_centers, event_counts_time.values, linewidth=1.5)
            plt.xlabel('Time (seconds)')
            plt.ylabel('Event Count')
            plt.title('Traffic Events Over Time')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(output_path / 'traffic_events_over_time.png', dpi=300)
            plt.close()
            print(f"  Saved: traffic_events_over_time.png")
        except Exception as e:
            print(f"  Warning: Could not create events over time plot: {e}")
        
        # 3. Event type over time (heatmap)
        try:
            plt.figure(figsize=(14, 8))
            time_bins = pd.cut(self.traffic_data['timestamp'], bins=50)
            event_time_dist = pd.crosstab(time_bins, self.traffic_data['event_type'])
            bin_centers = [interval.mid for interval in event_time_dist.index]
            sns.heatmap(event_time_dist.T, xticklabels=[f'{t:.4f}' for t in bin_centers[::max(1, len(bin_centers)//10)]],
                       yticklabels=True, cmap='YlOrRd', cbar_kws={'label': 'Event Count'})
            plt.xlabel('Time (seconds)')
            plt.ylabel('Event Type')
            plt.title('Traffic Event Type Distribution Over Time')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(output_path / 'traffic_event_heatmap.png', dpi=300)
            plt.close()
            print(f"  Saved: traffic_event_heatmap.png")
        except Exception as e:
            print(f"  Warning: Could not create event heatmap: {e}")
        
        # 4. Flow activity (top flows)
        try:
            plt.figure(figsize=(12, 8))
            flow_counts = self.traffic_data['flow_id'].value_counts().head(20)
            plt.barh(range(len(flow_counts)), flow_counts.values)
            plt.yticks(range(len(flow_counts)), [f'Flow {fid}' for fid in flow_counts.index])
            plt.xlabel('Event Count')
            plt.ylabel('Flow ID')
            plt.title('Top 20 Most Active Flows')
            plt.tight_layout()
            plt.savefig(output_path / 'traffic_top_flows.png', dpi=300)
            plt.close()
            print(f"  Saved: traffic_top_flows.png")
        except Exception as e:
            print(f"  Warning: Could not create top flows plot: {e}")
        
        # 5. Packet type distribution (if available)
        if self.traffic_data['ptype'].notna().any():
            try:
                plt.figure()
                ptype_counts = self.traffic_data['ptype'].value_counts()
                plt.pie(ptype_counts.values, labels=ptype_counts.index, autopct='%1.1f%%', startangle=90)
                plt.title('Packet Type Distribution')
                plt.tight_layout()
                plt.savefig(output_path / 'traffic_packet_type_distribution.png', dpi=300)
                plt.close()
                print(f"  Saved: traffic_packet_type_distribution.png")
            except Exception as e:
                print(f"  Warning: Could not create packet type plot: {e}")
        
        # 6. Event rate by type over time
        try:
            plt.figure(figsize=(14, 8))
            time_bins = pd.cut(self.traffic_data['timestamp'], bins=100)
            for event_type in self.traffic_data['event_type'].unique()[:5]:  # Top 5 event types
                event_data = self.traffic_data[self.traffic_data['event_type'] == event_type]
                if len(event_data) > 0:
                    event_counts = event_data.groupby(time_bins).size()
                    bin_centers = [interval.mid for interval in event_counts.index]
                    plt.plot(bin_centers, event_counts.values, label=event_type, linewidth=1.5, alpha=0.7)
            plt.xlabel('Time (seconds)')
            plt.ylabel('Event Count per Bin')
            plt.title('Event Rate by Type Over Time')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(output_path / 'traffic_event_rate_by_type.png', dpi=300)
            plt.close()
            print(f"  Saved: traffic_event_rate_by_type.png")
        except Exception as e:
            print(f"  Warning: Could not create event rate by type plot: {e}")
        
        # 7. Location activity (top locations)
        try:
            plt.figure(figsize=(12, 8))
            location_counts = self.traffic_data['location_id'].value_counts().head(20)
            plt.barh(range(len(location_counts)), location_counts.values)
            plt.yticks(range(len(location_counts)), [f'Location {lid}' for lid in location_counts.index])
            plt.xlabel('Event Count')
            plt.ylabel('Location ID')
            plt.title('Top 20 Most Active Locations')
            plt.tight_layout()
            plt.savefig(output_path / 'traffic_top_locations.png', dpi=300)
            plt.close()
            print(f"  Saved: traffic_top_locations.png")
        except Exception as e:
            print(f"  Warning: Could not create top locations plot: {e}")
        
        print("\nAll plots generated successfully!")
    
    def export_summary(self, output_file="traffic_analysis_summary.txt"):
        """Export analysis summary to text file"""
        if self.traffic_data is None or len(self.traffic_data) == 0:
            return
        
        with open(output_file, 'w') as f:
            f.write("=== Traffic Log Analysis Summary ===\n\n")
            f.write(f"Total events: {len(self.traffic_data)}\n")
            f.write(f"Time range: {self.traffic_data['timestamp'].min():.6f} - {self.traffic_data['timestamp'].max():.6f} seconds\n")
            f.write(f"Duration: {self.traffic_data['timestamp'].max() - self.traffic_data['timestamp'].min():.6f} seconds\n\n")
            
            f.write("Event type distribution:\n")
            event_counts = self.traffic_data['event_type'].value_counts()
            for event, count in event_counts.items():
                f.write(f"  {event}: {count} ({count/len(self.traffic_data)*100:.2f}%)\n")
            
            f.write(f"\nUnique flows: {self.traffic_data['flow_id'].nunique()}\n")
            f.write(f"Unique locations: {self.traffic_data['location_id'].nunique()}\n")
            f.write(f"Unique packets: {self.traffic_data['pkt_id'].nunique()}\n")
            
            if self.traffic_data['ptype'].notna().any():
                f.write("\nPacket type distribution:\n")
                ptype_counts = self.traffic_data['ptype'].value_counts()
                for ptype, count in ptype_counts.items():
                    f.write(f"  {ptype}: {count} ({count/len(self.traffic_data)*100:.2f}%)\n")
        
        print(f"Summary exported to {output_file}")
    
    def export_flow_paths(self, output_file="flow_paths.txt"):
        """Export flow paths: For each flow, list all switches it goes through with timestamps"""
        if self.traffic_data is None or len(self.traffic_data) == 0:
            print("No data to export")
            return
        
        print("\nGenerating flow paths...")
        
        # Filter for ARRIVE and DEPART events only
        switch_events = self.traffic_data[
            self.traffic_data['event_type'].isin(['ARRIVE', 'DEPART'])
        ].copy()
        
        if len(switch_events) == 0:
            print("No ARRIVE/DEPART events found")
            return
        
        # Sort by flow_id, then timestamp
        switch_events = switch_events.sort_values(['flow_id', 'timestamp', 'location_id'])
        
        # Group by flow_id and build paths
        flow_paths = {}
        
        for flow_id in switch_events['flow_id'].unique():
            flow_data = switch_events[switch_events['flow_id'] == flow_id].copy()
            flow_data = flow_data.sort_values('timestamp')
            
            # Track path: list of (location_id, arrival_time, departure_time, dwell_time)
            path = []
            current_location = None
            arrival_time = None
            
            for _, row in flow_data.iterrows():
                location_id = row['location_id']
                timestamp = row['timestamp']
                event_type = row['event_type']
                
                if event_type == 'ARRIVE':
                    # If we have a previous location, record its departure
                    if current_location is not None and arrival_time is not None:
                        dwell_time = timestamp - arrival_time
                        path.append((current_location, arrival_time, timestamp, dwell_time))
                    
                    # Start new location visit
                    current_location = location_id
                    arrival_time = timestamp
                
                elif event_type == 'DEPART':
                    if current_location == location_id and arrival_time is not None:
                        dwell_time = timestamp - arrival_time
                        path.append((location_id, arrival_time, timestamp, dwell_time))
                        current_location = None
                        arrival_time = None
            
            # Handle case where flow ends at a location (ARRIVE without DEPART)
            if current_location is not None and arrival_time is not None:
                # Use last timestamp as departure
                last_time = flow_data['timestamp'].max()
                dwell_time = last_time - arrival_time
                path.append((current_location, arrival_time, last_time, dwell_time))
            
            if path:
                flow_paths[flow_id] = path
        
        # Write to file
        with open(output_file, 'w') as f:
            f.write("=== Flow Paths Through Switches ===\n")
            f.write("Format: FlowID -> SwitchID (Arrival_Time, Departure_Time, Dwell_Time_seconds)\n\n")
            
            for flow_id in sorted(flow_paths.keys()):
                f.write(f"Flow {flow_id}:\n")
                path = flow_paths[flow_id]
                
                for i, (switch_id, arrive, depart, dwell) in enumerate(path):
                    f.write(f"  {i+1}. Switch {switch_id}: ")
                    f.write(f"Arrive={arrive:.9f}s, Depart={depart:.9f}s, Dwell={dwell:.9f}s")
                    f.write(f" ({dwell*1e6:.3f}μs)\n")
                
                # Summary line
                total_switches = len(path)
                total_time = path[-1][2] - path[0][1] if path else 0
                total_dwell = sum(dwell for _, _, _, dwell in path)
                f.write(f"  Summary: {total_switches} switches, Total time: {total_time:.9f}s, Total dwell: {total_dwell:.9f}s\n\n")
        
        print(f"  Exported {len(flow_paths)} flow paths to {output_file}")
    
    def export_switch_occupancy(self, output_file="switch_occupancy.txt"):
        """Export switch occupancy: For each switch, list flows present at different timestamps"""
        if self.traffic_data is None or len(self.traffic_data) == 0:
            print("No data to export")
            return
        
        print("\nGenerating switch occupancy...")
        
        # Filter for ARRIVE and DEPART events only
        switch_events = self.traffic_data[
            self.traffic_data['event_type'].isin(['ARRIVE', 'DEPART'])
        ].copy()
        
        if len(switch_events) == 0:
            print("No ARRIVE/DEPART events found")
            return
        
        # Sort by location_id, then timestamp
        switch_events = switch_events.sort_values(['location_id', 'timestamp'])
        
        # Group by location_id
        switch_occupancy = {}
        
        for location_id in switch_events['location_id'].unique():
            location_data = switch_events[switch_events['location_id'] == location_id].copy()
            location_data = location_data.sort_values('timestamp')
            
            # Track active flows at each timestamp
            occupancy = []
            active_flows = set()  # Set of (flow_id, pkt_id) tuples currently at this switch
            
            for _, row in location_data.iterrows():
                timestamp = row['timestamp']
                flow_id = row['flow_id']
                pkt_id = row['pkt_id']
                event_type = row['event_type']
                flow_key = (flow_id, pkt_id)
                
                if event_type == 'ARRIVE':
                    active_flows.add(flow_key)
                elif event_type == 'DEPART':
                    active_flows.discard(flow_key)
                
                # Record state at this timestamp
                occupancy.append({
                    'timestamp': timestamp,
                    'active_flows': active_flows.copy(),
                    'flow_count': len(active_flows),
                    'event_type': event_type,
                    'flow_id': flow_id,
                    'pkt_id': pkt_id
                })
            
            switch_occupancy[location_id] = occupancy
        
        # Write to file
        with open(output_file, 'w') as f:
            f.write("=== Switch Occupancy by Time ===\n")
            f.write("Format: SwitchID -> Timestamp: [List of flows (FlowID, PktID)]\n\n")
            
            for location_id in sorted(switch_occupancy.keys()):
                f.write(f"Switch {location_id}:\n")
                occupancy = switch_occupancy[location_id]
                
                # Group consecutive timestamps with same active flows
                i = 0
                while i < len(occupancy):
                    current_flows = occupancy[i]['active_flows']
                    start_time = occupancy[i]['timestamp']
                    
                    # Find end of this period (same active flows)
                    end_time = start_time
                    j = i + 1
                    while j < len(occupancy) and occupancy[j]['active_flows'] == current_flows:
                        end_time = occupancy[j]['timestamp']
                        j += 1
                    
                    # Write this period
                    if current_flows:
                        flow_list = sorted([f"Flow{fid}_Pkt{pkt}" for fid, pkt in current_flows])
                        f.write(f"  [{start_time:.9f}s - {end_time:.9f}s]: {len(current_flows)} flows - {', '.join(flow_list)}\n")
                    else:
                        f.write(f"  [{start_time:.9f}s - {end_time:.9f}s]: 0 flows (empty)\n")
                    
                    i = j
                
                # Summary
                total_events = len(occupancy)
                unique_flows = set()
                for occ in occupancy:
                    unique_flows.update([fid for fid, _ in occ['active_flows']])
                max_concurrent = max(occ['flow_count'] for occ in occupancy) if occupancy else 0
                
                f.write(f"  Summary: {total_events} events, {len(unique_flows)} unique flows, Max concurrent: {max_concurrent}\n\n")
        
        print(f"  Exported occupancy for {len(switch_occupancy)} switches to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Analyze network traffic logs')
    parser.add_argument('log_file', nargs='?', default='intraffic.log',
                       help='Path to traffic log file (default: intraffic.log)')
    parser.add_argument('-o', '--output', default='.',
                       help='Output directory for plots (default: current directory)')
    parser.add_argument('--no-plots', action='store_true',
                       help='Skip generating plots')
    parser.add_argument('--summary', action='store_true',
                       help='Export summary to text file')
    parser.add_argument('--no-flow-paths', action='store_true',
                       help='Skip exporting flow paths')
    parser.add_argument('--no-switch-occupancy', action='store_true',
                       help='Skip exporting switch occupancy')
    parser.add_argument('--all-exports', action='store_true',
                       help='Export all text files (summary, flow paths, switch occupancy)')
    
    args = parser.parse_args()
    
    # Check if log file exists
    if not os.path.exists(args.log_file):
        print(f"Error: Log file not found: {args.log_file}")
        sys.exit(1)
    
    # Create analyzer
    analyzer = TrafficLogAnalyzer(args.log_file)
    
    # Parse log file
    if not analyzer.parse_log_file():
        print("Failed to parse log file")
        sys.exit(1)
    
    # Perform analysis
    analyzer.analyze_events()
    
    # Generate plots
    if not args.no_plots:
        analyzer.generate_plots(args.output)
    
    # Export summary
    if args.summary or args.all_exports:
        analyzer.export_summary(os.path.join(args.output, 'traffic_analysis_summary.txt'))
    
    # Export flow paths (always enabled by default)
    if not args.no_flow_paths:
        analyzer.export_flow_paths(os.path.join(args.output, 'flow_paths.txt'))
    
    # Export switch occupancy (always enabled by default)
    if not args.no_switch_occupancy:
        analyzer.export_switch_occupancy(os.path.join(args.output, 'switch_occupancy.txt'))
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()
