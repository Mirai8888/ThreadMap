# ThreadMap Architecture Specification

**Version:** 0.2.0
**Date:** 2026-02-18
**Status:** Architecture Draft
**Author:** Seithar Group Research Division

---

## 1. Purpose and Scope

ThreadMap is a hybrid operation chain modeling system. It fills a specific gap in the Seithar ecosystem: no existing tool models how cognitive and technical operations chain together across time, platforms, and actors.

**What exists today:**

| Tool | Domain | Function |
|------|--------|----------|
| HoleSpawn | Offense | Profile targets, map vulnerability surfaces, generate engagement architectures |
| seithar-cogdef | Defense | Scan content for cognitive exploitation, classify using SCT taxonomy |
| ThreatMouth | Intelligence | Collect, score, and summarize threat intelligence |

**What is missing:**

None of these tools model the sequencing of operations. HoleSpawn profiles a target but does not model how that profile feeds into a multi-step campaign. ThreatMouth identifies threats but does not chain them into kill sequences. seithar-cogdef detects techniques in isolation but does not track how those techniques compose over time.

ThreadMap models the full operation chain: ordered sequences of technical and cognitive actions, their dependencies, their temporal structure, and the platforms and actors involved. The key differentiator is hybrid convergence. MITRE ATT&CK models cyber kill chains. DISARM models influence operations. ThreadMap models chains where both domains are interdependent within a single operation.

**Primary outputs:**

1. Operation chain models (DAGs of technical + cognitive nodes)
2. Critical dependency analysis (which edges, if broken, collapse the most downstream nodes)
3. Defensive intervention priorities (ranked by impact/cost ratio)
4. Temporal sequence visualization (when things happen, on which platforms, by which actors)

---

## 2. Core Data Model

### 2.1 Resource

The atomic unit of dependency. Every node consumes and produces resources.

```python
@dataclass
class Resource:
    id: str                          # unique within chain, e.g. "r-email-creds-01"
    resource_type: ResourceType      # enum: access, data, relationship, capability, behavioral_change, infrastructure
    description: str                 # "CFO email credentials"
    platform: str | None             # "gmail", "twitter", "physical", None
    classification: str | None       # SCT code or ATT&CK data source, e.g. "SCT-005", "DS0029"
    perishable: bool = False         # does this resource expire?
    ttl_hours: int | None = None     # if perishable, how long is it valid?
```

### 2.2 Actor

An entity that executes nodes. Can be an individual, a team, a bot, or an automated system.

```python
@dataclass
class Actor:
    id: str                          # "actor-apt28-unit-26165"
    name: str                        # "Unit 26165"
    actor_type: ActorType            # enum: state, proxy, hacktivist, criminal, automated, insider
    capabilities: list[str]          # ["spearphishing", "zero-day-dev", "media-placement"]
    known_aliases: list[str]         # ["Fancy Bear", "Sofacy", "Pawn Storm"]
    attribution_confidence: float    # 0.0 to 1.0
```

### 2.3 Platform

Where an operation step executes.

```python
@dataclass
class Platform:
    id: str                          # "plat-twitter"
    name: str                        # "Twitter/X"
    platform_type: PlatformType      # enum: social_media, email, messaging, infrastructure, physical, media, government
    reach_estimate: str | None       # "500M monthly active users"
    detection_difficulty: float      # 0.0 (trivial to detect) to 1.0 (nearly impossible)
```

### 2.4 Node

A single operation step. Either technical or cognitive.

```python
@dataclass
class Node:
    id: str                          # "n-spearphish-01"
    name: str                        # "Spearphish credential harvester"
    description: str                 # detailed explanation of what this step does
    node_type: NodeType              # enum: technical, cognitive, hybrid
    domain: str                      # "cyber", "cognitive", "physical", "convergence"

    # Framework references
    attack_ids: list[str]            # ATT&CK technique IDs: ["T1566.001", "T1598.003"]
    disarm_ids: list[str]            # DISARM tactic/technique IDs: ["TA01", "T0085.004"]
    sct_codes: list[str]             # Seithar taxonomy: ["SCT-001", "SCT-005"]

    # Dependencies
    inputs: list[str]                # Resource IDs this node requires
    outputs: list[str]               # Resource IDs this node produces

    # Execution context
    actor_id: str | None             # which actor executes this node
    platform_id: str | None          # where this node executes
    tools: list[str]                 # tools/malware/software used

    # Temporal
    earliest_start: datetime | None  # absolute earliest this can begin
    duration_estimate: timedelta | None  # how long this step takes
    sequence_order: int | None       # optional explicit ordering hint

    # Analysis
    detection_surface: list[str]     # observable indicators for defenders
    failure_modes: list[str]         # ways this step can fail
    success_probability: float       # 0.0 to 1.0 estimate
    reversibility: float             # 0.0 (permanent) to 1.0 (trivially reversible)
```

