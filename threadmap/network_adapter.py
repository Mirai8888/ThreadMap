"""
Adapter: HoleSpawn NetworkEngine -> ThreadMap chain entities.

Converts network operational intelligence into ThreadMap's entity model
so that network-derived operations can be modeled as hybrid chains.

Usage:
    from holespawn.network.engine import NetworkEngine
    from threadmap.network_adapter import network_to_chain

    engine = NetworkEngine(graph)
    intel = engine.analyze()
    plan = engine.plan_operation(objective="reach", target_nodes=["dave"])
    chain = network_to_chain(intel, plan, campaign_name="OpName")
"""

from __future__ import annotations

import logging
from typing import Any

from .chain import HybridChain
from .models import (
    Action,
    ActionDomain,
    Actor,
    ActorType,
    Capability,
    CapabilityType,
    EdgeType,
    Effect,
    EffectType,
    Infrastructure,
    InfrastructureType,
    Narrative,
    NarrativeType,
    Relationship,
    Target,
)

logger = logging.getLogger(__name__)


def _role_to_actor_type(role: str) -> ActorType:
    """Map network engine role to ThreadMap actor type."""
    mapping = {
        "hub": ActorType.STATE,
        "bridge": ActorType.PROXY,
        "seed": ActorType.STATE,
        "amplifier": ActorType.AUTOMATED,
        "gatekeeper": ActorType.PROXY,
        "peripheral": ActorType.HACKTIVIST,
    }
    return mapping.get(role, ActorType.PROXY)


def network_to_chain(
    intel: Any,
    plan: Any | None = None,
    campaign_name: str = "Network Operation",
) -> HybridChain:
    """
    Convert NetworkEngine intel (and optional OperationPlan) into a
    ThreadMap Chain for hybrid operation modeling.

    Creates:
    - Actors from top network nodes (by influence)
    - Infrastructure from detected communities
    - Actions from operation plan entry/amplification steps
    - Relationships from influence paths
    - Targets from plan target nodes
    - Effects from estimated reach

    Args:
        intel: NetworkIntel from engine.analyze()
        plan: Optional OperationPlan from engine.plan_operation()
        campaign_name: name for the chain

    Returns:
        Chain populated with network-derived entities
    """
    chain = HybridChain(chain_id=campaign_name.lower().replace(" ", "-"), name=campaign_name)

    # Create actors from top influential nodes
    top_nodes = intel.top_nodes(by="influence_score", n=20)
    for op in top_nodes:
        if op.influence_score <= 0:
            continue
        actor = Actor(
            id=f"actor-{op.node}",
            name=op.node,
            actor_type=_role_to_actor_type(op.role),
            capabilities=[op.role],
            attribution_confidence=min(op.influence_score, 1.0),
        )
        chain.add_entity(actor)

    # Create infrastructure from communities
    for cid, members in intel.communities.items():
        infra = Infrastructure(
            id=f"community-{cid}",
            name=f"Community {cid} ({len(members)} members)",
            infra_type=InfrastructureType.SOCIAL_MEDIA,
            reach_estimate=str(len(members)),
            detection_difficulty=0.3,
        )
        chain.add_entity(infra)

    # If we have an operation plan, model it as a chain of actions
    if plan:
        _add_plan_entities(chain, plan, intel)

    return chain


def _add_plan_entities(chain: HybridChain, plan: Any, intel: Any) -> None:
    """Add operation plan as chain actions, targets, and relationships."""

    # Entry points become initial recon/position actions
    prev_action_id = None
    for i, ep in enumerate(plan.entry_points):
        action = Action(
            id=f"entry-{i}",
            name=f"Position at {ep['node']}",
            description=f"Establish presence via {ep.get('role', 'unknown')} node (influence: {ep.get('influence_score', 0):.3f})",
            domain=ActionDomain.COGNITIVE,
            actor_id=f"actor-{ep['node']}" if f"actor-{ep['node']}" in {e.id for e in chain.entities.values()} else None,
            success_probability=min(ep.get("influence_score", 0.5), 0.95),
        )
        chain.add_entity(action)

        if prev_action_id:
            chain.add_relationship(Relationship(
                source_id=prev_action_id,
                target_id=action.id,
                edge_type=EdgeType.ENABLES,
            ))
        prev_action_id = action.id

    # Amplification chain becomes sequential boost actions
    for i, amp in enumerate(plan.amplification_chain):
        action = Action(
            id=f"amplify-{i}",
            name=f"Amplify via {amp['node']}",
            description=f"Content amplification through {amp.get('role', 'unknown')} (influence: {amp.get('influence_score', 0):.3f})",
            domain=ActionDomain.COGNITIVE,
            actor_id=f"actor-{amp['node']}" if f"actor-{amp['node']}" in {e.id for e in chain.entities.values()} else None,
            success_probability=0.6,
        )
        chain.add_entity(action)

        if prev_action_id:
            chain.add_relationship(Relationship(
                source_id=prev_action_id,
                target_id=action.id,
                edge_type=EdgeType.AMPLIFIES,
            ))
        prev_action_id = action.id

    # Target nodes become targets
    if hasattr(plan, "entry_points") and plan.entry_points:
        # Use entry point downstream as proxy for targets
        target = Target(
            id="target-network",
            name=f"Target network segment",
            target_type="population",
            description=f"Estimated reach: {plan.estimated_reach_pct:.1%}",
        )
        chain.add_entity(target)

    # Weak links become capabilities (exploitable)
    for i, wl in enumerate(plan.weak_links):
        cap = Capability(
            id=f"weakness-{i}",
            name=f"Weak link: {wl['node']}",
            capability_type=CapabilityType.ACCESS,
            description=f"SPOF={wl.get('is_spof', False)}, fragmentation={wl.get('fragmentation_if_removed', 0):.3f}",
            perishable=True,
        )
        chain.add_entity(cap)

    # Risk nodes as narrative threats
    for i, rn in enumerate(plan.risk_nodes):
        narrative = Narrative(
            id=f"risk-{i}",
            name=f"Risk: {rn['node']}",
            narrative_type=NarrativeType.AMPLIFICATION,
            description=rn.get("reason", ""),
        )
        chain.add_entity(narrative)

    # Final effect
    effect = Effect(
        id="effect-reach",
        name=f"Network penetration ({plan.estimated_reach_pct:.0%} reach)",
        effect_type=EffectType.NARRATIVE_ADOPTION,
        severity=plan.estimated_reach_pct,
        reversibility=0.7,
    )
    chain.add_entity(effect)

    if prev_action_id:
        chain.add_relationship(Relationship(
            source_id=prev_action_id,
            target_id=effect.id,
            edge_type=EdgeType.TRIGGERS,
        ))
