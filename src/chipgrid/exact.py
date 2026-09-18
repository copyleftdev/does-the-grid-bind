"""Bridge to agent-calc: exact rational and interval arithmetic.

Every number that justifies a conclusion goes through here. Floating point is
allowed for exploration (finding the shape of a surface); it is not allowed to
produce a headline figure or decide a predicate.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from typing import Iterable

AGENT_CALC = "agent-calc"
CONTRACT = "calc1/0.1.0"


class CalcError(RuntimeError):
    pass


def _run(domain: str, request: dict) -> dict:
    payload = json.dumps(request, sort_keys=True)
    proc = subprocess.run(
        [AGENT_CALC, domain],
        input=payload,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise CalcError(f"{domain}: {proc.stderr.strip() or proc.stdout.strip()}")
    out = json.loads(proc.stdout)
    if out.get("contract_version") != CONTRACT:
        raise CalcError(f"contract drift: {out.get('contract_version')!r} != {CONTRACT!r}")
    failed = [c["name"] for c in out.get("checks", []) if not c.get("passed", False)]
    if failed:
        raise CalcError(f"{domain}: failed checks {failed}")
    return out


@lru_cache(maxsize=4096)
def _run_cached(domain: str, payload: str) -> str:
    return json.dumps(_run(domain, json.loads(payload)))


def call(domain: str, request: dict) -> dict:
    return json.loads(_run_cached(domain, json.dumps(request, sort_keys=True)))


# ---------------------------------------------------------------- expressions

def lit(x: Fraction | int | str) -> dict:
    """Encode a Python exact value as an agent-calc Expr node."""
    f = as_fraction(x)
    if f.denominator == 1:
        return {"kind": "integer", "value": str(f.numerator)}
    return {
        "kind": "rational",
        "numerator": str(f.numerator),
        "denominator": str(f.denominator),
    }


def as_fraction(x) -> Fraction:
    if isinstance(x, Fraction):
        return x
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, str):
        return Fraction(x)
    if isinstance(x, float):
        raise TypeError(
            f"refusing to coerce float {x!r} into an exact value; "
            "pass a str, int or Fraction so the literal is auditable"
        )
    raise TypeError(f"cannot make an exact value from {type(x).__name__}")


def _decode(node: dict) -> Fraction:
    return Fraction(int(node["numerator"]), int(node["denominator"]))


def evaluate(expr: dict) -> Fraction:
    """Evaluate an exact expression tree; returns a Fraction."""
    return _decode(call("eval", {"expr": expr})["exact"])


def binop(kind: str, a, b) -> dict:
    return {"kind": kind, "left": _coerce(a), "right": _coerce(b)}


def _coerce(x) -> dict:
    return x if isinstance(x, dict) else lit(x)


# ------------------------------------------------------------------ intervals

@dataclass(frozen=True)
class Interval:
    """A closed exact interval [lo, hi]. Bounds are Fractions, never floats."""

    lo: Fraction
    hi: Fraction

    def __post_init__(self) -> None:
        if self.lo > self.hi:
            raise ValueError(f"degenerate interval [{self.lo}, {self.hi}]")

    @staticmethod
    def of(lo, hi=None) -> "Interval":
        lo_f = as_fraction(lo)
        hi_f = lo_f if hi is None else as_fraction(hi)
        return Interval(lo_f, hi_f)

    @property
    def is_point(self) -> bool:
        return self.lo == self.hi

    def encode(self) -> dict:
        return {"lower": lit(self.lo), "upper": lit(self.hi)}

    def _bin(self, other: "Interval", intent: str) -> "Interval":
        out = call(
            "interval",
            {"intent": intent, "left": self.encode(), "right": other.encode()},
        )
        return Interval(_decode(out["lower"]), _decode(out["upper"]))

    def __add__(self, o: "Interval") -> "Interval":
        return self._bin(o, "add")

    def __sub__(self, o: "Interval") -> "Interval":
        return self._bin(o, "sub")

    def __mul__(self, o: "Interval") -> "Interval":
        return self._bin(o, "mul")

    def __truediv__(self, o: "Interval") -> "Interval":
        return self._bin(o, "div")

    def contains(self, x) -> bool:
        f = as_fraction(x)
        return self.lo <= f <= self.hi

    def strictly_above(self, x) -> bool:
        """True iff EVERY point in the interval exceeds x — a decidable verdict."""
        return self.lo > as_fraction(x)

    def strictly_below(self, x) -> bool:
        return self.hi < as_fraction(x)

    def straddles(self, x) -> bool:
        """The honest third answer: the data does not decide the question."""
        return self.contains(x) and not self.is_point

    @property
    def width(self) -> Fraction:
        return self.hi - self.lo

    def fmt(self, places: int = 4) -> str:
        if self.is_point:
            return _dec(self.lo, places)
        return f"[{_dec(self.lo, places)}, {_dec(self.hi, places)}]"

    def __repr__(self) -> str:
        return f"Interval({self.fmt()})"


def _dec(f: Fraction, places: int = 4) -> str:
    from decimal import Decimal, getcontext

    getcontext().prec = 50
    return str(round(Decimal(f.numerator) / Decimal(f.denominator), places))


def hull(parts: Iterable[Interval]) -> Interval:
    parts = list(parts)
    return Interval(min(p.lo for p in parts), max(p.hi for p in parts))