### 2.5 Edge

A dependency between two nodes, mediated by a resource transfer.

```python
@dataclass
class Edge:
    source_node_id: str
    target_node_id: str
    resource_id: str                 # which resource flows along this edge
    edge_type: EdgeType              # enum: dependency, enables, amplifies, triggers
    delay: timedelta | None          # minimum time between source completion and target start
    conditional: str | None          # condition under which this edge activates, e.g. "if target clicks link"
```

### 2.6 Chain

The top-level operation model. A directed acyclic graph of nodes and edges.

```python
@dataclass
class Chain:
    id: str                          # "chain-apt28-election-2016"
    name: str                        # "APT28 US Election Interference 2016"
    description: str
    classification: str              # "hybrid-influence", "cyber-only", "cognitive-only"

    # Components
    actors: list[Actor]
    platforms: list[Platform]
    resources: list[Resource]
    nodes: list[Node]
    edges: list[Edge]

    # Metadata
    date_range: tuple[datetime, datetime] | None  # when the operation occurred or is modeled for
    source_reports: list[str]        # URLs to public reporting used to construct this chain
    confidence: float                # overall confidence in the model, 0.0 to 1.0
    tags: list[str]                  # ["election", "APT28", "Russia", "information-operations"]

    # Computed (populated by analysis engine)
    critical_path: list[str] | None           # node IDs on the longest dependency chain
    critical_edges: list[str] | None          # edge keys where failure causes maximum cascade
    intervention_points: list[dict] | None    # ranked defensive recommendations
```

### 2.7 Enums

```python
class ResourceType(str, Enum):
    ACCESS = "access"                # credentials, sessions, physical entry
    DATA = "data"                    # exfiltrated documents, profiles, intelligence
    RELATIONSHIP = "relationship"    # trust, rapport, social connection
    CAPABILITY = "capability"        # exploit code, tooling, tradecraft
    BEHAVIORAL_CHANGE = "behavioral_change"  # opinion shift, action taken, decision altered
    INFRASTRUCTURE = "infrastructure"  # servers, domains, accounts, personas

class NodeType(str, Enum):
    TECHNICAL = "technical"
    COGNITIVE = "cognitive"
    HYBRID = "hybrid"               # single step with both technical and cognitive components

class ActorType(str, Enum):
    STATE = "state"
    PROXY = "proxy"
    HACKTIVIST = "hacktivist"
    CRIMINAL = "criminal"
    AUTOMATED = "automated"
    INSIDER = "insider"

class PlatformType(str, Enum):
    SOCIAL_MEDIA = "social_media"
    EMAIL = "email"
    MESSAGING = "messaging"
    INFRASTRUCTURE = "infrastructure"
    PHYSICAL = "physical"
    MEDIA = "media"
    GOVERNMENT = "government"

class EdgeType(str, Enum):
    DEPENDENCY = "dependency"        # hard requirement
    ENABLES = "enables"              # makes possible but not strictly required
    AMPLIFIES = "amplifies"          # increases effectiveness
    TRIGGERS = "triggers"            # causes automatic execution
```

---

## 3. Integration Points

### 3.1 HoleSpawn Integration

HoleSpawn produces psychological profiles, vulnerability maps, and network topology. ThreadMap consumes these as inputs to cognitive nodes.

**Data flow:**

```
HoleSpawn profile output (JSON)
    -> ThreadMap Resource(type=DATA, description="psychological profile of {target}")
    -> Input to cognitive Node (e.g. "craft identity-targeted messaging")
```

**Integration method:** File-based initially. HoleSpawn writes profiles to `~/HoleSpawn/output/profiles/`. ThreadMap reads them via `shared_config.resolve_repo_path("holespawn")`.

**Specific HoleSpawn outputs ThreadMap consumes:**
- `profile.json`: psychological profile with communication style, themes, vulnerabilities
- `network.json`: community graph with bridge nodes, influence scores
- `sct_report.json`: SCT vulnerability mapping per target
- `temporal/`: time-series behavioral data

