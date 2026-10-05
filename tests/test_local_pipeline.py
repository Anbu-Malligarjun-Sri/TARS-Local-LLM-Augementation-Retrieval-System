from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from src.ai import embeddings as embeddings_module
from src.core.memory_store import MemoryStore
from src.core.tars_engine import TARSEngine
from src.interfaces import api as api_module
from src.utils.config import TARSConfig


class FakeRAG:
    def __init__(self):
        self.queries = []

    def retrieve(self, query, n_results):
        self.queries.append((query, n_results))
        return "Reference: local retrieval evidence"


class FakePersonality:
    class CueLight:
        @staticmethod
        def maybe_add(probability):
            return ""

    cue_light = CueLight()

    @staticmethod
    def enhance_response(response):
        return f"enhanced:{response}"

    @staticmethod
    def format_unknown_input():
        return "empty"

    @staticmethod
    def format_greeting():
        return "TARS online"


class FakeLLM:
    def __init__(self):
        self.prompts = []

    def generate(self, message, conversation_history=None):
        self.prompts.append((message, conversation_history))
        return "answer"

    def generate_stream(self, message, conversation_history=None):
        self.prompts.append((message, conversation_history))
        yield "streamed "
        yield "answer"

    def set_system_prompt(self, prompt):
        self.system_prompt = prompt


def make_engine():
    config = TARSConfig(rag_enabled=False, voice_enabled=False, _env_file=None)
    llm = FakeLLM()
    engine = TARSEngine(
        config=config,
        llm_handler=llm,
        memory_store=MemoryStore(),
        response_generator=FakePersonality(),
        use_rag=False,
    )
    rag = FakeRAG()
    engine.rag_system = rag
    engine.use_rag = True
    return engine, llm, rag


def test_regular_and_streaming_chat_use_rag_and_isolated_memory():
    engine, llm, rag = make_engine()

    assert engine.chat("Explain this", conversation_id="session-a") == "enhanced:answer"
    streamed = "".join(engine.chat_stream("Explain that", conversation_id="session-b"))

    assert streamed == "streamed answer"
    assert len(rag.queries) == 2
    assert all("local retrieval evidence" in prompt for prompt, _ in llm.prompts)
    assert engine.get_conversation_history("session-a") == [
        {"role": "user", "content": "Explain this"},
        {"role": "assistant", "content": "enhanced:answer"},
    ]
    assert engine.get_conversation_history("session-b") == [
        {"role": "user", "content": "Explain that"},
        {"role": "assistant", "content": "streamed answer"},
    ]


def test_embedding_generator_batches_and_checks_dimension(monkeypatch):
    config = TARSConfig(
        lm_studio_base_url="http://localhost:1234/v1",
        embedding_model="text-embedding-nomic-embed-text-v1.5",
        embedding_dimension=3,
        _env_file=None,
    )
    calls = []

    class FakeOpenAI:
        def __init__(self, **kwargs):
            assert kwargs["base_url"] == config.lm_studio_base_url

        @property
        def embeddings(self):
            return self

        def create(self, model, input):
            calls.append((model, input))
            data = [
                SimpleNamespace(index=index, embedding=[float(index), 1.0, 2.0])
                for index, _ in enumerate(input)
            ]
            return SimpleNamespace(data=data)

    monkeypatch.setattr(embeddings_module, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(embeddings_module, "get_config", lambda: config)
    generator = embeddings_module.EmbeddingGenerator()

    vectors = generator.embed_batch(["one", "two", "three"], batch_size=2)

    assert len(vectors) == 3
    assert [len(vector) for vector in vectors] == [3, 3, 3]
    assert [len(inputs) for _, inputs in calls] == [2, 1]
    assert all(model == config.embedding_model for model, _ in calls)
    assert calls[0][1] == ["search_document: one", "search_document: two"]
    assert generator.embed_query("question") == [0.0, 1.0, 2.0]
    assert calls[-1][1] == ["search_query: question"]


def test_rest_and_websocket_preserve_conversation_ids():
    engine, _, _ = make_engine()
    previous_engine = api_module._engine
    api_module._engine = engine
    client = TestClient(api_module.app)
    rest_id = str(uuid4())
    websocket_id = str(uuid4())

    try:
        rest_response = client.post(
            "/api/chat",
            json={"message": "REST question", "conversation_id": rest_id},
        )
        assert rest_response.status_code == 200
        assert rest_response.json()["conversation_id"] == rest_id
        assert engine.get_conversation_history(rest_id)[0]["content"] == "REST question"

        with client.websocket_connect("/api/ws/chat") as websocket:
            greeting = websocket.receive_json()
            assert greeting["type"] == "greeting"
            websocket.send_json({
                "message": "WebSocket question",
                "stream": True,
                "conversation_id": websocket_id,
            })
            assert websocket.receive_json()["type"] == "start"
            assert websocket.receive_json()["type"] == "chunk"
            assert websocket.receive_json()["type"] == "chunk"
            end_message = websocket.receive_json()
            assert end_message["type"] == "end"
            assert end_message["full_response"] == "streamed answer"

        assert engine.get_conversation_history(websocket_id)[0]["content"] == "WebSocket question"
        assert engine.get_conversation_history(rest_id)[0]["content"] == "REST question"
    finally:
        api_module._engine = previous_engine