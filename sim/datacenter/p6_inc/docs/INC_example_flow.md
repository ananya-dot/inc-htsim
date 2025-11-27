┌─────────────────────────────────────────────────────────────────┐
│ TIME T0: SOURCE NODES CREATE PACKETS                           │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ Node 1  │          │ Node 2  │          │ Node 3  │
   │ EqdsSrc │          │ EqdsSrc │          │ EqdsSrc │
   └─────────┘          └─────────┘          └─────────┘
        │                     │                     │
        │ Creates Pkt1        │ Creates Pkt2        │ Creates Pkt3
        │ fid=1, rid=1, cid=0 │ fid=1, rid=1, cid=0 │ fid=1, rid=1, cid=0
        │ agg_op=SUM          │ agg_op=SUM          │ agg_op=SUM
        │ agg_dir=UP          │ agg_dir=UP          │ agg_dir=UP
        │ value=1048576       │ value=1048576       │ value=1048576
        │ dst=0               │ dst=0               │ dst=0
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ PACKETS ENTER NETWORK (Host → ToR Switch)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ ToR-S1  │          │ ToR-S2  │          │ ToR-S3  │
   │ Queue   │          │ Queue   │          │ Queue   │
   └─────────┘          └─────────┘          └─────────┘
        │                     │                     │
        │ Pkt1 arrives        │ Pkt2 arrives        │ Pkt3 arrives
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ PACKETS ROUTE THROUGH NETWORK (ToR → Agg → Core → Agg → ToR)  │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ Agg-S1  │          │ Agg-S2  │          │ Core-S1 │
   │ Switch  │          │ Switch  │          │ Switch  │
   └─────────┘          └─────────┘          └─────────┘
        │                     │                     │
        │ [Pkt1 arrives]      │ [Pkt2 arrives]      │ [Pkt3 arrives]
        │                     │                     │
        │ CHECK: INC packet?  │ CHECK: INC packet?  │ CHECK: INC packet?
        │ YES (agg_dir=UP)    │ YES (agg_dir=UP)    │ YES (agg_dir=UP)
        │                     │                     │
        │ KEY = (fid=1,       │ KEY = (fid=1,       │ KEY = (fid=1,
        │        rid=1,        │        rid=1,        │        rid=1,
        │        cid=0)        │        cid=0)        │        cid=0)
        │                     │                     │
        │ Create AggState:    │ Lookup AggState:    │ Lookup AggState:
        │ expected=3          │ (same key)          │ (same key)
        │ received=0          │ received=1          │ received=2
        │ agg_value=0         │ agg_value=1048576   │ agg_value=2097152
        │                     │                     │
        │ Add Pkt1 value:     │ Add Pkt2 value:     │ Add Pkt3 value:
        │ agg_value += 1048576 │ agg_value += 1048576│ agg_value += 1048576
        │ received++ (1/3)    │ received++ (2/3)    │ received++ (3/3)
        │                     │                     │
        │ FREE Pkt1           │ FREE Pkt2           │ FREE Pkt3
        │ (consumed)          │ (consumed)          │ (consumed)
        │                     │                     │
        │ Check: Complete?    │ Check: Complete?    │ Check: Complete?
        │ NO (1/3)            │ NO (2/3)            │ YES (3/3) ✓
        │                     │                     │
        │ [Continue waiting]  │ [Continue waiting]  │ [AGGREGATION COMPLETE]
        │                     │                     │
        └─────────────────────┴─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ AGGREGATION COMPLETE AT Core-S1                                 │
│ AggState: received=3, agg_value=3145728 (1048576*3)            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ CREATE NEW AGGREGATED PACKETS (Multicast)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │AggPkt→1 │          │AggPkt→2 │          │AggPkt→3 │
   │         │          │         │          │         │
   │fid=1    │          │fid=1    │          │fid=1    │
   │rid=1    │          │rid=1    │          │rid=1    │
   │cid=0    │          │cid=0    │          │cid=0    │
   │agg_op=  │          │agg_op=  │          │agg_op=  │
   │  NONE   │          │  NONE   │          │  NONE   │
   │agg_dir= │          │agg_dir= │          │agg_dir= │
   │  DOWN   │          │  DOWN   │          │  DOWN   │
   │value=   │          │value=   │          │value=   │
   │3145728  │          │3145728  │          │3145728  │
   │dst=1    │          │dst=2    │          │dst=3    │
   └─────────┘          └─────────┘          └─────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: DOWN DIRECTION (Scatter/Broadcast)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ Core-S1 │          │ Core-S1 │          │ Core-S1 │
   │ Switch  │          │ Switch  │          │ Switch  │
   └─────────┘          └─────────┘          └─────────┘
        │                     │                     │
        │ [AggPkt→1]          │ [AggPkt→2]          │ [AggPkt→3]
        │ arrives             │ arrives             │ arrives
        │                     │                     │
        │ CHECK: INC packet?  │ CHECK: INC packet?  │ CHECK: INC packet?
        │ YES (agg_dir=DOWN)  │ YES (agg_dir=DOWN)  │ YES (agg_dir=DOWN)
        │                     │                     │
        │ NO AGGREGATION      │ NO AGGREGATION      │ NO AGGREGATION
        │ (agg_op=NONE)       │ (agg_op=NONE)       │ (agg_op=NONE)
        │                     │                     │
        │ NORMAL ROUTING      │ NORMAL ROUTING      │ NORMAL ROUTING
        │ Route to dst=1      │ Route to dst=2      │ Route to dst=3
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ PACKETS ROUTE TO DESTINATIONS                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ ToR-S1  │          │ ToR-S2  │          │ ToR-S3  │
   │ Queue   │          │ Queue   │          │ Queue   │
   └─────────┘          └─────────┘          └─────────┘
        │                     │                     │
        │ [AggPkt→1]          │ [AggPkt→2]          │ [AggPkt→3]
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ FINAL DELIVERY TO DESTINATION NODES                            │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ Node 1  │          │ Node 2  │          │ Node 3  │
   │EqdsSink │          │EqdsSink │          │EqdsSink │
   └─────────┘          └─────────┘          └─────────┘
        │                     │                     │
        │ Receives aggregated  │ Receives aggregated  │ Receives aggregated
        │ value: 3145728       │ value: 3145728       │ value: 3145728
        │ (SUM of all 3)       │ (SUM of all 3)       │ (SUM of all 3)
        │                     │                     │
        └─────────────────────┴─────────────────────┘