**Future:** Direct Python import. ThreadMap imports `holespawn.profiler` to run on-demand profiling during chain construction.

### 3.2 seithar-cogdef Integration

seithar-cogdef provides the SCT taxonomy (SCT-001 through SCT-012) and scanning capability. ThreadMap uses the taxonomy for node classification and the scanner for validating that modeled cognitive techniques match real-world content.

**Data flow:**

```
seithar-cogdef taxonomy.py
    -> ThreadMap Node.sct_codes classification
    -> Defensive analysis: which SCT codes appear in the chain, what inoculation is available

seithar-cogdef scanner output (JSON)
    -> ThreadMap validation: "does this real-world content match the cognitive technique modeled in node X?"
```

**Integration method:** Import `taxonomy` module via `shared_config.get_taxonomy_module()`. Scanner invoked as subprocess or direct import for chain validation.

**Specific integration points:**
- `taxonomy.SCT_TAXONOMY`: classifying cognitive nodes
- `taxonomy.get_code()`: looking up technique details for node documentation
- `scanner.analyze_local()` / `scanner.analyze_with_llm()`: validating that modeled techniques appear in collected content
- `inoculator.py`: generating defensive training materials for identified intervention points

### 3.3 ThreatMouth Integration

ThreatMouth collects and scores threat intelligence. ThreadMap uses this to ground technical nodes in current, real threats rather than abstract possibilities.

**Data flow:**

```
ThreatMouth scored items (SQLite)
    -> ThreadMap: "CVE-2024-XXXX is actively exploited, confidence 0.95"
    -> Populate technical Node with real exploit data
    -> Update chain success_probability based on exploit availability
```

**Integration method:** Read ThreatMouth SQLite database directly via `aiosqlite` or sync wrapper. Query `items` table for high-relevance scored items matching chain context.

**Specific queries:**
- Items with `relevance_score >= 0.7` matching target technology stack
- CVE data from `cve_ids` field for specific software versions
- Active exploit availability from `poc_cache` table
- Temporal trends: is this threat increasing or decreasing?

### 3.4 External Framework Mapping

**MITRE ATT&CK:**
- Each technical node maps to one or more ATT&CK technique IDs
- ThreadMap ships a local copy of ATT&CK STIX data (updated quarterly)
- Used for: node classification, procedure example lookup, detection mapping

**DISARM Framework:**
- Each cognitive node maps to one or more DISARM tactic/technique IDs
- ThreadMap ships a local copy of DISARM matrix
- Used for: influence operation node classification, countermeasure lookup

---

## 4. Architecture

### 4.1 Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.11+ | Ecosystem consistency (HoleSpawn, ThreatMouth, seithar-cogdef all Python) |
| Data modeling | Pydantic v2 | Validation, serialization, JSON Schema generation |
| Storage (chains) | YAML/JSON files + SQLite index | Chains are documents, not relational. Files for version control, SQLite for querying |
| Storage (analysis) | SQLite | Intervention analysis results, cached computations |
| Graph engine | NetworkX | DAG operations, critical path, topological sort. Already a HoleSpawn dependency |
| Visualization | Cytoscape.js (web) | Interactive graph visualization with good Python bindings (py2cytoscape) |
| Web layer | FastAPI | Lightweight API for visualization frontend and future integrations |
| CLI | Click | Consistent with ThreatMouth CLI patterns |
| LLM integration | Anthropic API | Chain construction assistance, natural language to chain translation |
| Serialization | YAML (human-authored chains), JSON (machine output) | YAML for readability when manually modeling operations |
| Testing | pytest | Ecosystem standard |

### 4.2 Project Structure

