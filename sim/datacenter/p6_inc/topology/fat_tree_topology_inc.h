// -*- c-basic-offset: 4; indent-tabs-mode: nil -*-
#ifndef FAT_TREE
#define FAT_TREE
#include "main.h"
#include "randomqueue.h"
#include "pipe.h"
#include "config.h"
#include "loggers.h"
#include "network.h"
#include "firstfit.h"
#include "topology.h"
#include "logfile.h"
#include "eventlist.h"
#include "switch.h"
#include <ostream>

//#define N K*K*K/4

#ifndef QT
#define QT
typedef enum {UNDEFINED, RANDOM, ECN, COMPOSITE, PRIORITY,
              CTRL_PRIO, FAIR_PRIO, LOSSLESS, LOSSLESS_INPUT, LOSSLESS_INPUT_ECN,
              COMPOSITE_ECN, COMPOSITE_ECN_LB, SWIFT_SCHEDULER, ECN_PRIO, AEOLUS, AEOLUS_ECN} queue_type;
typedef enum {UPLINK, DOWNLINK} link_direction;
#endif

// avoid random constants
#define TOR_TIER 0
#define AGG_TIER 1
#define CORE_TIER 2

class FatTreeTopology: public Topology{
public:
    vector <Switch*> switches_lp;
    vector <Switch*> switches_up;
    vector <Switch*> switches_c;

    // 3rd index is link number in bundle
    vector< vector< vector<Pipe*> > > pipes_nc_nup;
    vector< vector< vector<Pipe*> > > pipes_nup_nlp;
    vector< vector< vector<Pipe*> > > pipes_nlp_ns;
    vector< vector< vector<BaseQueue*> > > queues_nc_nup;
    vector< vector< vector<BaseQueue*> > > queues_nup_nlp;
    vector< vector< vector<BaseQueue*> > > queues_nlp_ns;

    vector< vector< vector<Pipe*> > > pipes_nup_nc;
    vector< vector< vector<Pipe*> > > pipes_nlp_nup;
    vector< vector< vector<Pipe*> > > pipes_ns_nlp;
    vector< vector< vector<BaseQueue*> > > queues_nup_nc;
    vector< vector< vector<BaseQueue*> > > queues_nlp_nup;
    vector< vector< vector<BaseQueue*> > > queues_ns_nlp;
  
    // SUPERNODE: Queues and pipes connecting the supernode (node ID = NSRV) to all core switches
    // The supernode is the (K^3/4 + 1)th node, connected directly to all core switches
    // queues_core_supernode[core_id] = queue from core switch to supernode
    // queues_supernode_core[core_id] = queue from supernode to core switch
    vector<BaseQueue*> queues_core_supernode;
    vector<BaseQueue*> queues_supernode_core;
    vector<Pipe*> pipes_core_supernode;
    vector<Pipe*> pipes_supernode_core;
  
    FirstFit* ff;
    QueueLoggerFactory* _logger_factory;
    EventList* _eventlist;
    uint32_t failed_links;
    queue_type _qt;
    queue_type _sender_qt;

    // For regular topologies, just use the constructor.  For custom topologies, load from a config file.
    static FatTreeTopology* load(const char * filename, QueueLoggerFactory* logger_factory, EventList& eventlist,
                                 mem_b queuesize, queue_type q_type, queue_type sender_q_type);

    FatTreeTopology(uint32_t no_of_nodes, linkspeed_bps linkspeed, mem_b queuesize, QueueLoggerFactory* logger_factory,
                    EventList* ev,FirstFit* f, queue_type qt, simtime_picosec latency, simtime_picosec switch_latency, queue_type snd = FAIR_PRIO);
    FatTreeTopology(uint32_t no_of_nodes, linkspeed_bps linkspeed, mem_b queuesize, QueueLoggerFactory* logger_factory,
                    EventList* ev,FirstFit* f, queue_type qt);      
    FatTreeTopology(uint32_t no_of_nodes, linkspeed_bps linkspeed, mem_b queuesize, QueueLoggerFactory* logger_factory,
                    EventList* ev,FirstFit* f, queue_type qt, uint32_t fail);
    FatTreeTopology(uint32_t no_of_nodes, linkspeed_bps linkspeed, mem_b queuesize, QueueLoggerFactory* logger_factory,
                    EventList* ev,FirstFit* f, queue_type qt, queue_type sender_qt, uint32_t fail);

