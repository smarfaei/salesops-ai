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


class UserRole(str, Enum):
    ADMIN = "admin"
    SALES_MANAGER = "sales_manager"
    SALES_REP = "sales_rep"
    VIEWER = "viewer"


class AuditEventType(str, Enum):
    LOGIN_SUCCEEDED = "login_succeeded"
    LEAD_CREATED = "lead_created"
    LEAD_UPDATED = "lead_updated"
    LEAD_DELETED = "lead_deleted"
    OWNER_CHANGED = "owner_changed"
    PIPELINE_CHANGED = "pipeline_changed"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_CANCELLED = "task_cancelled"
    ACTIVITY_ADDED = "activity_added"
    INTELLIGENCE_GENERATED = "intelligence_generated"
    USER_CREATED = "user_created"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    ROLE_CHANGED = "role_changed"
