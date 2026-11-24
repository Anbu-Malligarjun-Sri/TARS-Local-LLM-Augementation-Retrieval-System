"""Run the R0 synthetic visitor scripts through the local chat engine."""
import json
import re
import sys
import time
from pathlib import Path

from src.ai.llm_handler import LMStudioHandler
from src.core.memory_store import MemoryStore
from src.core.tars_engine import TARSEngine
from src.personality.response_generator import ResponseGenerator
from src.utils.config import TARSConfig


def review_reply(reply: str, locale: str) -> tuple[bool, list[str]]:
    tamil = len(re.findall(r"[\u0b80-\u0bff]+", reply))
    english = len(re.findall(r"[a-z]+", reply, re.I))
    matches = tamil > english if locale == "ta-IN" else english > tamil
    # These held-out scripts ask for ordinary English and Tamil prose. Surface
    # malformed tokens for review without censoring the user's chat or quotations.
    foreign = r"[\u0600-\u06ff\u0980-\u09ff]"
    tamil_char = r"[\u0b80-\u0bff]"
    flags = []
    if re.search(f"{foreign}{tamil_char}|{tamil_char}{foreign}", reply):
        flags.append("mixed_script_word")
    return matches, flags


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    fixtures = Path(__file__).resolve().parents[1] / "tests/fixtures/companion_visitors.json"
    config = TARSConfig(
        _env_file=None, allow_cloud=False, rag_enabled=False,
        lm_studio_base_url="http://127.0.0.1:1234/v1", lm_studio_model="qwen/qwen3.5-9b",
        lm_studio_reasoning_effort="none", max_tokens=256, request_timeout=180,
    )
    engine = TARSEngine(config=config, llm_handler=LMStudioHandler(config), use_rag=False,
                        memory_store=MemoryStore(), response_generator=ResponseGenerator(config))
    failed = False
    for case in json.loads(fixtures.read_text(encoding="utf-8")):
        start = time.monotonic()
        reply = "".join(engine.chat_stream(case["prompt"], conversation_id=case["session"]))
        matches, flags = review_reply(reply, case["locale"])
        failed |= not matches or bool(flags)
        print(json.dumps(dict(id=case["id"], expected=case["locale"], script_check=matches,
                              review_flags=flags, seconds=round(time.monotonic()-start, 1), reply=reply),
                         ensure_ascii=False), flush=True)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