```
threadmap/
    __init__.py
    __main__.py                  # CLI entry point
    models/
        __init__.py
        base.py                  # Resource, Actor, Platform, Node, Edge, Chain
        enums.py                 # ResourceType, NodeType, ActorType, etc.
        validation.py            # Chain validation (dependency resolution, cycle detection)
    engine/
        __init__.py
        analyzer.py              # Critical path, critical dependencies, intervention scoring
        composer.py              # Chain construction helpers, template instantiation
        resolver.py              # Dependency resolution: do all inputs have producers?
        temporal.py              # Timeline computation, scheduling, temporal overlap detection
    integrations/
        __init__.py
        holespawn.py             # Read HoleSpawn profiles, convert to Resources
        cogdef.py                # SCT taxonomy lookup, scanner invocation
        threatmouth.py           # Query ThreatMouth DB for active threats
        attack.py                # MITRE ATT&CK STIX data loader
        disarm.py                # DISARM matrix loader
    storage/
        __init__.py
        file_store.py            # YAML/JSON chain persistence
        index.py                 # SQLite index for chain metadata, search
    visualization/
        __init__.py
        graph.py                 # NetworkX to Cytoscape.js conversion
        timeline.py              # Temporal sequence rendering
        server.py                # FastAPI app serving the visualization
        static/                  # HTML/JS/CSS for Cytoscape.js frontend
    cli/
        __init__.py
        commands.py              # Click CLI: validate, analyze, visualize, import, export
    templates/
        apt28_election_2016.yaml
        lazarus_social_engineering.yaml
        generic_hack_and_leak.yaml
        supply_chain_influence.yaml
    data/
        attack_stix/             # ATT&CK STIX bundle (updated quarterly)
        disarm_matrix/           # DISARM framework data
tests/
    test_models.py
    test_analyzer.py
    test_resolver.py
    test_integrations.py
    test_cli.py
docs/
    SPEC.md                      # this file
    EXAMPLES.md                  # worked examples
    INTEGRATION_GUIDE.md         # how to connect ecosystem tools
```

### 4.3 Data Flow

```
                                    ┌─────────────────┐
                                    │  YAML/JSON       │
                                    │  Chain Definition │
                                    └────────┬────────┘
                                             │
                                             v
┌──────────────┐                  ┌─────────────────────┐                 ┌────────────────┐
│  HoleSpawn   │─── profiles ───>│                       │<── threat ────│  ThreatMouth   │
│  profiles    │                  │    ThreadMap Core     │    intel      │  intelligence  │
└──────────────┘                  │                       │               └────────────────┘
                                  │  1. Parse & validate  │
┌──────────────┐                  │  2. Resolve deps      │               ┌────────────────┐
│  seithar-    │─── taxonomy ───>│  3. Compute critical   │               │  ATT&CK STIX   │
│  cogdef      │                  │     path               │<── technique ─│  DISARM matrix │
└──────────────┘                  │  4. Score interventions│    data       └────────────────┘
                                  │  5. Generate output    │
                                  └──────────┬────────────┘
                                             │
                              ┌──────────────┼──────────────┐
                              v              v              v
                     ┌──────────────┐ ┌────────────┐ ┌────────────────┐
                     │ Analysis     │ │ Cytoscape  │ │ Defensive      │
                     │ Report (JSON)│ │ Graph (web)│ │ Priorities (MD)│
                     └──────────────┘ └────────────┘ └────────────────┘
```

---

## 5. Analysis Engine

### 5.1 Dependency Resolution

Given a chain, verify that every node's input resources are produced by at least one upstream node (or are marked as pre-existing). Uses topological sort on the DAG.

```python
def resolve_dependencies(chain: Chain) -> list[str]:
    """
    Returns list of unresolved resource IDs (inputs with no producer).
    Empty list means all dependencies are satisfied.
    """
```

### 5.2 Critical Path Computation

The critical path is the longest path through the DAG weighted by `duration_estimate`. This determines the minimum calendar time for the operation.

```python
def compute_critical_path(chain: Chain) -> CriticalPathResult:
    """
    Returns:
        nodes: ordered list of node IDs on the critical path
        total_duration: sum of durations along the path
        bottlenecks: nodes where duration reduction would shorten the critical path
    """
```

### 5.3 Critical Dependency Analysis

For each edge, compute how many downstream nodes become unreachable if that edge is severed. Edges with the highest downstream impact are critical dependencies.

```python
def compute_critical_dependencies(chain: Chain) -> list[CriticalEdge]:
    """
    Returns edges ranked by downstream_impact (number of nodes disabled if edge breaks).
    """
```

### 5.4 Intervention Scoring

The primary analytical output. For each possible intervention point (edge that can be broken by a defender), compute:

- **Impact**: number of downstream nodes disabled
- **Coverage**: across a library of chains, what fraction include this edge pattern
- **Cost**: estimated defensive effort (manual annotation or heuristic)
- **Priority**: impact * coverage / cost

```python
def score_interventions(chain: Chain, library: list[Chain] | None = None) -> list[Intervention]:
    """
    Returns ranked list of defensive interventions.
    If library is provided, coverage is computed across all chains.
    """
```

