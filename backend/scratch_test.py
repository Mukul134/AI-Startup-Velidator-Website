from enum import Enum
from sqlalchemy import Enum as SAEnum

class ProjectStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# 1. Without values_callable
type_without = SAEnum(ProjectStatus, name="project_status")
processor_without = type_without.bind_processor(None)
val_without = processor_without(ProjectStatus.PENDING) if processor_without else ProjectStatus.PENDING

# 2. With values_callable
type_with = SAEnum(ProjectStatus, name="project_status", values_callable=lambda x: [e.value for e in x])
processor_with = type_with.bind_processor(None)
val_with = processor_with(ProjectStatus.PENDING) if processor_with else ProjectStatus.PENDING

print(f"Without values_callable: {val_without!r} (type: {type(val_without).__name__})")
print(f"With values_callable: {val_with!r} (type: {type(val_with).__name__})")
