"""Core entity models for ThreadMap hybrid operation chains.

Seven entity types representing the components of hybrid operations:
Actor, Action, Capability, Infrastructure, Narrative, Target, Effect.

These map to the spec's detailed model (Actor, Node, Resource/Capability,
Platform/Infrastructure, cognitive nodes as Narrative, Target, and
downstream behavioral_change as Effect).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# --- Enums ---

class ActorType(str, Enum):
    STATE = "state"
    PROXY = "proxy"
    HACKTIVIST = "hacktivist"
    CRIMINAL = "criminal"
    AUTOMATED = "automated"
    INSIDER = "insider"


class ActionDomain(str, Enum):
    CYBER = "cyber"
    COGNITIVE = "cognitive"
    PHYSICAL = "physical"
    HYBRID = "hybrid"


class CapabilityType(str, Enum):
    EXPLOIT = "exploit"
    TOOLING = "tooling"
    TRADECRAFT = "tradecraft"
    ACCESS = "access"
    DATA = "data"


class InfrastructureType(str, Enum):
    SOCIAL_MEDIA = "social_media"
    EMAIL = "email"
    MESSAGING = "messaging"
    SERVER = "server"
    DOMAIN = "domain"
    PHYSICAL = "physical"
    MEDIA = "media"
    GOVERNMENT = "government"


class NarrativeType(str, Enum):
    DISINFORMATION = "disinformation"
    PROPAGANDA = "propaganda"
    LEAK = "leak"
    AMPLIFICATION = "amplification"
    FRAMING = "framing"


class EffectType(str, Enum):
    BEHAVIORAL_CHANGE = "behavioral_change"
    DATA_LOSS = "data_loss"
    ACCESS_GAINED = "access_gained"
    REPUTATION_DAMAGE = "reputation_damage"
    OPERATIONAL_DISRUPTION = "operational_disruption"
    NARRATIVE_ADOPTION = "narrative_adoption"


class EdgeType(str, Enum):
    DEPENDENCY = "dependency"
    ENABLES = "enables"
    AMPLIFIES = "amplifies"
    TRIGGERS = "triggers"


# --- Entity Models ---

class Actor(BaseModel):
    """An entity that executes operations."""
    id: str
    name: str
    actor_type: ActorType
    capabilities: list[str] = Field(default_factory=list)
    known_aliases: list[str] = Field(default_factory=list)
    attribution_confidence: float = 0.5


class Action(BaseModel):
    """A single operation step - technical, cognitive, or hybrid."""
    id: str
    name: str
    description: str = ""
    domain: ActionDomain = ActionDomain.CYBER
    attack_ids: list[str] = Field(default_factory=list)
    disarm_ids: list[str] = Field(default_factory=list)
    sct_codes: list[str] = Field(default_factory=list)
    actor_id: str | None = None
    platform_id: str | None = None
    tools: list[str] = Field(default_factory=list)
    duration_hours: float | None = None
    success_probability: float = 0.5
    detection_surface: list[str] = Field(default_factory=list)


class Capability(BaseModel):
    """A resource or capability that flows between actions."""
    id: str
    name: str
    capability_type: CapabilityType
    description: str = ""
    perishable: bool = False
    ttl_hours: float | None = None


class Infrastructure(BaseModel):
    """A platform or infrastructure where operations execute."""
    id: str
    name: str
    infra_type: InfrastructureType
    reach_estimate: str | None = None
    detection_difficulty: float = 0.5


class Narrative(BaseModel):
    """A cognitive/information operation narrative thread."""
    id: str
    name: str
    narrative_type: NarrativeType
    description: str = ""
    target_audience: str | None = None
    sct_codes: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)


class Target(BaseModel):
    """A target of operations - individual, organization, or population."""
    id: str
    name: str
    target_type: str = "organization"  # individual, organization, population
    description: str = ""
    vulnerabilities: list[str] = Field(default_factory=list)


class Effect(BaseModel):
    """An outcome or impact of the operation chain."""
    id: str
    name: str
    effect_type: EffectType
    description: str = ""
    severity: float = 0.5  # 0.0 to 1.0
    reversibility: float = 0.5  # 0.0 (permanent) to 1.0 (trivially reversible)


class Relationship(BaseModel):
    """An edge between two entities in the chain."""
    source_id: str
    target_id: str
    edge_type: EdgeType = EdgeType.DEPENDENCY
    resource_id: str | None = None
    description: str = ""


# Union type for all entities
Entity = Actor | Action | Capability | Infrastructure | Narrative | Target | Effect