    static void set_tier_parameters(int tier, int radix_up, int radix_down, mem_b queue_up, mem_b queue_down, int bundlesize, linkspeed_bps downlink_speed, int oversub);

    void init_network();
    virtual vector<const Route*>* get_bidir_paths(uint32_t src, uint32_t dest, bool reverse);

    BaseQueue* alloc_src_queue(QueueLogger* q);
    BaseQueue* alloc_queue(QueueLogger* q, mem_b queuesize, link_direction dir, int switch_tier, bool tor);
    BaseQueue* alloc_queue(QueueLogger* q, uint64_t speed, mem_b queuesize,
                           link_direction dir,  int switch_tier, bool tor);
    static void set_tiers(uint32_t tiers) {_tiers = tiers;}
    static uint32_t get_tiers() {return _tiers;}
    static void set_latencies(simtime_picosec src_lp, simtime_picosec lp_up, simtime_picosec up_cs,
                              simtime_picosec lp_switch, simtime_picosec up_switch, simtime_picosec core_switch) {
        _link_latencies[0] = src_lp;
        _link_latencies[1] = lp_up;
        _link_latencies[2] = up_cs;
        _switch_latencies[0] = lp_switch; // aka tor
        _switch_latencies[1] = up_switch; // aka tor
        _switch_latencies[2] = core_switch; // aka tor
    }
    static void set_podsize(int hosts_per_pod) {
        _hosts_per_pod = hosts_per_pod;
    }

    void count_queue(Queue*);
    void print_path(std::ofstream& paths,uint32_t src,const Route* route);
    vector<uint32_t>* get_neighbours(uint32_t src) { return NULL;};
    uint32_t no_of_nodes() const {return _no_of_nodes;}
    uint32_t no_of_cores() const {return NCORE;}
    uint32_t no_of_servers() const {return NSRV;}
    uint32_t no_of_pods() const {return NPOD;}
    uint32_t tor_switches_per_pod() const {
        if (_tor_switches_per_pod == 0) {
            cerr << "ERROR: tor_switches_per_pod() returning 0! this=" << this 
                 << " _tor_switches_per_pod=" << _tor_switches_per_pod << endl;
        }
        return _tor_switches_per_pod;
    }
    uint32_t agg_switches_per_pod() const {return _agg_switches_per_pod;}
    uint32_t bundlesize(int tier) const {return _bundlesize[tier];}
    uint32_t radix_up(int tier) const {return _radix_up[tier];}
    uint32_t radix_down(int tier) const {return _radix_down[tier];}
    uint32_t queue_up(int tier) const {return _queue_up[tier];}
    uint32_t queue_down(int tier) const {return _queue_down[tier];}

    void add_failed_link(uint32_t type, uint32_t switch_id, uint32_t link_id);

    // add loggers to record total queue size at switches
    virtual void add_switch_loggers(Logfile& log, simtime_picosec sample_period); 

    uint32_t HOST_POD_SWITCH(uint32_t src){
        // SUPERNODE: Supernode is in the last pod, connected to the last ToR switch
        // The supernode has node ID = NSRV, and it's in pod NPOD-1 (the virtual pod)
        // The ToR switch for the supernode pod is NTOR-1
        if (is_supernode(src)) {
            return NTOR - 1;  // Last ToR switch (in the virtual pod)
        }
        return src/_radix_down[TOR_TIER];
    }

    uint32_t HOST_POD_ID(uint32_t src){
        if (_tiers == 3)
            return src%_hosts_per_pod;
        else
            // only one pod in leaf-spine
            return src;
    }

