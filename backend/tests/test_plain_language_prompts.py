"""Every Gemini prompt asks for plain, beginner-friendly wording without loosening the honesty rules."""

import json
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.schemas.diagnosis import HistoryPoint
from app.services import diagnosis as diagnosis_service
from app.services import document_analysis
from app.services.diagnosis import PLAIN_LANGUAGE, build_evidence


class _Recorder:
    def __init__(self, output: str) -> None:
        self.output = output
        self.prompts: list[str] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.prompts.append(str(kwargs.get("input")))
        return SimpleNamespace(output_text=self.output)


@pytest.fixture(autouse=True)
def _model(monkeypatch):
    monkeypatch.setattr(settings, "gemini_model", "gemini-3.8-flash")


def _evidence():
    return build_evidence(
        subject_id="abc",
        title="Fold a crane",
        views=1000,
        likes=50,
        comments=10,
        history=[HistoryPoint(observed_at="2026-02-01T00:00:00+00:00", views=1000)],
    )


def test_diagnosis_prompt_is_plain_and_keeps_the_evidence_rules():
    recorder = _Recorder("{}")
    evidence = _evidence()
    diagnosis_service._call_model(SimpleNamespace(interactions=recorder), evidence)
    prompt = recorder.prompts[0]
    assert PLAIN_LANGUAGE in prompt
    assert "Every evidence field must copy one observation string exactly." in prompt
    assert "Do not invent metrics" in prompt
    assert "untrusted data" in prompt
    assert "never use these words: guarantee" in prompt
    start = prompt.index("{")
    assert prompt[:start].endswith("Evidence: ")
    assert json.loads(prompt[start:])["evidence_level"] == evidence.evidence_level


def test_document_prompts_are_plain_and_keep_exact_numbers():
    narrative = _Recorder("{}")
    with pytest.raises(document_analysis.DocumentProcessError):
        document_analysis._request_narrative(SimpleNamespace(interactions=narrative), "csv", "a,b\n1,2\n", {"rows": 1})
    assert PLAIN_LANGUAGE in narrative.prompts[0]
    assert "every number you mention must already appear in the statistics" in narrative.prompts[0]

    answer = _Recorder("{}")
    with pytest.raises(document_analysis.DocumentProcessError):
        document_analysis._ask_model(SimpleNamespace(interactions=answer), "Revenue was 40 dollars.", "What was revenue?")
    assert PLAIN_LANGUAGE in answer.prompts[0]
    assert "Do not invent figures." in answer.prompts[0]
