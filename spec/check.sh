#!/usr/bin/env bash
# TLC gate. Every run declares the outcome it expects BEFORE it runs, and the
# gate fails if a run produces any other outcome -- including an unexpected
# pass. A model checker that cannot fail is a model checker that is not
# checking, so the canaries are as load-bearing as the results.
set -uo pipefail

TLA_JAR="${TLA_JAR:-$HOME/.local/lib/tla2tools.jar}"
SPEC_DIR="$(cd "$(dirname "$0")" && pwd)"
PASS=0
FAIL=0

run() {
    local cfg="$1" expect="$2" note="$3"
    # Hermetic: a fresh metadir per run, or a stale states/ directory decides
    # the verdict instead of the spec.
    local meta; meta="$(mktemp -d)"
    local log; log="$(mktemp)"
    java -XX:+UseSerialGC -Xmx2g -cp "$TLA_JAR" tlc2.TLC \
        -cleanup -metadir "$meta" -workers 2 -deadlock \
        -config "$SPEC_DIR/$cfg" "$SPEC_DIR/Energization.tla" >"$log" 2>&1

    local actual
    if grep -q "Invariant .* is violated" "$log"; then
        actual="VIOLATED"
    elif grep -q "Model checking completed. No error has been found" "$log"; then
        actual="HOLDS"
    else
        actual="ERROR"
    fi

    local states; states="$(grep -oE '[0-9]+ states generated' "$log" | tail -1)"
    local viol;   viol="$(grep -oE 'Invariant [A-Za-z0-9_]+ is violated' "$log" | tail -1)"

    if [ "$actual" = "$expect" ]; then
        printf '  PASS  %-18s expected %-8s  %s  %s\n' "$cfg" "$expect" "${states:-—}" "$note"
        PASS=$((PASS+1))
    else
        printf '  FAIL  %-18s expected %-8s got %-8s  %s\n' "$cfg" "$expect" "$actual" "$note"
        printf '        %s\n' "${viol:-no violation line}"
        tail -25 "$log" | sed 's/^/        | /'
        FAIL=$((FAIL+1))
    fi
    rm -rf "$meta" "$log"
}

echo "=== Energization.tla — TLC gate ==="
echo
echo "canaries (each MUST be violated; a pass here invalidates every result below)"
run Canary.cfg        VIOLATED "clock must advance past t<MaxTime"
run CanaryShip.cfg    VIOLATED "Ship must be enabled"
run CanaryStrand.cfg  VIOLATED "a binding grid must strand hardware"
echo
echo "regime A — grid keeps up (S <= E-B): absorption is free"
run AbundantAbsorb.cfg   VIOLATED "warehouse CAN be cleared"
run Abundant.cfg         VIOLATED "and cleared with zero impairment — witness exists"
echo
echo "regime B — envelope-bound (E-B < S <= E): absorption costs book value"
run TightAbsorb.cfg      VIOLATED "warehouse CAN still be cleared"
run Tight.cfg            HOLDS    "but NO strategy clears it without a write-down"
echo
echo "regime C — supply-bound (S > E): stranding is forced outright"
run ConstrainedAbsorb.cfg HOLDS   "warehouse CANNOT be cleared by any strategy"
run Constrained.cfg      HOLDS    "so clean absorption is unreachable a fortiori"
echo
echo "passed=$PASS failed=$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
echo "GATE PASSED"