### 5.5 Temporal Analysis

Compute the operation timeline: when each node can start (given dependencies and delays), when it completes, and what the overall operation window looks like.

```python
def compute_timeline(chain: Chain) -> Timeline:
    """
    Returns:
        schedule: dict[node_id, (earliest_start, latest_start, expected_end)]
        total_window: (operation_start, operation_end)
        parallel_phases: list of node groups that can execute simultaneously
    """
```

---

## 6. MVP Features vs Roadmap

### MVP (Phase 1)

Target: functional chain modeling and analysis from CLI.

- [ ] Pydantic data models for all entities (Resource, Actor, Platform, Node, Edge, Chain)
- [ ] YAML/JSON chain serialization and deserialization
- [ ] Dependency resolution (validate all inputs have producers)
- [ ] Cycle detection (reject invalid DAGs)
- [ ] Critical path computation via NetworkX
- [ ] Critical dependency analysis (edge removal impact)
- [ ] Basic intervention scoring (impact only, no cross-chain coverage)
- [ ] CLI: `threadmap validate <chain.yaml>`
- [ ] CLI: `threadmap analyze <chain.yaml>`
- [ ] CLI: `threadmap export <chain.yaml> --format json|dot|markdown`
- [ ] One complete example chain: APT28 2016 election interference
- [ ] SCT taxonomy integration via shared_config

### Phase 2: Template Library and Framework Integration

- [ ] 5+ operation chain templates from public threat intelligence
- [ ] ATT&CK STIX data loader with technique lookup
- [ ] DISARM matrix loader with tactic lookup
- [ ] HoleSpawn profile importer (convert profiles to Resources)
- [ ] ThreatMouth query integration (ground technical nodes in active threats)
- [ ] CLI: `threadmap import-profile <holespawn-output.json>`
- [ ] CLI: `threadmap enrich <chain.yaml>` (auto-populate ATT&CK/DISARM references)

### Phase 3: Visualization

- [ ] Cytoscape.js web frontend for chain visualization
- [ ] Color-coded nodes (technical=blue, cognitive=red, hybrid=purple)
- [ ] Edge annotations (resource type, delay)
- [ ] Critical path highlighting
- [ ] Interactive intervention simulation (click to break edge, see cascade)
- [ ] Timeline view (horizontal axis = time, vertical axis = platform)
- [ ] FastAPI server: `threadmap serve`

### Phase 4: Advanced Analysis

- [ ] Cross-chain coverage scoring (which interventions disrupt the most modeled operations)
- [ ] Pattern matching across chains (find common sub-chains)
- [ ] Defensive gap analysis (given current defenses, which chains are unmitigated)
- [ ] LLM-assisted chain construction ("describe an operation and I will model it")
- [ ] Automatic chain generation from ThreatMouth intelligence + HoleSpawn profiles

### Phase 5: Real-Time and Operational

- [ ] Live ThreatMouth feed integration (new threats auto-suggest chain modifications)
- [ ] HoleSpawn real-time profile updates flowing into active chain models
- [ ] seithar-cogdef scanner validating that modeled techniques appear in collected content
- [ ] Alert system: "new exploit matches a technical node in chain X, success probability increased"
- [ ] Rust TUI (consistent with HoleSpawn TUI for ecosystem coherence)

---

## 7. Example Use Case: APT28 2016 Election Interference

This chain models the publicly reported hybrid operation combining cyber intrusion with information operations.

### Actors

- **Unit 26165** (GRU): technical intrusion team
- **Unit 74455** (GRU): information operations team
- **DCLeaks persona**: synthetic online persona for document release
- **Guccifer 2.0 persona**: synthetic online persona for media engagement

### Platforms

- Email (Gmail, campaign infrastructure)
- Twitter/X
- WordPress (DCLeaks.com)
- WikiLeaks
- US news media (amplification)

### Chain (simplified)

