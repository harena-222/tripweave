from langgraph.graph import StateGraph, END
from core.state import TripWeaveState
from core.nodes import parse_meaning, retrieve_memory
# Initialize the StateGraph with our custom State definition
workflow = StateGraph(TripWeaveState)

# Add nodes to the graph
workflow.add_node("parse", parse_meaning)         # Node 1
workflow.add_node("memory", retrieve_memory)       # Node 2-A
# workflow.add_node("weather", fetch_weather)     # Node 2-B (Coming soon)
# workflow.add_node("plan", generate_final_plan)  # Node 3 (Coming soon)

# Define edges (the flow of data)
workflow.set_entry_point("parse")
workflow.add_edge("parse", "memory")
workflow.add_edge("memory", END) # Change END to next node once created

# Compile the graph into an executable app
compiled_graph = workflow.compile()