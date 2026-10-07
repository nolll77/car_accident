from app.domain.executions.models import ExecutionStatus

ALLOWED_TRANSITIONS = {
    ExecutionStatus.QUEUED: {
        ExecutionStatus.RUNNING,
        ExecutionStatus.CANCELLED,
    },
    ExecutionStatus.RUNNING: {
        ExecutionStatus.SUCCEEDED,
        ExecutionStatus.FAILED,
        ExecutionStatus.CANCELLED,
    },
    ExecutionStatus.SUCCEEDED: set(),
    ExecutionStatus.FAILED: set(),
    ExecutionStatus.CANCELLED: set(),
}


def can_transition(current: ExecutionStatus, target: ExecutionStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


def transition(current: ExecutionStatus, target: ExecutionStatus) -> ExecutionStatus:
    if not can_transition(current, target):
        raise ValueError(f"Invalid execution transition: {current} -> {target}")
    return target
