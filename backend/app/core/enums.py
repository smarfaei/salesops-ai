from enum import Enum


class PipelineStage(str, Enum):
    NEW = "New"
    QUALIFIED = "Qualified"
    CONTACTED = "Contacted"
    PROPOSAL = "Proposal"
    WON = "Won"
    LOST = "Lost"


class ActivityType(str, Enum):
    LEAD_CREATED = "lead_created"
    LEAD_UPDATED = "lead_updated"
    STAGE_CHANGED = "stage_changed"
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    NOTE = "note"


class ManualActivityType(str, Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    NOTE = "note"


class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
