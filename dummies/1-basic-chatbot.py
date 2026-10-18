from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END

from langgraph.graph.message import add_messages

from IPython.display import Image, display

from model_config import get_model
from logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

model = get_model()


class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)

logger.info("graph_builder initialized", graph=str(graph_builder))

logger.info("model loaded", model=str(model))


def chatbot(state: State):
    return {"messages": model.invoke(state["messages"])}


graph_builder.add_node("llmchatbot", chatbot)
graph_builder.add_edge(START, "llmchatbot")
graph_builder.add_edge("llmchatbot", END)

graph = graph_builder.compile()


# try:
#     png_bytes = graph.get_graph().draw_mermaid_png()
#     with open("graph.png","wb") as f:
#         f.write(png_bytes)
# except Exception as e:
#     print("Error displaying graph:", e)


result = graph.invoke({"messages": "What is the capital of France?"})

logger.info("graph invocation complete", result=result)

logger.info(
    "Model Used", model=str(result["messages"][-1].response_metadata["model_name"])
)


for event in graph.stream(
    {
        "messages": "My life has been a living chaos recently where I am always confused and nothing makes sense"
    }
):
    node_name = list(event.keys())[0] if event else None
    logger.info(
        "stream event", node=node_name, output=event[node_name] if node_name else None
    )
