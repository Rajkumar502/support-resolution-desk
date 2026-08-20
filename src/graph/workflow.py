import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph
from src.schemas.tickets import TicketResolutionState
from src.graph.nodes import (
    ingest_node,
    classify_node,
    refund_agent_node,
    technical_agent_node,
    general_agent_node,
    answer_composer_node,
    confidence_gate_node,
    handover_node
)

# 1. Setup SQLite Checkpointer connection for persistent thread memory
conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)

# 2. Build the workflow graph matching the architecture diagram
workflow = StateGraph(TicketResolutionState)

# Add all nodes
workflow.add_node("ingest_node", ingest_node)
workflow.add_node("classify_node", classify_node)
workflow.add_node("refund_agent", refund_agent_node)
workflow.add_node("technical_agent", technical_agent_node)
workflow.add_node("general_agent", general_agent_node)
workflow.add_node("answer_composer", answer_composer_node)
workflow.add_node("confidence_gate", confidence_gate_node)
workflow.add_node("handover_node", handover_node)

# Entry point
workflow.set_entry_point("ingest_node")

# Conditional edge after ingest: if an escalation reason was flagged, go straight to handover
workflow.add_conditional_edges(
    "ingest_node",
    lambda state: "handover_node" if getattr(state, "escalation_reason", None) else "classify_node",
    {
        "handover_node": "handover_node",
        "classify_node": "classify_node"
    }
)

# --- 3-WAY INTENT ROUTER ---
def route_intent(state: TicketResolutionState) -> str:
    """Routes classified tickets to the appropriate specialized agent branch."""
    if not state.classification:
        return "general_agent"
    
    category = state.classification.category.value
    if category in ["order_status", "returns"]:
        return "refund_agent"
    elif category == "subscriptions":
        return "technical_agent"
    else:
        return "general_agent"

# Add conditional 3-way routing from classifier
workflow.add_conditional_edges(
    "classify_node",
    route_intent,
    {
        "refund_agent": "refund_agent",
        "technical_agent": "technical_agent",
        "general_agent": "general_agent"
    }
)

# All 3 specialist agents converge into the Answer Composer
workflow.add_edge("refund_agent", "answer_composer")
workflow.add_edge("technical_agent", "answer_composer")
workflow.add_edge("general_agent", "answer_composer")

# Linear flow from composer to confidence gate
workflow.add_edge("answer_composer", "confidence_gate")

# Conditional routing from confidence gate (Auto Reply vs Human Queue)
workflow.add_conditional_edges(
    "confidence_gate",
    lambda state: "handover_node" if not state.confidence_gate_passed else "__end__",
    {
        "handover_node": "handover_node",
        "__end__": "__end__"
    }
)
workflow.add_edge("handover_node", "__end__")

# 3. Compile graph with checkpointer
graph = workflow.compile(checkpointer=memory)