"""Parameters, each one carrying its provenance.

A model whose inputs cannot be traced is an opinion with arithmetic attached.
Every parameter here is an exact Interval plus a citation and a provenance
class, and the class is load-bearing: conclusions that rest on VENDOR or
ADVOCACY inputs are reported separately from conclusions that rest on MEASURED
ones, because they fail differently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction

from .exact import Interval


class Provenance(str, Enum):
    MEASURED = "MEASURED"      # an observed statistic from a statistical agency
    FILED = "FILED"            # a number in an SEC filing or regulatory docket
    OFFICIAL = "OFFICIAL"      # an ISO/RTO or operator publication
    ESTIMATED = "ESTIMATED"    # third-party analyst estimate, method disclosed
    VENDOR = "VENDOR"          # the seller's own claim about its own product
    ADVOCACY = "ADVOCACY"      # published by a party with a stake in the number
    DERIVED = "DERIVED"        # computed here from other parameters
    ASSUMED = "ASSUMED"        # no source; a stated assumption under test

    @property
    def is_hard(self) -> bool:
        return self in (Provenance.MEASURED, Provenance.FILED, Provenance.OFFICIAL)


@dataclass(frozen=True)
class Param:
    key: str
    value: Interval
    unit: str
    provenance: Provenance
    source: str
    url: str = ""
    as_of: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if self.provenance is not Provenance.ASSUMED and not self.source:
            raise ValueError(f"{self.key}: a non-ASSUMED parameter needs a source")
        if self.provenance in (Provenance.MEASURED, Provenance.FILED, Provenance.OFFICIAL):
            if not self.as_of:
                raise ValueError(f"{self.key}: a hard parameter needs an as-of date")

    @property
    def lo(self) -> Fraction:
        return self.value.lo

    @property
    def hi(self) -> Fraction:
        return self.value.hi

    @property
    def is_point(self) -> bool:
        return self.value.is_point

    def row(self) -> str:
        return (
            f"{self.key:<34} {self.value.fmt(3):>22} {self.unit:<16} "
            f"{self.provenance.value:<10} {self.as_of:<10} {self.source}"
        )


class Registry:
    """A parameter set that refuses silent redefinition and tracks what was used."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._params: dict[str, Param] = {}
        self._touched: set[str] = set()

    def add(self, p: Param) -> Param:
        if p.key in self._params:
            raise KeyError(f"{p.key} already defined; edit it, do not shadow it")
        self._params[p.key] = p
        return p

    def __getitem__(self, key: str) -> Interval:
        self._touched.add(key)
        return self._params[key].value

    def param(self, key: str) -> Param:
        self._touched.add(key)
        return self._params[key]

    def __contains__(self, key: str) -> bool:
        return key in self._params

    def keys(self):
        return self._params.keys()

    def values(self):
        return self._params.values()

    @property
    def unused(self) -> set[str]:
        """Parameters defined but never read. Usually a wiring bug or dead data."""
        return set(self._params) - self._touched

    def by_provenance(self) -> dict[Provenance, list[Param]]:
        out: dict[Provenance, list[Param]] = {}
        for p in self._params.values():
            out.setdefault(p.provenance, []).append(p)
        return out

    def soft_dependencies(self, keys: list[str]) -> list[Param]:
        """Which of these inputs are not hard evidence — the caveat list."""
        return [self._params[k] for k in keys if not self._params[k].provenance.is_hard]

    def table(self) -> str:
        hdr = (
            f"{'key':<34} {'value':>22} {'unit':<16} "
            f"{'provenance':<10} {'as-of':<10} source"
        )
        lines = [hdr, "-" * len(hdr)]
        for p in sorted(self._params.values(), key=lambda q: q.key):
            lines.append(p.row())
        return "\n".join(lines)
