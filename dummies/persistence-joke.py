from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from langchain_openrouter import ChatOpenRouter
from settings import Settings
from langgraph.checkpoint.memory import InMemorySaver

from model_config import get_model
from logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

model = get_model()


class JokeState(TypedDict):
    topic: str
    joke: str
    explanation: str


def generate_joke(state: JokeState):
    logger.info("Generating joke", topic=state["topic"])
    prompt = f"Generate a joke on the topic {state["topic"]}"
    response = model.invoke(prompt).content
    logger.info("Joke generated", topic=state["topic"], joke_length=len(response))
    logger.debug("Joke content", joke=response)
    return {"joke": response}


def generate_explanation(state: JokeState):
    logger.info("Generating explanation", topic=state["topic"])
    prompt = f"I made a joke on the topic {state["topic"]} but I also need an explanation of this joke {state["joke"]} in 1 line "
    response = model.invoke(prompt).content
    logger.info(
        "Explanation generated", topic=state["topic"], explanation_length=len(response)
    )
    logger.debug("Explanation content", explanation=response)
    return {"explanation": response}


SEPARATOR = "─" * 60
MAX_VALUE_WIDTH = 60


def shorten(value, width=MAX_VALUE_WIDTH):
    text = str(value).replace("\n", " ")
    return text if len(text) <= width else text[: width - 1] + "…"


def print_state_history(workflow, config):
    snapshots = list(workflow.get_state_history(config))
    thread_id = config["configurable"]["thread_id"]

    print(f"\n State history · thread {thread_id} · {len(snapshots)} checkpoints")
    print(f" {SEPARATOR}")
    for snapshot in reversed(snapshots):
        step = snapshot.metadata["step"]
        writes = snapshot.metadata.get("writes") or {}
        node = ", ".join(writes) or snapshot.metadata["source"]
        checkpoint_id = snapshot.config["configurable"]["checkpoint_id"][:8]
        next_nodes = ", ".join(snapshot.next) or "END"

        print(f"\n ● step {step:>2}  {node}")
        print(f"   checkpoint  {checkpoint_id}")
        print(f"   next        {next_nodes}")
        for key, value in snapshot.values.items():
            print(f"   {key:<12}{shorten(value)}")
    print(f"\n {SEPARATOR}\n")


graph = StateGraph(JokeState)

graph.add_node("Generate Joke", generate_joke)
graph.add_node("Generate Explanation", generate_explanation)
graph.add_edge(START, "Generate Joke")
graph.add_edge("Generate Joke", "Generate Explanation")
graph.add_edge("Generate Explanation", END)

checkpointer = InMemorySaver()

workflow = graph.compile(checkpointer=checkpointer)
logger.info("Graph compiled", nodes=["Generate Joke", "Generate Explanation"])

config1 = {"configurable": {"thread_id": "1"}}
logger.info("Invoking workflow", thread_id=config1["configurable"]["thread_id"])
result = workflow.invoke({"topic": "pizza"}, config=config1)
logger.info(
    "Workflow complete", thread_id=config1["configurable"]["thread_id"], result=result
)

print_state_history(workflow, config1)
