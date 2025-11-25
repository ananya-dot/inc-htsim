#!/usr/bin/env python3
"""
Example usage of the network simulation log analyzer.
"""

import subprocess
import os

def run_analysis_example():
    """Run the analyzer on the small_allreduce_extended.log file"""
    
    print("Network Simulation Log Analysis Example")
    print("=" * 50)
    
    # Check if log file exists
    log_file = "../small_allreduce_extended.log"
    if not os.path.exists(log_file):
        print(f"Error: Log file '{log_file}' not found")
        print("Please run the simulation first to generate the log file.")
        return
    
    # Run the analyzer
    print(f"Analyzing log file: {log_file}")
    print("This will generate several visualization plots...")
    print()
    
    try:
        result = subprocess.run(["python3", "analyze_log.py", log_file], 
                              check=True, capture_output=True, text=True)
        print("Analysis completed successfully!")
        print("\nGenerated files:")
        
        # List generated PNG files
        png_files = [f for f in os.listdir('.') if f.endswith('.png')]
        for png_file in sorted(png_files):
            print(f"  - {png_file}")
        
        print("\nTo view the plots, open the PNG files in an image viewer.")
        print("The plots show:")
        print("  - rate_over_time.png: Network rates over time")
        print("  - rate_heatmap.png: 2D heatmap of rates by sink and time")
        print("  - cack_evolution.png: Cumulative ACK evolution")
        print("  - rate_distributions.png: Statistical distributions")
        print("  - network_utilization.png: Network-wide utilization metrics")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running analysis: {e}")
        print("Make sure you have the required Python packages installed:")
        print("  pip install pandas numpy matplotlib seaborn")

if __name__ == "__main__":
    run_analysis_example()
