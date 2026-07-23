from langchain.messages import AIMessage, ToolMessage

from vitess_rag import agent as agent_module


class FakeAgent:
    def __init__(self, messages):
        self.messages = messages

    def invoke(self, payload):
        return {"messages": self.messages}


class FakeAnswerModel:
    def __init__(self, response_content):
        self.response_content = response_content
        self.received_messages = None

    def invoke(self, messages):
        self.received_messages = messages
        return AIMessage(content=self.response_content)


def test_ask_hybrid_agent_returns_final_ai_message(monkeypatch):
    fake_agent = FakeAgent(
        messages=[
            AIMessage(content="The guide module transports neutrons.")
        ]
    )

    monkeypatch.setattr(
        agent_module,
        "build_vitess_research_agent",
        lambda collection, model=None: fake_agent,
    )

    answer = agent_module.ask_hybrid_agent(
        query="What does the guide module do?",
        collection=object(),
    )

    assert answer == "The guide module transports neutrons."


def test_ask_hybrid_agent_ignores_ai_message_with_tool_calls(monkeypatch):
    tool_call_message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "vitess_search",
                "args": {"query": "guide"},
                "id": "tool-call-1",
                "type": "tool_call",
            }
        ],
    )

    fake_agent = FakeAgent(
        messages=[
            tool_call_message,
            AIMessage(content="Final grounded answer."),
        ]
    )

    monkeypatch.setattr(
        agent_module,
        "build_vitess_research_agent",
        lambda collection, model=None: fake_agent,
    )

    answer = agent_module.ask_hybrid_agent(
        query="Tell me about guide.",
        collection=object(),
    )

    assert answer == "Final grounded answer."


def test_ask_hybrid_agent_returns_failure_when_no_context(monkeypatch):
    fake_agent = FakeAgent(
        messages=[
            AIMessage(content=""),
        ]
    )

    monkeypatch.setattr(
        agent_module,
        "build_vitess_research_agent",
        lambda collection, model=None: fake_agent,
    )

    answer = agent_module.ask_hybrid_agent(
        query="Unknown topic",
        collection=object(),
    )

    assert answer == (
        "I could not retrieve enough information from the "
        "VITESS documentation to answer this question reliably."
    )


def test_ask_hybrid_agent_uses_tool_context_for_fallback(monkeypatch):
    fake_agent = FakeAgent(
        messages=[
            ToolMessage(
                content="The guide module transports neutrons.",
                tool_call_id="tool-call-1",
            )
        ]
    )

    fake_answer_model = FakeAnswerModel(
        response_content="The guide module transports neutrons."
    )

    monkeypatch.setattr(
        agent_module,
        "build_vitess_research_agent",
        lambda collection, model=None: fake_agent,
    )

    monkeypatch.setattr(
        agent_module,
        "ChatOpenAI",
        lambda **kwargs: fake_answer_model,
    )

    answer = agent_module.ask_hybrid_agent(
        query="What does the guide module do?",
        collection=object(),
    )

    assert answer == "The guide module transports neutrons."
    assert fake_answer_model.received_messages is not None

    fallback_prompt = fake_answer_model.received_messages[1].content

    assert "What does the guide module do?" in fallback_prompt
    assert "The guide module transports neutrons." in fallback_prompt


def test_ask_hybrid_agent_removes_duplicate_tool_context(monkeypatch):
    duplicated_context = "The filter module removes unwanted trajectories."

    fake_agent = FakeAgent(
        messages=[
            ToolMessage(
                content=duplicated_context,
                tool_call_id="tool-call-1",
            ),
            ToolMessage(
                content=duplicated_context,
                tool_call_id="tool-call-2",
            ),
        ]
    )

    fake_answer_model = FakeAnswerModel(
        response_content="The filter module removes unwanted trajectories."
    )

    monkeypatch.setattr(
        agent_module,
        "build_vitess_research_agent",
        lambda collection, model=None: fake_agent,
    )

    monkeypatch.setattr(
        agent_module,
        "ChatOpenAI",
        lambda **kwargs: fake_answer_model,
    )

    agent_module.ask_hybrid_agent(
        query="What does filter do?",
        collection=object(),
    )

    fallback_prompt = fake_answer_model.received_messages[1].content

    assert fallback_prompt.count(duplicated_context) == 1


def test_ask_hybrid_agent_handles_empty_fallback_response(monkeypatch):
    fake_agent = FakeAgent(
        messages=[
            ToolMessage(
                content="Relevant documentation.",
                tool_call_id="tool-call-1",
            )
        ]
    )

    fake_answer_model = FakeAnswerModel(response_content="")

    monkeypatch.setattr(
        agent_module,
        "build_vitess_research_agent",
        lambda collection, model=None: fake_agent,
    )

    monkeypatch.setattr(
        agent_module,
        "ChatOpenAI",
        lambda **kwargs: fake_answer_model,
    )

    answer = agent_module.ask_hybrid_agent(
        query="Question",
        collection=object(),
    )

    assert answer == (
        "The relevant VITESS documentation was retrieved, "
        "but no final textual answer could be generated."
    )