```yaml
chain:
  id: chain-apt28-election-2016
  name: "APT28 DNC Hack and Leak Operation"
  classification: hybrid-influence

  nodes:
    - id: n-recon
      name: "Target reconnaissance"
      node_type: technical
      attack_ids: ["T1589", "T1590"]
      inputs: []
      outputs: ["r-target-emails", "r-org-structure"]
      actor_id: unit-26165
      platform_id: plat-email
      duration_estimate: "14d"

    - id: n-spearphish
      name: "Spearphishing credential harvester"
      node_type: technical
      attack_ids: ["T1566.002"]
      inputs: ["r-target-emails"]
      outputs: ["r-email-creds"]
      actor_id: unit-26165
      platform_id: plat-email
      success_probability: 0.3
      duration_estimate: "7d"

    - id: n-access
      name: "Email account compromise and exfiltration"
      node_type: technical
      attack_ids: ["T1114.002", "T1048"]
      inputs: ["r-email-creds"]
      outputs: ["r-exfil-docs", "r-internal-comms"]
      actor_id: unit-26165
      platform_id: plat-email
      duration_estimate: "30d"

    - id: n-profile
      name: "Profile key figures from exfiltrated communications"
      node_type: cognitive
      sct_codes: ["SCT-005", "SCT-002"]
      inputs: ["r-internal-comms", "r-org-structure"]
      outputs: ["r-psych-profiles", "r-narrative-targets"]
      actor_id: unit-74455
      duration_estimate: "14d"
      description: "HoleSpawn-style profiling of organizational leadership from stolen emails. Identify narrative vulnerabilities, internal tensions, exploitable relationships."

    - id: n-persona-creation
      name: "Create synthetic release personas"
      node_type: cognitive
      disarm_ids: ["T0007", "T0014"]
      sct_codes: ["SCT-003"]
      inputs: []
      outputs: ["r-dcleaks-persona", "r-guccifer-persona"]
      actor_id: unit-74455
      platform_id: plat-twitter
      duration_estimate: "7d"

    - id: n-selective-release
      name: "Staged document release via personas"
      node_type: hybrid
      attack_ids: ["T1567"]
      disarm_ids: ["T0085", "TA06"]
      sct_codes: ["SCT-006", "SCT-001", "SCT-002"]
      inputs: ["r-exfil-docs", "r-narrative-targets", "r-dcleaks-persona", "r-guccifer-persona"]
      outputs: ["r-public-docs", "r-media-attention"]
      actor_id: unit-74455
      duration_estimate: "90d"
      description: "Timed release of selected documents to maximize narrative impact. Exploits SCT-006 (temporal manipulation) by aligning releases with campaign events. Exploits SCT-002 (information asymmetry) through selective disclosure."

    - id: n-amplification
      name: "Media and social amplification"
      node_type: cognitive
      disarm_ids: ["TA09", "T0049"]
      sct_codes: ["SCT-004", "SCT-007"]
      inputs: ["r-public-docs", "r-media-attention"]
      outputs: ["r-narrative-adoption"]
      actor_id: unit-74455
      platform_id: plat-twitter
      duration_estimate: "120d"
      description: "Drive media coverage and social sharing. Exploit SCT-004 (social proof) through bot amplification. Exploit SCT-007 (recursive infection) by making documents 'news' that journalists and citizens propagate independently."

  edges:
    - source: n-recon
      target: n-spearphish
      resource: r-target-emails
      edge_type: dependency

    - source: n-spearphish
      target: n-access
      resource: r-email-creds
      edge_type: dependency

    - source: n-access
      target: n-profile
      resource: r-internal-comms
      edge_type: dependency

    - source: n-recon
      target: n-profile
      resource: r-org-structure
      edge_type: dependency

    - source: n-access
      target: n-selective-release
      resource: r-exfil-docs
      edge_type: dependency

    - source: n-profile
      target: n-selective-release
      resource: r-narrative-targets
      edge_type: dependency

    - source: n-persona-creation
      target: n-selective-release
      resource: r-dcleaks-persona
      edge_type: dependency

    - source: n-persona-creation
      target: n-selective-release
      resource: r-guccifer-persona
      edge_type: dependency

    - source: n-selective-release
      target: n-amplification
      resource: r-public-docs
      edge_type: dependency

    - source: n-selective-release
      target: n-amplification
      resource: r-media-attention
      edge_type: enables
```

### Analysis Output (expected)

**Critical path:** recon -> spearphish -> access -> selective-release -> amplification (261+ days)

**Critical dependencies:**
1. `n-spearphish -> n-access` (r-email-creds): if credential harvesting fails, the entire downstream chain collapses. This is the single highest-impact intervention point.
2. `n-access -> n-selective-release` (r-exfil-docs): without documents, there is nothing to release. Second highest impact.

