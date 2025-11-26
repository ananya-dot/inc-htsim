#!/usr/bin/env python3
"""
EQDS Traffic Log Analyzer
Parses EQDS log files using parse_output tool and creates separate text files for different modes.

Usage: python analyse_eqds_traffic_logs.py [log_file_path] [output_dir]
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

class EQDSTrafficLogAnalyzer:
    def __init__(self, log_file_path, output_dir=None):
        self.log_file_path = log_file_path
        self.output_dir = output_dir or os.path.dirname(log_file_path)
        self.parse_tool = None
        
        # Find parse_output executable
        self._find_parse_output()
        
    def _find_parse_output(self):
        """Find the parse_output executable"""
        # Try different possible locations
        possible_paths = [
            "../../../parse_output",  # From p6_inc/analysis/
            "../../parse_output",      # From datacenter/analysis/
            "../parse_output",         # From sim/
            "parse_output",            # Current directory
            os.path.join(os.path.dirname(__file__), "../../../parse_output"),
        ]
        
        for path in possible_paths:
            abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), path))
            if os.path.exists(abs_path) and os.access(abs_path, os.X_OK):
                self.parse_tool = abs_path
                print(f"Found parse_output at: {self.parse_tool}")
                return
        
        # If not found, try in PATH
        import shutil
        parse_output_in_path = shutil.which("parse_output")
        if parse_output_in_path:
            self.parse_tool = parse_output_in_path
            print(f"Found parse_output in PATH: {self.parse_tool}")
            return
            
        print("Warning: parse_output not found. Please ensure it's built and in PATH.")
        self.parse_tool = "parse_output"  # Will try anyway
        
    def run_parse_output(self, mode, output_file, additional_args=None, use_filter=None):
        """Run parse_output with specified mode and save to file"""
        if not os.path.exists(self.log_file_path):
            print(f"Error: Log file not found: {self.log_file_path}")
            return False
            
        cmd = [self.parse_tool, self.log_file_path]
        
        # For text output, always use -ascii
        # For statistics output, use mode without -ascii
        if mode == "ascii" or mode == "all" or use_filter:
            cmd.append("-ascii")
            if use_filter:
                cmd.append("-filter")
                cmd.append(use_filter)
        elif mode:
            # Statistics mode - no -ascii
            cmd.append(f"-{mode}")
        
        # Add any additional arguments
        if additional_args:
            cmd.extend(additional_args)
        
        print(f"Running: {' '.join(cmd)}")
        print(f"Output: {output_file}")
        
        try:
            with open(output_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, 
                                      text=True, check=False)
            
            if result.returncode != 0:
                print(f"Warning: parse_output returned code {result.returncode}")
                if result.stderr:
                    print(f"Error output: {result.stderr[:500]}")
                return False
                
            # Check if file was created and has content
            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                print(f"  Created {output_file} ({size:,} bytes)")
                return True
            else:
                print(f"  Error: Output file was not created")
                return False
                
        except FileNotFoundError:
            print(f"Error: parse_output executable not found at {self.parse_tool}")
            return False
        except Exception as e:
            print(f"Error running parse_output: {e}")
            return False
    
    def extract_traffic_events(self, ascii_file, output_file):
        """Extract only TRAFFIC events from ASCII output"""
        print(f"Extracting TRAFFIC events from {ascii_file}...")
        
        if not os.path.exists(ascii_file):
            print(f"Error: ASCII file not found: {ascii_file}")
            return False
        
        traffic_count = 0
        try:
            with open(ascii_file, 'r') as infile, open(output_file, 'w') as outfile:
                for line in infile:
                    if "Type TRAFFIC" in line or "Type EQDSTRAFFIC" in line:
                        outfile.write(line)
                        traffic_count += 1
            
            print(f"  Extracted {traffic_count:,} TRAFFIC events to {output_file}")
            return True
        except Exception as e:
            print(f"Error extracting traffic events: {e}")
            return False
    
    def extract_by_event_type(self, ascii_file, output_dir):
        """Extract different event types into separate files"""
        print(f"Extracting events by type from {ascii_file}...")
        
        if not os.path.exists(ascii_file):
            print(f"Error: ASCII file not found: {ascii_file}")
            return False
        
        event_files = {
            "TRAFFIC": open(os.path.join(output_dir, "traffic_events.txt"), 'w'),
            "FLOW_EVENT": open(os.path.join(output_dir, "flow_events.txt"), 'w'),
            "QUEUE": open(os.path.join(output_dir, "queue_events.txt"), 'w'),
            "EQDS": open(os.path.join(output_dir, "eqds_events.txt"), 'w'),
            "EQDS_SINK": open(os.path.join(output_dir, "eqds_sink_events.txt"), 'w'),
        }
        
        counts = {key: 0 for key in event_files.keys()}
        
        try:
            with open(ascii_file, 'r') as infile:
                for line in infile:
                    written = False
                    for event_type, outfile in event_files.items():
                        if f"Type {event_type}" in line:
                            outfile.write(line)
                            counts[event_type] += 1
                            written = True
                            break
                    
                    # Also check for queue events
                    if not written and ("QUEUE_EVENT" in line or "QUEUE_APPROX" in line or "QUEUE_RECORD" in line):
                        event_files["QUEUE"].write(line)
                        counts["QUEUE"] += 1
                    # Check for EQDS events
                    elif not written and ("EQDS_EVENT" in line or "EQDS_STATE" in line or "EQDS_RECORD" in line):
                        event_files["EQDS"].write(line)
                        counts["EQDS"] += 1
                    elif not written and "EQDS_SINK" in line:
                        event_files["EQDS_SINK"].write(line)
                        counts["EQDS_SINK"] += 1
            
            # Close all files
            for outfile in event_files.values():
                outfile.close()
            
            print("  Event extraction summary:")
            for event_type, count in counts.items():
                if count > 0:
                    print(f"    {event_type}: {count:,} events")
            
            return True
        except Exception as e:
            print(f"Error extracting events by type: {e}")
            # Close files on error
            for outfile in event_files.values():
                try:
                    outfile.close()
                except:
                    pass
            return False
    
    def analyze(self):
        """Run all parsing modes and create output files"""
        print(f"\n{'='*60}")
        print(f"EQDS Traffic Log Analyzer")
        print(f"{'='*60}")
        print(f"Log file: {self.log_file_path}")
        print(f"Output directory: {self.output_dir}")
        print()
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Base name for output files
        log_basename = os.path.splitext(os.path.basename(self.log_file_path))[0]
        
        results = {}
        
        # 1. ASCII mode - all events in readable format
        print("\n[1/8] Running parse_output in ASCII mode (all events)...")
        ascii_file = os.path.join(self.output_dir, f"{log_basename}_all_ascii.txt")
        results['ascii'] = self.run_parse_output("ascii", ascii_file)
        
        # 2. Statistics mode for EQDS (non-ASCII, shows rates)
        print("\n[2/8] Running parse_output in EQDS statistics mode...")
        eqds_stats_file = os.path.join(self.output_dir, f"{log_basename}_eqds_stats.txt")
        results['eqds_stats'] = self.run_parse_output("eqds", eqds_stats_file)
        
        # 3. Extract EQDS sink events using filter
        if results['ascii']:
            print("\n[3/8] Extracting EQDS sink events...")
            eqds_sink_file = os.path.join(self.output_dir, f"{log_basename}_eqds_sink.txt")
            results['eqds_sink'] = self.run_parse_output("ascii", eqds_sink_file, use_filter="EQDS_SINK")
        
        # 4. Extract queue events using filter
        if results['ascii']:
            print("\n[4/8] Extracting queue events...")
            queue_file = os.path.join(self.output_dir, f"{log_basename}_queue.txt")
            results['queue'] = self.run_parse_output("ascii", queue_file, use_filter="QUEUE")
        
        # 5. Extract queue verbose events (all queue-related)
        if results['ascii']:
            print("\n[5/8] Extracting all queue-related events...")
            queue_verbose_file = os.path.join(self.output_dir, f"{log_basename}_queue_verbose.txt")
            self._extract_queue_events(ascii_file, queue_verbose_file)
            results['queue_verbose'] = os.path.exists(queue_verbose_file)
        
        # 6. Extract only TRAFFIC events from ASCII output
        if results['ascii']:
            print("\n[6/8] Extracting TRAFFIC events only...")
            traffic_file = os.path.join(self.output_dir, f"{log_basename}_traffic_only.txt")
            results['traffic_only'] = self.extract_traffic_events(ascii_file, traffic_file)
        
        # 7. Extract events by type
        if results['ascii']:
            print("\n[7/8] Extracting events by type...")
            results['by_type'] = self.extract_by_event_type(ascii_file, self.output_dir)
        
        # 8. Filter traffic events by specific event types
        if results.get('traffic_only'):
            print("\n[8/8] Creating filtered traffic event files...")
            traffic_file = os.path.join(self.output_dir, f"{log_basename}_traffic_only.txt")
            self._create_filtered_traffic_files(traffic_file, self.output_dir, log_basename)
        
        # Summary
        print(f"\n{'='*60}")
        print("Analysis Summary")
        print(f"{'='*60}")
        for mode, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {mode}")
        
        print(f"\nOutput files created in: {self.output_dir}")
        print(f"{'='*60}\n")
    
    def _extract_queue_events(self, ascii_file, output_file):
        """Extract all queue-related events"""
        if not os.path.exists(ascii_file):
            return False
        
        queue_keywords = ["QUEUE_EVENT", "QUEUE_APPROX", "QUEUE_RECORD", "Type QUEUE"]
        count = 0
        
        try:
            with open(ascii_file, 'r') as infile, open(output_file, 'w') as outfile:
                for line in infile:
                    if any(keyword in line for keyword in queue_keywords):
                        outfile.write(line)
                        count += 1
            
            print(f"  Extracted {count:,} queue events to {output_file}")
            return True
        except Exception as e:
            print(f"Error extracting queue events: {e}")
            return False
    
    def _create_filtered_traffic_files(self, traffic_file, output_dir, basename):
        """Create separate files for different traffic event types"""
        event_types = {
            "ARRIVE": "arrive",
            "DEPART": "depart",
            "SEND": "send",
            "CREATE": "create",
            "CREATESEND": "createsend",
            "DROP": "drop",
            "RCV": "receive",
            "TRIM": "trim",
            "BOUNCE": "bounce",
        }
        
        if not os.path.exists(traffic_file):
            return False
        
        event_files = {ev: open(os.path.join(output_dir, f"{basename}_traffic_{name}.txt"), 'w') 
                      for ev, name in event_types.items()}
        counts = {ev: 0 for ev in event_types.keys()}
        
        try:
            with open(traffic_file, 'r') as infile:
                for line in infile:
                    for event_type in event_types.keys():
                        if f"Ev {event_type}" in line:
                            event_files[event_type].write(line)
                            counts[event_type] += 1
                            break
            
            for outfile in event_files.values():
                outfile.close()
            
            print("  Traffic event type breakdown:")
            for event_type, count in counts.items():
                if count > 0:
                    print(f"    {event_type}: {count:,} events")
            
            return True
        except Exception as e:
            print(f"Error creating filtered traffic files: {e}")
            for outfile in event_files.values():
                try:
                    outfile.close()
                except:
                    pass
            return False


def main():
    parser = argparse.ArgumentParser(
        description='Parse EQDS traffic logs using parse_output tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyse_eqds_traffic_logs.py logs/simulation.log
  python analyse_eqds_traffic_logs.py logs/simulation.log -o output/
        """
    )
    
    parser.add_argument('log_file', 
                       help='Path to the EQDS log file to analyze')
    parser.add_argument('-o', '--output', 
                       default=None,
                       help='Output directory for parsed files (default: same as log file)')
    
    args = parser.parse_args()
    
    # Validate log file exists
    if not os.path.exists(args.log_file):
        print(f"Error: Log file not found: {args.log_file}")
        sys.exit(1)
    
    # Create analyzer and run
    analyzer = EQDSTrafficLogAnalyzer(args.log_file, args.output)
    analyzer.analyze()


if __name__ == "__main__":
    main()

