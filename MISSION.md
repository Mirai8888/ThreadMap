# MISSION.md -- ThreadMap (信線図)

**Status:** MVP Complete
**Last Updated:** 2026-02-19

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
- **MVP Implementation (v0.1.0)**:
  - `threadmap/models.py` — 7 entity types: Actor, Action, Capability, Infrastructure, Narrative, Target, Effect (Pydantic v2)
  - `threadmap/chain.py` — HybridChain class: NetworkX directed graph with add_entity(), add_relationship(), get_chain(), get_critical_path(), intervention_score()
  - `threadmap/analysis.py` — Chain analysis: find_chokepoints(), narrative_threads(), capability_requirements(), intervention_ranking()
  - `threadmap/io.py` — Import/export: JSON roundtrip, STIX 2.1 bundle, Markdown report generation
  - `threadmap/examples/apt28_2016.py` — APT28 2016 election interference worked example (11 entities, 9 relationships, all 7 entity types)
  - `tests/test_threadmap.py` — 24 tests (all passing): models, chain ops, analysis, I/O, APT28 example
  - `pyproject.toml` — Package configuration

### Queued (post-MVP)
1. Template library: 5+ chains from public threat intelligence
2. CLI interface (Click): validate, analyze, export commands
3. Framework integration: ATT&CK STIX loader, DISARM matrix loader
4. HoleSpawn/ThreatMouth/seithar-cogdef integrations
5. Visualization: Cytoscape.js web frontend
6. Advanced: cross-chain coverage scoring, LLM-assisted chain construction

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
| 2026-02-19 | MVP v0.1.0: models, chain, analysis, I/O, APT28 example, 24 tests |
| 2026-02-18 | Architecture spec v0.2.0 (docs/SPEC.md) |
| 2026-02-18 | MISSION.md created |
| 2026-02-08 | Initial conceptual README |

## Dependencies

Python 3.11+, Pydantic v2, NetworkX, PyYAML, Rich. See docs/SPEC.md section 11 for full list.