**Top interventions:**
1. **Phishing defense** (breaks n-spearphish -> n-access): MFA, security awareness training, email filtering. Disables 4 downstream nodes. Cost: moderate. Priority: highest.
2. **Data loss prevention** (breaks n-access -> n-selective-release): DLP monitoring on email exfiltration. Disables 2 downstream nodes. Cost: moderate. Priority: high.
3. **Platform persona detection** (breaks n-persona-creation -> n-selective-release): detecting synthetic personas before they can publish. Disables 2 downstream nodes. Cost: high (platform cooperation required). Priority: moderate.
4. **Media literacy / SCT-007 inoculation** (weakens n-amplification): pre-bunking, inoculation training. Does not break the chain but reduces recursive infection potential. Cost: high (population-scale). Priority: long-term.

---

## 8. Storage Design

### 8.1 Chain Files

Chains are stored as YAML files in a `chains/` directory. This makes them version-controllable, human-readable, and diffable.

```
chains/
    apt28_election_2016.yaml
    lazarus_social_engineering.yaml
    custom/
        my_scenario.yaml
```

### 8.2 SQLite Index

A lightweight SQLite database indexes chain metadata for search and cross-chain analysis.

```sql
CREATE TABLE chains (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    classification TEXT,
    file_path TEXT NOT NULL,
    node_count INTEGER,
    edge_count INTEGER,
    actor_count INTEGER,
    date_range_start TIMESTAMP,
    date_range_end TIMESTAMP,
    tags TEXT,                    -- JSON array
    last_analyzed TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chain_nodes (
    chain_id TEXT NOT NULL REFERENCES chains(id),
    node_id TEXT NOT NULL,
    node_type TEXT,
    attack_ids TEXT,             -- JSON array
    disarm_ids TEXT,             -- JSON array
    sct_codes TEXT,              -- JSON array
    PRIMARY KEY (chain_id, node_id)
);

CREATE TABLE analysis_results (
    chain_id TEXT NOT NULL REFERENCES chains(id),
    analysis_type TEXT NOT NULL, -- "critical_path", "interventions", "timeline"
    result_json TEXT NOT NULL,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chain_id, analysis_type)
);
```

---

## 9. CLI Interface

```
threadmap validate <chain.yaml>         Validate chain structure and dependencies
threadmap analyze <chain.yaml>          Run full analysis (critical path, dependencies, interventions)
threadmap timeline <chain.yaml>         Compute and display temporal schedule
threadmap export <chain.yaml> --format  Export to JSON, DOT (Graphviz), or Markdown
threadmap import-profile <profile.json> Convert HoleSpawn profile to ThreadMap Resources
threadmap enrich <chain.yaml>           Auto-populate ATT&CK/DISARM references
threadmap serve                         Start visualization web server
threadmap list                          List all indexed chains
threadmap search <query>                Search chains by tag, technique, or actor
```

---

## 10. Security Considerations

ThreadMap models offensive operations in detail. This is dual-use by nature. The same models that help defenders prioritize interventions could theoretically help attackers plan operations.

**Mitigations:**
- Chain files can be marked with classification levels
- The tool focuses analytical output on defensive interventions, not operational planning
- Template library draws exclusively from publicly reported operations
- No automation of actual attack execution; this is a modeling and analysis tool only

---

## 11. Dependencies

```
# Core
pydantic>=2.0
networkx>=3.0
pyyaml>=6.0
click>=8.0
rich>=13.0          # CLI output formatting

# Visualization (Phase 3)
fastapi>=0.100
uvicorn>=0.20
jinja2>=3.0

# Integration
aiosqlite>=0.19     # ThreatMouth DB access
httpx>=0.25         # ATT&CK STIX fetching

# LLM (Phase 4)
anthropic>=0.30

# Testing
pytest>=7.0
pytest-asyncio>=0.21
```

---

## 12. Prerequisites

Do not begin implementation until:

1. ThreatMouth is delivering daily intelligence (operational)
2. HoleSpawn network profiling v2 is stable (operational)
3. Operator has studied 20+ real APT campaign reports through ThreatMouth
4. Operator has internalized hybrid operation patterns sufficient to model them accurately
5. DISARM framework taxonomy is understood at the tactic level

Domain knowledge precedes tool construction. The tool crystallizes understanding; it does not replace it.

---

**Document version:** 0.2.0
**Classification:** Research
**Distribution:** Internal + Public (GitHub)
