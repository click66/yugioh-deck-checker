from dataclasses import dataclass, field
from typing import Any, Dict, List
from datetime import datetime
import uuid


@dataclass
class Job:
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    payload: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    result: Dict[str, Any] | None = None
    error: str | None = None

@dataclass
class BatchJob:
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    jobs: List[Job] = field(default_factory=list)
