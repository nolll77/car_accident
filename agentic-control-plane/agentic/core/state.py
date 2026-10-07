"""
StateMachine stricte : un agent ne choisit jamais son état suivant.
"""

from __future__ import annotations


class InvalidTransition(Exception):
    pass


TRANSITIONS: dict[str, tuple[str, ...]] = {
    "DETECTED": ("INVESTIGATING",),
    "INVESTIGATING": ("DIAGNOSED", "FAILED"),
    "DIAGNOSED": ("PLANNED", "FAILED"),
    "PLANNED": ("AWAITING_APPROVAL", "EXECUTING", "DENIED"),
    "AWAITING_APPROVAL": ("EXECUTING", "DENIED", "CANCELLED"),
    "EXECUTING": ("RESOLVED", "FAILED"),
    "FAILED": ("ESCALATED",),
    "RESOLVED": (),
    "DENIED": (),
    "CANCELLED": (),
    "ESCALATED": (),
}


class StateMachine:
    def __init__(self, initial: str = "DETECTED"):
        self.current = initial
        self.trace: list[str] = [initial]

    def transition(self, target: str) -> None:
        allowed = TRANSITIONS.get(self.current, ())
        if target not in allowed:
            raise InvalidTransition(
                f"Transition illégale : {self.current} -> {target}. "
                f"Autorisées depuis {self.current} : {allowed}"
            )
        self.current = target
        self.trace.append(target)
