from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class Profile:
    model: str
    effort: str

    @property
    def label(self) -> str:
        return f"{self.model} {self.effort}"


LINX_BASELINE = Profile("gpt-5.6", "high")
THINX_BASELINE = Profile("gpt-5.6", "xhigh")
THINX_ESCALATED = Profile("gpt-5.6", "ultra")


class ModelState:
    """Deterministic role routing; an escalated Thinx pass always resets."""

    def __init__(self) -> None:
        self._thinx = THINX_BASELINE
        self.escalated = False

    def linx_profile(self) -> Profile:
        return LINX_BASELINE

    def thinx_profile(self) -> Profile:
        return self._thinx

    def begin_thinx_pass(self, *, high_risk: bool, proof_failed: bool) -> Profile:
        self.escalated = high_risk or proof_failed
        self._thinx = THINX_ESCALATED if self.escalated else THINX_BASELINE
        return self._thinx

    def complete_thinx_pass(self) -> Profile:
        self._thinx = THINX_BASELINE
        self.escalated = False
        return self._thinx

    @contextmanager
    def thinx_pass(self, *, high_risk: bool, proof_failed: bool) -> Iterator[Profile]:
        try:
            yield self.begin_thinx_pass(
                high_risk=high_risk,
                proof_failed=proof_failed,
            )
        finally:
            self.complete_thinx_pass()
