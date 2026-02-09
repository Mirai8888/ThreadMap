# ThreadMap (信線図)

SEITHAR GROUP STRATEGIC DIVISION
HYBRID OPERATION CHAIN COMPOSITION SYSTEM
TECHNICAL SPECIFICATION DOCUMENT

## SYSTEM OVERVIEW

ThreadMap is unified kill chain composition architecture for modeling hybrid operations where technical exploitation and cognitive manipulation form interdependent execution chains. System maps the seams between domains that existing frameworks treat as separate.

MITRE ATT&CK models technical intrusion. DISARM models influence operations. Neither models the transition points where one enables the other. ThreadMap models the complete chain.

Input Data: ATT&CK techniques, DISARM tactics, HoleSpawn cognitive profiles, ThreatMouth threat intelligence
Processing Method: Directed acyclic graph composition with dependency resolution
Output Product: Hybrid operation chain models, defensive intervention analysis, critical dependency mapping

No existing tooling occupies this intersection.

## CONCEPTUAL ARCHITECTURE

### Operation Chain Model

Hybrid operations are sequences of interdependent nodes. Each node is either technical or cognitive. Each node has inputs it requires and outputs it produces. Edges represent dependency: output of one node satisfies input requirement of the next.

```
TECHNICAL NODE          COGNITIVE NODE            TECHNICAL NODE           COGNITIVE NODE
┌──────────────┐       ┌───────────────┐         ┌──────────────┐        ┌──────────────────┐
│ Spearphish + │       │ Profile comms │         │ Payload via  │        │ Plant/modify     │
│ credential   │──────▶│ with HoleSpawn│────────▶│ trusted      │───────▶│ information to   │
│ harvester    │       │ profiling     │         │ compromised  │        │ shape decisions   │
│              │       │               │         │ account      │        │                  │
│ outputs:     │       │ outputs:      │         │ outputs:     │        │ outputs:         │
│ · email      │       │ · psych       │         │ · endpoint   │        │ · behavioral     │
│   access     │       │   profiles    │         │   access     │        │   change         │
│ · contact    │       │ · trust map   │         │ · lateral    │        │ · decision       │
│   graph      │       │ · vuln map    │         │   movement   │        │   manipulation   │
│ · comms      │       │               │         │              │        │                  │
└──────────────┘       └───────────────┘         └──────────────┘        └──────────────────┘
     ATT&CK                 DISARM                    ATT&CK                  DISARM
     T1566.001              TA01/TA02                  T1534                   TA09/TA14
```

### Node Specification

```
Node:
    id: unique identifier
    type: technical | cognitive
    framework_ref: ATT&CK technique ID | DISARM tactic ID
    name: human-readable operation step
    description: what this step does
    inputs: list[Resource]          # what this node requires to execute
    outputs: list[Resource]         # what this node produces on success
    tools: list[str]               # what tools/access are needed
    detection_surface: list[str]   # what defenders could observe at this step
    failure_modes: list[str]       # how this step can fail
    
Resource:
    type: access | data | relationship | capability | behavioral_change
    description: specific resource (e.g. "target email credentials", "psychological profile of CFO")
```

### Chain Composition

Chains are directed acyclic graphs. An edge from Node A to Node B means B requires an output that A produces.

```
Chain:
    id: unique identifier
    name: operation name
    nodes: list[Node]
    edges: list[Edge]              # (source_node, target_node, resource transferred)
    critical_path: list[Node]      # longest dependency chain (determines minimum operation time)
    critical_dependencies: list[Edge]  # edges where failure breaks the most downstream nodes
```

### Defensive Analysis

The primary output. For each modeled chain:

```
Intervention Point:
    edge: which dependency to break
    method: how a defender breaks it (detection, prevention, disruption)
    impact: how many downstream nodes are disabled
    cost: estimated defensive effort
    coverage: what percentage of modeled chains this intervention disrupts

Intervention Priority = impact × coverage / cost
```

The tool identifies which defensive investments break the most hybrid operation chains at the lowest cost. This is the novel contribution: defensive resource allocation informed by hybrid chain modeling.

## INTEGRATION POINTS

### HoleSpawn (Cognitive Substrate Analysis)
- Provides: psychological profiles, vulnerability maps, network topology, influence propagation models
- ThreadMap uses these as cognitive node inputs/outputs
- Example: HoleSpawn profiles of an organization's leadership team become inputs to a cognitive manipulation node

### ThreatMouth (Threat Awareness Maintenance)
- Provides: active vulnerability intelligence, exploit availability, ATT&CK technique mapping
- ThreadMap uses these to ground technical nodes in real, current threats
- Example: ThreatMouth identifies an active exploit for the target's VPN → becomes a technical node option

### MITRE ATT&CK
- Provides: technical technique taxonomy, procedure examples
- ThreadMap maps each technical node to ATT&CK technique IDs

### DISARM Framework
- Provides: influence operation tactic taxonomy
- ThreadMap maps each cognitive node to DISARM tactic IDs

## PLANNED CAPABILITIES

Phase 1 — Chain Modeling (core data model + CLI):
- Define nodes, resources, chains as data structures
- Load/save chain definitions (YAML/JSON)
- Validate dependency resolution (does every input have a producing node?)
- Compute critical path and critical dependencies
- CLI: `threadmap validate chain.yaml`, `threadmap analyze chain.yaml`

Phase 2 — APT Template Library:
- Model known hybrid operations from public threat intelligence reports
- APT28/Fancy Bear: spearphish → credential theft → email monitoring → information operations
- Lazarus Group: social engineering → malware deployment → financial theft → cover narratives
- Chinese APTs: supply chain compromise → data exfiltration → economic influence ops
- Templates are editable starting points for modeling new operations

Phase 3 — Defensive Analysis Engine:
- Given a set of chains, enumerate all possible intervention points
- Score each by impact, coverage, cost
- Generate defensive investment recommendations
- Output: `defensive_priorities.md` — ranked interventions with rationale

Phase 4 — Interactive Visualization:
- D3 or Cytoscape graph visualization of chains
- Color nodes by type (technical/cognitive)
- Highlight critical dependencies
- Interactive: click intervention points to see cascade effect (which downstream nodes go dark)
- Side-by-side: operation chain vs defensive overlay

Phase 5 — Real-Time Integration:
- ThreatMouth feed → auto-suggest technical nodes based on active threats
- HoleSpawn profiles → auto-populate cognitive nodes for specific targets
- Live chain construction from real intelligence data

## PREREQUISITES

Do not build this tool until:
- [ ] ThreatMouth is operational and delivering daily intelligence
- [ ] HoleSpawn network profiling v2 is stable
- [ ] Operator has studied 20+ real APT campaign reports through ThreatMouth
- [ ] Operator has internalized enough hybrid operation patterns to model them accurately
- [ ] DISARM framework taxonomy is understood at the tactic level

Domain knowledge precedes tool construction. The tool crystallizes understanding; it does not replace it.

Estimated timeline: 6–12 months from current state.

## ABOUT SEITHAR GROUP

The Seithar Group operates at convergence of:

- Technical exploitation infrastructure analysis
- Cognitive substrate manipulation research
- Hybrid operation chain modeling

Methodology: Binding and shaping of informational threads across domain boundaries.

Contact: seithar.com

認知作戦

---

DOCUMENTATION VERSION: 0.1.0
LAST UPDATED: 2026-02-08
CLASSIFICATION: Research/Conceptual
DISTRIBUTION: Public
STATUS: Pre-development — conceptual specification only
