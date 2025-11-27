# Main Simulation File with Supernode Support

## Overview

`main_eqds_inc.cpp` is a simulation driver that uses the Fat-Tree topology with supernode support (`fat_tree_topology_inc.h`). It's based on `main_eqds.cpp` but includes special handling for the supernode feature.

## Key Features

- **Supernode Support**: Handles routing to/from the supernode (node ID = K³/4)
- **Compatible with EQDS**: Uses the same EQDS transport protocol
- **Full Feature Parity**: Supports all the same command-line options as `main_eqds.cpp`

## Usage

### Basic Usage

```bash
./htsim_eqds_inc -nodes <N> -tm <traffic_matrix_file> [options]
```

### Example with Supernode

For a K=8 fat-tree (K³/4 = 128 regular servers + 1 supernode = 129 total nodes):

```bash
./htsim_eqds_inc -nodes 129 -tm traffic_matrix.cm -o output.log -log traffic
```

### Command-Line Options

All options from `main_eqds.cpp` are supported:

- `-nodes N`: Total number of nodes (including supernode if present)
- `-tm <file>`: Traffic matrix file
- `-topo <file>`: Topology configuration file (optional)
- `-tiers <2|3>`: Number of tiers (default: 3)
- `-queue_type <type>`: Queue type (composite, composite_ecn, aeolus, aeolus_ecn)
- `-strat <strategy>`: Routing strategy (ecmp_host, rr_ecmp, ecmp_host_ecn, etc.)
- `-log <type>`: Logging options (traffic, flow_events, sink, switch, etc.)
- `-cwnd <size>`: Congestion window size
- `-q <size>`: Queue size
- `-end <time>`: Simulation end time in microseconds
- `-seed <n>`: Random seed
- And more...

## Supernode Details

### Node ID Assignment

- **Regular servers**: Node IDs 0 to NSRV-1 (where NSRV = K³/4)
- **Supernode**: Node ID = NSRV (K³/4)
- **Total nodes**: NSRV + 1 = K³/4 + 1

### Routing Behavior

- **Regular → Regular**: Standard fat-tree routing through ToR → Agg → Core
- **Regular → Supernode**: Routes through ToR → Agg → Core → Supernode
- **Supernode → Regular**: Routes through Core → Agg → ToR → Regular
- **Supernode → Supernode**: Not applicable (only one supernode)

### Path Selection

- The supernode connects to ALL core switches
- ECMP automatically selects among available core switches
- Multiple paths available for load balancing

## Building

Add to your Makefile:

```makefile
htsim_eqds_inc: main_eqds_inc.o fat_tree_topology_inc.o [other objects]
	$(CXX) $(LDFLAGS) -o $@ $^ $(LIBS)
```

## Differences from main_eqds.cpp

1. **Include**: Uses `../topology/fat_tree_topology_inc.h` instead of `fat_tree_topology.h`
2. **Supernode Detection**: Checks for supernode and handles routing accordingly
3. **Route Construction**: Creates routes to core switches for supernode (instead of ToR switches)
4. **Switch Registration**: Only registers regular nodes with ToR switches; supernode uses core switches

## Notes

- The supernode is only supported for 3-tier fat-tree topologies
- When using file-based topology (`-topo`), ensure the topology file accounts for the supernode
- Traffic matrices can include the supernode (node ID = NSRV) like any other node