    uint32_t HOST_POD(uint32_t src){
        // SUPERNODE: Supernode is in the last pod (the virtual pod)
        // The supernode has node ID = NSRV, and it's in pod NPOD-1
        if (is_supernode(src)) {
            return NPOD - 1;  // Last pod (the virtual pod)
        }
        if (_tiers == 3) 
            return src/_hosts_per_pod;
        else
            // only one pod in leaf-spine
            return 0;
    }
    /*
    uint32_t MIN_POD_ID(uint32_t pod_id){
        if (_tiers == 2) assert(pod_id == 0);
        return pod_id*K/2;
    }
    uint32_t MAX_POD_ID(uint32_t pod_id){
        if (_tiers == 2) assert(pod_id == 0);
        return (pod_id+1)*K/2-1;
    }
     */
    uint32_t MIN_POD_TOR_SWITCH(uint32_t pod_id){
        if (_tiers == 2) assert(pod_id == 0);
        return pod_id * _tor_switches_per_pod;
    }
    uint32_t MAX_POD_TOR_SWITCH(uint32_t pod_id){
        if (_tiers == 2) assert(pod_id == 0);
        return (pod_id + 1) * _tor_switches_per_pod - 1;
    }
    uint32_t MIN_POD_AGG_SWITCH(uint32_t pod_id){
        if (_tiers == 2) assert(pod_id == 0);
        return pod_id * _agg_switches_per_pod;
    }
    uint32_t MAX_POD_AGG_SWITCH(uint32_t pod_id){
        if (_tiers == 2) assert(pod_id == 0);
        if (_agg_switches_per_pod == 0) {
            cerr << "FATAL: MAX_POD_AGG_SWITCH called with _agg_switches_per_pod=0 for pod " << pod_id << endl;
            cerr << "  This means set_params() was not called or _agg_switches_per_pod was not set correctly" << endl;
            abort();
        }
        uint32_t result = (pod_id + 1) * _agg_switches_per_pod - 1;
        cerr << "DEBUG: MAX_POD_AGG_SWITCH(" << pod_id << ") = (" << pod_id << "+1)*" << _agg_switches_per_pod << "-1 = " << result << endl;
        return result;
    }

    // convert an agg switch ID to a pod ID
    uint32_t AGG_SWITCH_POD_ID(uint32_t agg_switch_id) {
        return agg_switch_id / _agg_switches_per_pod;
    }
    
    // SUPERNODE: Check if a node ID corresponds to the supernode
    // The supernode has node ID = NSRV (the (K^3/4 + 1)th node)
    bool is_supernode(uint32_t node_id) const {
        return (_tiers == 3 && node_id == NSRV);
    }
    
    // SUPERNODE: Get the supernode ID (NSRV)
    uint32_t get_supernode_id() const {
        return NSRV;
    }
    
    //uint32_t getK() const {return K;}
    uint32_t getNAGG() const {return NAGG;}
private:
    map<Queue*,int> _link_usage;
    static FatTreeTopology* load(istream& file, QueueLoggerFactory* logger_factory, EventList& eventlist,
                                 mem_b queuesize, queue_type q_type, queue_type sender_q_type);
    void set_linkspeeds(linkspeed_bps linkspeed);
    void set_queue_sizes(mem_b queuesize);
    int64_t find_lp_switch(Queue* queue);
    int64_t find_up_switch(Queue* queue);
    int64_t find_core_switch(Queue* queue);
    int64_t find_destination(Queue* queue);
    void set_params(uint32_t no_of_nodes);
    void set_custom_params(uint32_t no_of_nodes);
    void alloc_vectors();
    uint32_t NCORE, NAGG, NTOR, NSRV, NPOD;
    uint32_t _tor_switches_per_pod, _agg_switches_per_pod;
    static uint32_t _tiers;

    // _link_latencies[0] is the ToR->host latency.
    static simtime_picosec _link_latencies[3];

    // _switch_latencies[0] is the ToR switch latency.
    static simtime_picosec _switch_latencies[3];

    // How many uplinks to bundle from each node in a tier to the same
    // node in the tier below.  Eg bundlesize[2] = 2 means two
    // bundled links from Core to Upper pod switch (and vice versa)
    //
    // Note: we don't currently support bundling from the hosts to
    // ToRs because transport needs to know for that to work.
    static uint32_t _bundlesize[3];

    // Linkspeed of each link in a switch tier to the tier below. ToRs are tier 0.
    // Eg. _downlink_speeds[0] = 400Gbps indicates 400Gbps links from hosts
    // to ToRs.
    static linkspeed_bps _downlink_speeds[3];

    // degree of oversubscription at tier.  Eg _oversub[TOR_TIER] = 3 implies 3x more bw to hosts than to agg switches.
    static uint32_t _oversub[3];

    // switch radix used.  Eg _radix_down[0] = 32 indicates 32 downlinks from ToRs.  _radix_up[2] should be zero in a 3-tier topology.  
    static uint32_t _radix_down[3];
    static uint32_t _radix_up[2];

    // switch queue size used.  Eg _queue_down[0] = 32 indicates 32 downlinks from ToRs.  _queue_up[2] should be zero in a 3-tier topology.  
    static mem_b _queue_down[3];
    static mem_b _queue_up[2];

    // number of hosts in a pod.  
    static uint32_t _hosts_per_pod; 
    
    uint32_t _no_of_nodes;
    simtime_picosec _hop_latency,_switch_latency;
};

#endif
