import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_openai import ChatOpenAI

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

    agent_model = ChatOpenAI(
        model=model or os.getenv("VITESS_AGENT_MODEL", "alias-large"),
        base_url=os.getenv("BLABLADOR_BASE_URL"),
        api_key=os.getenv("BLABLADOR_API_KEY"),
    )

    return create_agent(
        model=agent_model,
        tools=create_vitess_tools(collection),
        system_prompt=VITESS_RESEARCH_AGENT_PROMPT,
        name="vitess_research_agent",
    )


def ask_hybrid_agent(
    query: str,
    collection,
    model: str | None = None,
) -> str:
    agent = build_vitess_research_agent(
        collection=collection,
        model=model,
    )

    result = agent.invoke(
        {"messages": [HumanMessage(content=query)]}
    )

    messages = result.get("messages", [])

    # Normal case: the agent generated a final textual answer.
    for message in reversed(messages):
        if not isinstance(message, AIMessage):
            continue

        content = message.content

        # Ignore AI messages that only contain tool calls.
        if message.tool_calls:
            continue

        if isinstance(content, str) and content.strip():
            return content.strip()

    # Fallback case: retrieval succeeded, but the agent produced no final text.
    retrieved_context: list[str] = []

    for message in messages:
        if not isinstance(message, ToolMessage):
            continue

        content = message.content

        if isinstance(content, str) and content.strip():
            retrieved_context.append(content.strip())

    if not retrieved_context:
        return (
            "I could not retrieve enough information from the "
            "VITESS documentation to answer this question reliably."
        )

    # Remove duplicate tool outputs while preserving their order.
    unique_context: list[str] = []
    seen: set[str] = set()

    for context_block in retrieved_context:
        if context_block in seen:
            continue

        seen.add(context_block)
        unique_context.append(context_block)

    context = "\n\n".join(unique_context)

    # Prevent excessively large fallback prompts.
    max_context_chars = 30000

    if len(context) > max_context_chars:
        context = context[:max_context_chars]

    answer_model = ChatOpenAI(
        model=model or os.getenv("VITESS_AGENT_MODEL", "alias-large"),
        base_url=os.getenv("BLABLADOR_BASE_URL"),
        api_key=os.getenv("BLABLADOR_API_KEY"),
    )

    fallback_response = answer_model.invoke(
        [
            SystemMessage(
                content=(
                    "You answer questions about VITESS documentation. "
                    "Use only the retrieved documentation supplied below. "
                    "Do not add information from memory or outside knowledge. "
                    "If the documentation does not fully support an answer, "
                    "state the limitation clearly. "
                    "Provide a clear and concise technical answer."
                )
            ),
            HumanMessage(
                content=(
                    f"User question:\n{query}\n\n"
                    "Retrieved VITESS documentation:\n"
                    f"{context}"
                )
            ),
        ]
    )

    fallback_content = fallback_response.content

    if isinstance(fallback_content, str) and fallback_content.strip():
        return fallback_content.strip()

    return (
        "The relevant VITESS documentation was retrieved, "
        "but no final textual answer could be generated."
    )