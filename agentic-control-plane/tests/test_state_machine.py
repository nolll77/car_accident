import pytest
from agentic.core.state import InvalidTransition, StateMachine


def test_valid_sequence():
    sm = StateMachine()
    for state in ["INVESTIGATING", "DIAGNOSED", "PLANNED", "EXECUTING", "RESOLVED"]:
        sm.transition(state)
    assert sm.current == "RESOLVED"


def test_cannot_skip_states():
    sm = StateMachine()
    with pytest.raises(InvalidTransition):
        sm.transition("EXECUTING")


def test_cannot_invent_states():
    sm = StateMachine()
    with pytest.raises(InvalidTransition):
        sm.transition("SUPER_RESOLVED")
