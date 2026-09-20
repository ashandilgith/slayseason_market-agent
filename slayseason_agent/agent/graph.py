from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage

from core.config import llm
from core.state import AgentState
from tools.financials import calculate_mer
from tools.marketing import calculate_cac

# Combine all tools into a single list for the LLM
jarvis_tools = [calculate_mer, calculate_cac]

# Bind to the LLM
llm_with_tools = llm.bind_tools(jarvis_tools)

def jarvis_node(state: AgentState):
    """The central reasoning engine."""
    sys_msg = SystemMessage(
        content=(
            "You are Jarvis, the SlaySeason intelligence layer. "
            f"The user's tenant_id is {state['tenant_id']}. Pass this EXACT ID to all tools. "
            "Rule 1: NEVER invent numbers. If a tool fails or returns 0, state the data is missing. "
            "Rule 2: Use calculate_mer for profit, revenue, or efficiency questions, and calculate_cac for customer acquisition and marketing spend questions."
        )
    )
    # Invoke the model
    response = llm_with_tools.invoke([sys_msg] + state["messages"])
    return {"messages": [response]}

# Build the Graph
builder = StateGraph(AgentState)
builder.add_node("jarvis", jarvis_node)
builder.add_node("tools", ToolNode(tools=jarvis_tools))

# Define flow
builder.add_edge(START, "jarvis")
builder.add_conditional_edges("jarvis", tools_condition)
builder.add_edge("tools", "jarvis")

# We leave compilation to app.py so Streamlit can inject the PostgresSaver session
def get_graph_builder():
    return builder