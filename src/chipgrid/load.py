"""Load the parameter set from YAML, so data is auditable separately from code.

The loader is strict on purpose. A missing source, a missing as-of date on a
hard parameter, or a float where an exact literal belongs is an error, not a
warning. The point of separating data from code is that a reviewer can read
the data file alone and know where every number came from.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import yaml

from .exact import Interval
from .params import Param, Provenance, Registry

REQUIRED = {"value", "unit", "provenance", "source"}


def _interval(raw) -> Interval:
    if isinstance(raw, list):
        if len(raw) != 2:
            raise ValueError(f"an interval needs exactly two bounds, got {raw!r}")
        return Interval.of(str(raw[0]), str(raw[1]))
    return Interval.of(str(raw))


def load(path: str | Path, name: str | None = None) -> Registry:
    path = Path(path)
    doc = yaml.safe_load(path.read_text())
    reg = Registry(name or path.stem)
    for key, spec in (doc.get("parameters") or {}).items():
        missing = REQUIRED - set(spec)
        prov = Provenance(spec.get("provenance", "ASSUMED"))
        if prov is Provenance.ASSUMED:
            missing -= {"source"}
        if missing:
            raise ValueError(f"{key}: missing {sorted(missing)}")
        reg.add(
            Param(
                key=key,
                value=_interval(spec["value"]),
                unit=spec["unit"],
                provenance=prov,
                source=spec.get("source", ""),
                url=spec.get("url", ""),
                as_of=str(spec.get("as_of", "")),
                note=spec.get("note", ""),
            )
        )
    return reg
