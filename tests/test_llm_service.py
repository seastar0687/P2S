from p2s_core.models import EvidenceSpan
from p2s_core.services import LLMService, LLMServiceError


DEBUG_TEST_DIR = __import__("pathlib").Path(__file__).resolve().parents[1] / ".test_runs" / "llm_debug"


class FakeResponse:
    def __init__(self, payload, status_error=None):
        self.payload = payload
        self.status_error = status_error

    def raise_for_status(self):
        if self.status_error is not None:
            raise self.status_error

    def json(self):
        return self.payload


class FakeAsyncClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []
        self.closed = False

    async def post(self, url, headers=None, json=None):
        self.requests.append({"url": url, "headers": headers, "json": json})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    async def aclose(self):
        self.closed = True


def make_config():
    return {
        "llm": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_base": "https://api.openai.com/v1",
            "api_key": "sk-test",
            "temperature": 0.3,
            "max_retries": 2,
        }
    }


def test_llm_service_rejects_non_openai_provider():
    config = make_config()
    config["llm"]["provider"] = "ollama"

    try:
        LLMService(config)
    except ValueError as exc:
        assert "provider='openai'" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_complete_returns_text():
    client = FakeAsyncClient(
        [
            FakeResponse(
                {
                    "choices": [
                        {"message": {"content": "hello from fake llm"}},
                    ]
                }
            )
        ]
    )
    service = LLMService(make_config(), client=client)

    import asyncio

    result = asyncio.run(service.complete([{"role": "user", "content": "你好"}]))

    assert result == "hello from fake llm"
    assert client.requests[0]["url"] == "https://api.openai.com/v1/chat/completions"
    assert client.requests[0]["headers"]["Authorization"] == "Bearer sk-test"
    assert client.requests[0]["json"]["model"] == "gpt-4o-mini"


def test_complete_parses_response_type():
    span_json = EvidenceSpan(section="Intro", text="A claim appears here.").model_dump_json()
    client = FakeAsyncClient(
        [
            FakeResponse(
                {
                    "choices": [
                        {"message": {"content": span_json}},
                    ]
                }
            )
        ]
    )
    service = LLMService(make_config(), client=client)

    import asyncio

    result = asyncio.run(
        service.complete(
            [{"role": "user", "content": "Return an evidence span."}],
            response_type=EvidenceSpan,
        )
    )

    assert result == EvidenceSpan(section="Intro", text="A claim appears here.")
    assert client.requests[0]["json"]["response_format"] == {"type": "json_object"}


def test_complete_parses_json_fenced_response_type():
    span_json = EvidenceSpan(section="Intro", text="A claim appears here.").model_dump_json()
    client = FakeAsyncClient(
        [
            FakeResponse(
                {
                    "choices": [
                        {"message": {"content": f"```json\n{span_json}\n```"}},
                    ]
                }
            )
        ]
    )
    service = LLMService(make_config(), client=client)

    import asyncio

    result = asyncio.run(
        service.complete(
            [{"role": "user", "content": "Return an evidence span."}],
            response_type=EvidenceSpan,
        )
    )

    assert result == EvidenceSpan(section="Intro", text="A claim appears here.")


def test_complete_retries_malformed_structured_output():
    span_json = EvidenceSpan(section="Intro", text="A claim appears here.").model_dump_json()
    client = FakeAsyncClient(
        [
            FakeResponse({"choices": [{"message": {"content": "not json"}}]}),
            FakeResponse({"choices": [{"message": {"content": span_json}}]}),
        ]
    )
    service = LLMService(make_config(), client=client)

    import asyncio

    result = asyncio.run(
        service.complete(
            [{"role": "user", "content": "Return an evidence span."}],
            response_type=EvidenceSpan,
            retry_delay_sec=0,
        )
    )

    assert result == EvidenceSpan(section="Intro", text="A claim appears here.")
    assert len(client.requests) == 2


def test_complete_writes_debug_raw_file_after_structured_retry_exhausted():
    import shutil

    if DEBUG_TEST_DIR.exists():
        shutil.rmtree(DEBUG_TEST_DIR)
    DEBUG_TEST_DIR.mkdir(parents=True)
    client = FakeAsyncClient(
        [
            FakeResponse({"choices": [{"message": {"content": "not json 1"}}]}),
            FakeResponse({"choices": [{"message": {"content": "not json 2"}}]}),
        ]
    )
    service = LLMService(make_config(), client=client)

    import asyncio

    try:
        asyncio.run(
            service.complete(
                [{"role": "user", "content": "Return an evidence span."}],
                response_type=EvidenceSpan,
                retry_delay_sec=0,
                debug_dir=DEBUG_TEST_DIR,
            )
        )
    except LLMServiceError as exc:
        assert "structured output parse failed" in str(exc)
    else:
        raise AssertionError("Expected LLMServiceError")

    debug_files = list(DEBUG_TEST_DIR.glob("llm_raw_*.txt"))
    assert len(debug_files) == 1
    assert debug_files[0].read_text(encoding="utf-8") == "not json 2"


def test_health_check_returns_true_for_text_response():
    client = FakeAsyncClient(
        [
            FakeResponse(
                {
                    "choices": [
                        {"message": {"content": "ok"}},
                    ]
                }
            )
        ]
    )
    service = LLMService(make_config(), client=client)

    import asyncio

    assert asyncio.run(service.health_check()) is True


def test_health_check_returns_false_on_error():
    client = FakeAsyncClient([RuntimeError("network down")])
    service = LLMService(make_config(), client=client)

    import asyncio

    assert asyncio.run(service.health_check()) is False


def test_complete_raises_service_error_after_retries():
    client = FakeAsyncClient([RuntimeError("first"), RuntimeError("second")])
    service = LLMService(make_config(), client=client)

    import asyncio

    try:
        asyncio.run(service.complete([{"role": "user", "content": "你好"}]))
    except LLMServiceError as exc:
        assert "LLM request failed" in str(exc)
    else:
        raise AssertionError("Expected LLMServiceError")

    assert len(client.requests) == 2
