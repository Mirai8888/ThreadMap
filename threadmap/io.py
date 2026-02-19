"""Import/export: JSON, STIX 2.1 bundle format, Markdown report generation."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from .chain import HybridChain
from .models import (
    Actor, Action, Capability, Infrastructure, Narrative, Target, Effect,
    Relationship, EdgeType,
    ActorType, ActionDomain, CapabilityType, InfrastructureType,
    NarrativeType, EffectType,
)
from .analysis import find_chokepoints, intervention_ranking


# --- JSON ---

def to_json(chain: HybridChain) -> str:
    """Export chain to JSON string."""
    data = {
        "id": chain.chain_id,
        "name": chain.name,
        "description": chain.description,
        "entities": {eid: e.model_dump(mode="json") | {"_type": type(e).__name__}
                     for eid, e in chain.entities.items()},
        "relationships": chain.relationships,
    }
    return json.dumps(data, indent=2, default=str)


def from_json(json_str: str) -> HybridChain:
    """Import chain from JSON string."""
    data = json.loads(json_str)
    chain = HybridChain(data["id"], data["name"], data.get("description", ""))

    type_map = {
        "Actor": Actor, "Action": Action, "Capability": Capability,
        "Infrastructure": Infrastructure, "Narrative": Narrative,
        "Target": Target, "Effect": Effect,
    }

    for eid, edata in data["entities"].items():
        etype = edata.pop("_type")
        cls = type_map[etype]
        chain.add_entity(cls(**edata))

    for rel in data["relationships"]:
        chain.add_relationship(Relationship(
            source_id=rel["source"],
            target_id=rel["target"],
            edge_type=EdgeType(rel.get("edge_type", "dependency")),
            resource_id=rel.get("resource_id"),
            description=rel.get("description", ""),
        ))

    return chain


# --- STIX 2.1 ---

_ENTITY_TO_STIX = {
    "Actor": "threat-actor",
    "Action": "attack-pattern",
    "Capability": "tool",
    "Infrastructure": "infrastructure",
    "Narrative": "campaign",
    "Target": "identity",
    "Effect": "impact",
}


def to_stix_bundle(chain: HybridChain) -> dict[str, Any]:
    """Export chain as a STIX 2.1 bundle."""
    objects = []

    for eid, entity in chain.entities.items():
        etype = type(entity).__name__
        stix_type = _ENTITY_TO_STIX.get(etype, "x-threadmap-entity")
        stix_obj = {
            "type": stix_type,
            "spec_version": "2.1",
            "id": f"{stix_type}--{entity.id}",
            "name": entity.name,
            "created": datetime.utcnow().isoformat() + "Z",
            "modified": datetime.utcnow().isoformat() + "Z",
        }
        if hasattr(entity, "description") and entity.description:
            stix_obj["description"] = entity.description
        # Store full ThreadMap data in extension
        stix_obj["x_threadmap"] = entity.model_dump(mode="json")
        objects.append(stix_obj)

    for rel in chain.relationships:
        src_entity = chain.get_entity(rel["source"])
        tgt_entity = chain.get_entity(rel["target"])
        src_type = _ENTITY_TO_STIX.get(type(src_entity).__name__, "x-threadmap-entity")
        tgt_type = _ENTITY_TO_STIX.get(type(tgt_entity).__name__, "x-threadmap-entity")
        objects.append({
            "type": "relationship",
            "spec_version": "2.1",
            "id": f"relationship--{rel['source']}--{rel['target']}",
            "relationship_type": rel.get("edge_type", "dependency"),
            "source_ref": f"{src_type}--{rel['source']}",
            "target_ref": f"{tgt_type}--{rel['target']}",
            "created": datetime.utcnow().isoformat() + "Z",
            "modified": datetime.utcnow().isoformat() + "Z",
        })

    return {
        "type": "bundle",
        "id": f"bundle--{chain.chain_id}",
        "objects": objects,
    }


# --- Markdown Report ---

def to_markdown(chain: HybridChain) -> str:
    """Generate a Markdown analysis report for the chain."""
    lines = [
        f"# ThreadMap Report: {chain.name}",
        "",
        f"**Chain ID:** `{chain.chain_id}`",
        "",
    ]

    if chain.description:
        lines += [chain.description, ""]

    # Entities summary
    lines += ["## Entities", ""]
    by_type: dict[str, list] = {}
    for eid, entity in chain.entities.items():
        tname = type(entity).__name__
        by_type.setdefault(tname, []).append(entity)

    for tname, entities in by_type.items():
        lines.append(f"### {tname}s ({len(entities)})")
        lines.append("")
        for e in entities:
            desc = getattr(e, "description", "") or ""
            lines.append(f"- **{e.name}** (`{e.id}`){': ' + desc if desc else ''}")
        lines.append("")

    # Relationships
    lines += ["## Relationships", ""]
    for rel in chain.relationships:
        etype = rel.get("edge_type", "?")
        lines.append(f"- `{rel['source']}` →[{etype}]→ `{rel['target']}`")
    lines.append("")

    # Critical path
    try:
        cp = chain.get_critical_path()
        lines += ["## Critical Path", "", " → ".join(f"`{n}`" for n in cp), ""]
    except Exception:
        pass

    # Top interventions
    try:
        interventions = intervention_ranking(chain)[:5]
        lines += ["## Top Intervention Points", ""]
        for i, iv in enumerate(interventions, 1):
            lines.append(
                f"{i}. **{iv['name']}** (`{iv['node_id']}`) — "
                f"score: {iv['score']}, downstream impact: {iv['downstream_impact']}"
            )
        lines.append("")
    except Exception:
        pass

    # Chokepoints
    try:
        cps = find_chokepoints(chain, top_n=5)
        lines += ["## Chokepoints", ""]
        for cp in cps:
            lines.append(f"- `{cp['node_id']}`: {cp['downstream_count']} downstream nodes")
        lines.append("")
    except Exception:
        pass

    return "\n".join(lines)
