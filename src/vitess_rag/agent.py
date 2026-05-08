import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import HumanMessage, SystemMessage

from .tools import create_vitess_tools

load_dotenv()


VITESS_RESEARCH_AGENT_PROMPT = SystemMessage(
    content=(
        "You are a VITESS documentation research agent.\n\n"
        "Your job is to answer questions using iterative retrieval over the VITESS documentation.\n"
        "Do not answer from memory. Use tool evidence only.\n\n"
        "Retrieval strategy:\n"
        "1. Start with the most appropriate retrieval tool.\n"
        "2. Inspect whether the returned context actually answers the question.\n"
        "3. If the result is incomplete, too broad, or off-topic, rewrite the query and search again.\n"
        "4. For command options like -z, -A, -H, -V, use vitess_option_lookup first.\n"
        "5. For module/section explanations, use vitess_module_lookup first.\n"
        "6. For general queries, use vitess_search.\n"
        "7. Use vitess_debug_retrieval only if retrieval seems wrong.\n\n"
        "Answering rules:\n"
        "- Use only tool output as your source of truth.\n"
        "- If a tool returns AMBIGUOUS_QUERY, ask the user to clarify the module.\n"
        "- If all searches fail, say you could not find a reliable answer.\n"
        "- Mention module/section/subsection when useful.\n"
        "- Keep answers concise and technical."
    )
)


def build_vitess_research_agent(collection, model: str | None = None):
    return create_agent(
        model=model or os.getenv("VITESS_AGENT_MODEL", "openai:gpt-5.4-mini"),
        tools=create_vitess_tools(collection),
        system_prompt=VITESS_RESEARCH_AGENT_PROMPT,
        name="vitess_research_agent",
    )


def ask_hybrid_agent(query: str, collection, model: str | None = None) -> str:
    agent = build_vitess_research_agent(
        collection=collection,
        model=model,
    )

    result = agent.invoke(
        {"messages": [HumanMessage(content=query)]}
    )

    return result["messages"][-1].content
