from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import tools_condition
from ai_companion.graph.edges import (
    select_workflow,
    should_summarize_conversation,
    decision_router,
    should_we_loop
)
from ai_companion.graph.nodes import (
    audio_node,
    conversation_node,
    image_node,
    memory_extraction_node,
    memory_injection_node,
    router_node,
    summarize_conversation_node,
    find_intent,
    SQL_Generator,
    Ambiguous_Node,
    Unsafe_Node,
    Evaluator,
    sales_node,
    email_sender_node
)
from ai_companion.graph.state import AICompanionState, SQLWorkflowState
from ai_companion.graph.tools import tool_node

def create_workflow_graph():
    graph_builder = StateGraph(AICompanionState)

    graph_builder.add_node("memory_extraction_node", memory_extraction_node)
    graph_builder.add_node('router_node', router_node)
    graph_builder.add_node('memory_injection_node', memory_injection_node)
    graph_builder.add_node('conversation_node', conversation_node)
    graph_builder.add_node('audio_node', audio_node)
    graph_builder.add_node('image_node', image_node)
    graph_builder.add_node('summarize_conversation_node', summarize_conversation_node)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_edge(START, 'memory_extraction_node')
    graph_builder.add_edge('memory_extraction_node', 'router_node')
    graph_builder.add_edge('router_node', 'memory_injection_node')

    graph_builder.add_conditional_edges('memory_injection_node', select_workflow, {'conversation_node' : 'conversation_node', "image_node": "image_node", "audio_node": "audio_node"})
    
    graph_builder.add_conditional_edges('conversation_node', tools_condition, {'tools' : 'tools', '__end__' : "summarize_conversation_node"})
    graph_builder.add_edge("tools", "conversation_node")

    graph_builder.add_conditional_edges('audio_node', should_summarize_conversation, {'summarize_conversation_node' : 'summarize_conversation_node', END: END})
    graph_builder.add_conditional_edges('image_node', should_summarize_conversation, {'summarize_conversation_node' : 'summarize_conversation_node', END: END})
    graph_builder.add_edge('summarize_conversation_node', END)

    return graph_builder

def create_subgraph():
    
    graph_builder = StateGraph(SQLWorkflowState)
    graph_builder.add_node("find_intent", find_intent)
    graph_builder.add_node('Ambiguous_Node', Ambiguous_Node)
    graph_builder.add_node('Unsafe_Node', Unsafe_Node)
    graph_builder.add_node('SQL_Generator', SQL_Generator)
    graph_builder.add_node('Evaluator', Evaluator)
    graph_builder.add_node("sales_node", sales_node)
    graph_builder.add_node("email_sender_node", email_sender_node)

    graph_builder.add_edge(START, 'find_intent')
    graph_builder.add_conditional_edges('find_intent', decision_router, {'Ambiguous': 'Ambiguous_Node', 'Unsafe': 'Unsafe_Node', 'Valid' : 'SQL_Generator'})
    graph_builder.add_edge('SQL_Generator', 'Evaluator')
    graph_builder.add_conditional_edges('Evaluator', should_we_loop, {
        "rewrite" : "SQL_Generator",
        "sales_agent" : 'sales_node',
        'back' : END
    })
    graph_builder.add_edge('sales_node', 'email_sender_node')

    graph_builder.add_edge("email_sender_node", END)

    return graph_builder


if __name__ == "__main__":
    try:
        image_bytes = create_workflow_graph().compile().get_graph().draw_mermaid_png()
        subgraph_image_bytes = create_subgraph().compile().get_graph().draw_mermaid_png()
        
        with open("graph_visualization.png", "wb") as f:
            f.write(image_bytes)

        with open("subgraph_visualization.png", "wb") as f:
            f.write(subgraph_image_bytes)
        
        print("Successfully saved graph visualization")
        
    except Exception as e:
        print(f"Could not generate PNG. Error: {e}")