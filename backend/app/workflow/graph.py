"""
LangGraph compilation for CivicShield Incident Response Workflow.
Supports Shadow Mode, Supervised Mode, and Autonomous Mode.
"""

from langgraph.graph import END, START, StateGraph

from .edges import route_after_plan, route_after_safety, route_after_verify
from .nodes import (
    await_approval_node,
    diagnose_node,
    escalate_node,
    execute_node,
    intake_node,
    plan_node,
    safety_gate_node,
    shadow_node,
    verify_node,
)
from .state import CivicShieldState


def build_civicshield_graph():
    """Assemble and compile the stateful incident response graph."""
    builder = StateGraph(CivicShieldState)

    # 1. Register Nodes
    builder.add_node("intake", intake_node)
    builder.add_node("diagnose", diagnose_node)
    builder.add_node("plan", plan_node)
    builder.add_node("safety_gate", safety_gate_node)
    builder.add_node("shadow", shadow_node)
    builder.add_node("await_approval", await_approval_node)
    builder.add_node("execute", execute_node)
    builder.add_node("verify", verify_node)
    builder.add_node("escalate", escalate_node)

    # 2. Sequential Edges
    builder.add_edge(START, "intake")
    builder.add_edge("intake", "diagnose")
    builder.add_edge("diagnose", "plan")
    builder.add_edge("execute", "verify")
    builder.add_edge("shadow", END)
    builder.add_edge("await_approval", END)
    builder.add_edge("escalate", END)

    # 3. Conditional Branching Edges
    builder.add_conditional_edges(
        "plan",
        route_after_plan,
        {
            "diagnose": "diagnose",
            "safety_gate": "safety_gate",
            "escalate": "escalate",
            "end": END,
        },
    )

    builder.add_conditional_edges(
        "safety_gate",
        route_after_safety,
        {
            "execute": "execute",
            "escalate": "escalate",
            "shadow": "shadow",
            "await_approval": "await_approval",
        },
    )

    builder.add_conditional_edges(
        "verify",
        route_after_verify,
        {
            "end": END,
            "diagnose": "diagnose",
            "escalate": "escalate",
        },
    )

    return builder.compile()


# Compiled singleton workflow
civicshield_workflow = build_civicshield_graph()
