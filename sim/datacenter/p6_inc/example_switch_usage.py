#!/usr/bin/env python3
"""
Example usage of the network switch log analyzer.
"""

import subprocess
import os

def run_switch_analysis_example():
    """Run the switch analyzer on the small_allreduce_extended_switch.log file"""
    
    print("Network Switch Log Analysis Example")
    print("=" * 50)
    
    # Check if log file exists
    log_file = "../small_allreduce_extended_switch.log"
    if not os.path.exists(log_file):
        print(f"Error: Log file '{log_file}' not found")
        print("Please run the simulation first to generate the switch log file.")
        return
    
    # Run the analyzer
    print(f"Analyzing switch log file: {log_file}")
    print("This will generate several visualization plots...")
    print()
    
    try:
        result = subprocess.run(["python3", "analyze_switch_log.py", log_file], 
                              check=True, capture_output=True, text=True)
        print("Switch analysis completed successfully!")
        print("\nGenerated files:")
        
        # List generated PNG files
        png_files = [f for f in os.listdir('.') if f.endswith('.png') and 'queue' in f]
        for png_file in sorted(png_files):
            print(f"  - {png_file}")
        
        print("\nTo view the plots, open the PNG files in an image viewer.")
        print("The plots show:")
        print("  - queue_occupancy_over_time.png: Queue sizes over time")
        print("  - queue_heatmap.png: 2D heatmap of queue occupancy")
        print("  - queue_utilization.png: Queue utilization percentages")
        print("  - queue_distributions.png: Statistical distributions")
        print("  - network_congestion.png: Network-wide congestion metrics")
        print("  - queue_evolution.png: Detailed queue behavior")
        
        print("\nKey insights from switch logs:")
        print("  - Queue occupancy indicates buffering and potential congestion")
        print("  - High utilization (>80%) suggests network bottlenecks")
        print("  - Active queue patterns show traffic distribution")
        print("  - Queue evolution reveals network dynamics")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running analysis: {e}")
        print("Make sure you have the required Python packages installed:")
        print("  pip install pandas numpy matplotlib seaborn")

if __name__ == "__main__":
    run_switch_analysis_example()
