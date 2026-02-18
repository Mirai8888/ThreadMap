# MISSION.md -- ThreadMap (信線図)

**Status:** Pre-development (architecture spec complete)
**Last Updated:** 2026-02-18

## Purpose

Hybrid operation chain modeling for the Seithar ecosystem. ThreadMap models how cognitive and technical operations chain together across time, platforms, and actors. It fills the gap between HoleSpawn (offense profiling), seithar-cogdef (defense scanning), and ThreatMouth (intelligence collection) by providing the sequencing and dependency layer that none of them address.

Primary analytical output: defensive intervention priorities ranked by impact, coverage, and cost. The tool answers the question "given limited defensive resources, where do we invest to break the most hybrid operation chains?"

## Current State

### Complete
- Conceptual architecture (README.md)
- Detailed architecture specification (docs/SPEC.md)
- Core data model design (Resource, Actor, Platform, Node, Edge, Chain)
- Analysis engine design (dependency resolution, critical path, intervention scoring)
- Integration points defined for HoleSpawn, seithar-cogdef, ThreatMouth
- Example chain modeled: APT28 2016 election interference
- Technology stack selected (Python, Pydantic, NetworkX, Click, FastAPI, Cytoscape.js)

### Blocked (prerequisites)
- Implementation blocked on domain knowledge prerequisites (see docs/SPEC.md section 12)
- Requires operational ThreatMouth + stable HoleSpawn network profiling
- Requires operator study of 20+ real APT campaign reports

### Queued (post-prerequisites)
1. MVP: Pydantic models, YAML chain serialization, CLI validate/analyze
2. Template library: 5+ chains from public threat intelligence
3. Framework integration: ATT&CK STIX loader, DISARM matrix loader
4. Visualization: Cytoscape.js web frontend
5. Advanced: cross-chain coverage scoring, LLM-assisted chain construction

## Ecosystem Role

```
HoleSpawn ──(profiles)──> ThreadMap <──(threats)── ThreatMouth
                              ^
                              |
                         (taxonomy)
                              |
                       seithar-cogdef
```

ThreadMap is the composition layer. It does not collect intelligence (ThreatMouth), profile targets (HoleSpawn), or scan content (seithar-cogdef). It chains their outputs into operation models and computes where to invest defensive effort.

## Recent Changes

| Date | Change |
|------|--------|
| 2026-02-18 | Architecture spec v0.2.0 (docs/SPEC.md) |
| 2026-02-18 | MISSION.md created |
| 2026-02-08 | Initial conceptual README |

## Dependencies

Python 3.11+, Pydantic v2, NetworkX, Click, PyYAML, Rich. See docs/SPEC.md section 11 for full list.
