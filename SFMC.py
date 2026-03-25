"""SFMC mapping metrics for mixed-criticality sporadic DAG tasks.

This module implements the two core metric computations used by the
Semi-Federated Scheduling of Mixed-Criticality System for Sporadic DAG Tasks:

- compute_SN(task): normal-state mapping speed
- compute_SO(task, SN): critical-state mapping speed
- validate_task_params(task): parameter sanity check

The implementation is compatible with the existing task settings in this repo
and also accepts paper-style field names.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, List, Optional


class MappingError(ValueError):
    """Raised when a task cannot be mapped under SFMC constraints."""


EPS = 1e-12


@dataclass(frozen=True)
class _TaskView:
    """Normalized task parameters required by SFMC formulas."""

    C_N: float
    C_O: float
    L_N: float
    L_O: float
    D: float
    D_vir: float
    crit: str  # "HI" or "LO"



def _first_attr(task: Any, names: Iterable[str], default: Optional[float] = None) -> float:
    for name in names:
        if hasattr(task, name):
            return getattr(task, name)
    if default is not None:
        return default
    raise MappingError(f"missing required attribute, tried one of: {tuple(names)}")



def _normalize_crit(raw: Any) -> str:
    """Normalize criticality label to 'HI'/'LO'.

    Existing code in this repo uses: cri == 0 for HI, cri == 1 for LO.
    """
    if isinstance(raw, str):
        v = raw.strip().upper()
        if v in {"HI", "H", "0"}:
            return "HI"
        if v in {"LO", "L", "1"}:
            return "LO"
    elif isinstance(raw, (int, float)):
        if int(raw) == 0:
            return "HI"
        if int(raw) == 1:
            return "LO"
    raise MappingError(f"invalid task criticality value: {raw!r}")



def _to_view(task: Any, strict: bool = True) -> _TaskView:
    # Paper-style aliases first, then repository task aliases.
    C_N = float(_first_attr(task, ("C_N", "c_n", "eLO")))
    C_O = float(_first_attr(task, ("C_O", "c_o", "eHI")))
    # For repository MCTask (no DAG path field), fallback to sequential path:
    # L_N = C_N, L_O = C_O. In strict mode, require explicit values.
    if strict and (not hasattr(task, "L_N")) and (not hasattr(task, "l_n")):
        raise MappingError("missing L_N: please provide DAG critical-path length for NS")
    if strict and (not hasattr(task, "L_O")) and (not hasattr(task, "l_o")):
        raise MappingError("missing L_O: please provide DAG critical-path length for CS")
    L_N = float(_first_attr(task, ("L_N", "l_n"), C_N))
    L_O = float(_first_attr(task, ("L_O", "l_o"), C_O))
    D = float(_first_attr(task, ("D", "d", "dLO", "dHI", "pLO", "pHI")))
    # Existing task objects do not carry D_vir by default.
    # In strict mode, this must be explicitly provided to keep experiments
    # consistent with task/processor settings chosen in reproduction scripts.
    if strict and (not hasattr(task, "D_vir")) and (not hasattr(task, "d_vir")) and (not hasattr(task, "D_prime")):
        raise MappingError("missing D_vir: please provide the NS-to-CS split point")
    D_vir = float(_first_attr(task, ("D_vir", "d_vir", "D_prime"), D * 0.5))
    crit_raw = _first_attr(task, ("crit", "cri"))
    crit = _normalize_crit(crit_raw)

    return _TaskView(C_N=C_N, C_O=C_O, L_N=L_N, L_O=L_O, D=D, D_vir=D_vir, crit=crit)



def validate_task_params(task: Any, strict: bool = True) -> _TaskView:
    """Validate SFMC-required task parameters.

    Returns:
        _TaskView: normalized immutable parameter view.

    Raises:
        MappingError: if parameters violate SFMC preconditions.
    """
    t = _to_view(task, strict=strict)

    if t.D <= EPS:
        raise MappingError("invalid deadline D: must be > 0")
    if t.D_vir <= EPS or t.D_vir >= t.D - EPS:
        raise MappingError("invalid D_vir: must satisfy 0 < D_vir < D")

    for name, value in (("C_N", t.C_N), ("C_O", t.C_O), ("L_N", t.L_N), ("L_O", t.L_O)):
        if value < -EPS:
            raise MappingError(f"invalid {name}: must be >= 0")

    if t.L_N - t.C_N > EPS:
        raise MappingError("invalid parameters: L_N must be <= C_N")
    if t.L_O - t.C_O > EPS:
        raise MappingError("invalid parameters: L_O must be <= C_O")

    # Mapping window constraints from formulas.
    if t.D_vir - t.L_N <= EPS:
        raise MappingError("invalid normal-state window: D_vir <= L_N")

    if t.crit == "HI" and (t.D - t.D_vir - t.L_O <= EPS):
        raise MappingError("invalid critical-state window: D - D_vir <= L_O")

    return t


def _compute_SN_from_view(t: _TaskView) -> float:
    """Internal helper: compute S_N from a validated task view."""
    u_n = t.C_N / t.D_vir
    if u_n <= 1.0:
        return max(0.0, u_n)

    denom = t.D_vir - t.L_N
    if denom <= EPS:
        raise MappingError("invalid normal-state window: D_vir <= L_N")

    s_n = (t.C_N - t.L_N) / denom
    return max(0.0, s_n)


def _compute_SO_from_view(t: _TaskView, SN: float) -> float:
    """Internal helper: compute S_O from a validated task view."""
    if t.crit == "LO":
        return 0.0

    crit_window = t.D - t.D_vir
    if crit_window <= EPS:
        raise MappingError("invalid critical-state window: D <= D_vir")

    u_o = (t.C_O - SN * t.D_vir) / crit_window
    if u_o <= 1.0:
        return max(0.0, u_o)

    denom = t.D - t.D_vir - t.L_O
    if denom <= EPS:
        raise MappingError("invalid critical-state window: D - D_vir <= L_O")

    s_o = (t.C_O - SN * t.D_vir - t.L_O) / denom
    return max(0.0, s_o)



def compute_SN(task: Any, strict: bool = True) -> float:
    """Compute normal-state mapping speed S_N for a task."""
    t = validate_task_params(task, strict=strict)
    return _compute_SN_from_view(t)



def compute_SO(task: Any, SN: float, strict: bool = True) -> float:
    """Compute critical-state mapping speed S_O for a task.

    LO tasks get S_O = 0. HI tasks follow SFMC Eq. (critical state mapping).
    """
    t = validate_task_params(task, strict=strict)
    return _compute_SO_from_view(t, SN)


def compute_task_speeds(task: Any, strict: bool = True) -> Dict[str, float]:
    """Compute and return SFMC speeds for one task.

    Returns:
        dict with keys: SN, SO
    """
    t = validate_task_params(task, strict=strict)
    sn = _compute_SN_from_view(t)
    so = _compute_SO_from_view(t, sn)
    return {"SN": sn, "SO": so}


def compute_taskset_speeds(
    taskset: Any,
    attach: bool = True,
    strict: bool = True,
) -> Dict[int, Dict[str, float]]:
    """Compute SFMC speeds for all tasks in current repository MCTaskSet.

    The function iterates over ``taskset.HI ∪ taskset.LO`` and computes
    speed metrics per task. If ``attach=True``, computed values are written
    back onto each task object as ``sfmc_SN`` and ``sfmc_SO``.
    """
    if not hasattr(taskset, "HI") or not hasattr(taskset, "LO"):
        raise MappingError("taskset must provide HI and LO sets")

    result: Dict[int, Dict[str, float]] = {}
    for task in taskset.HI.union(taskset.LO):
        speeds = compute_task_speeds(task, strict=strict)
        result[int(getattr(task, "id", len(result)))] = speeds
        if attach:
            setattr(task, "sfmc_SN", speeds["SN"])
            setattr(task, "sfmc_SO", speeds["SO"])
    return result


def split_load_to_mccts(S: float, state_tag: str) -> List[Dict[str, Any]]:
    """Split mapped load ``S`` into a list of MCCT containers.

    Rule (paper Algorithm 1/2 equivalent):
    - let k = ceil(S)
    - create k-1 unit containers (delta=1.0)
    - create one fractional container so total load equals S

    The resulting list is sorted by ``delta`` in descending order.
    """
    if S < -EPS:
        raise MappingError("negative mapped load")
    if abs(S) <= EPS:
        return []

    k = int(math.ceil(S))
    frac = S - (k - 1)  # expected in (0, 1]
    mccts = [1.0] * (k - 1) + [frac]
    mccts.sort(reverse=True)

    return [{"delta": d, "state": state_tag} for d in mccts]


def build_task_mccts(task: Any, strict: bool = True) -> Dict[str, List[Dict[str, Any]]]:
    """Build NS/CS MCCT sets for a single task.

    Returns:
        {
            "NS": [{"delta": ..., "state": "NS"}, ...],
            "CS": [{"delta": ..., "state": "CS"}, ...],
            "SN": float,
            "SO": float,
        }
    """
    sn = compute_SN(task, strict=strict)
    so = compute_SO(task, sn, strict=strict)
    return {
        "NS": split_load_to_mccts(sn, "NS"),
        "CS": split_load_to_mccts(so, "CS"),
        "SN": sn,
        "SO": so,
    }


def build_taskset_mccts(
    taskset: Any,
    attach: bool = True,
    strict: bool = True,
) -> Dict[int, Dict[str, Any]]:
    """Build NS/CS MCCT sets for all tasks in ``taskset.HI ∪ taskset.LO``."""
    if not hasattr(taskset, "HI") or not hasattr(taskset, "LO"):
        raise MappingError("taskset must provide HI and LO sets")

    result: Dict[int, Dict[str, Any]] = {}
    for task in taskset.HI.union(taskset.LO):
        tid = int(getattr(task, "id", len(result)))
        mccts = build_task_mccts(task, strict=strict)
        result[tid] = mccts
        if attach:
            setattr(task, "sfmc_SN", mccts["SN"])
            setattr(task, "sfmc_SO", mccts["SO"])
            setattr(task, "sfmc_mcct_ns", mccts["NS"])
            setattr(task, "sfmc_mcct_cs", mccts["CS"])
    return result


def map_task(task: Any, m: float, strict: bool = True) -> Dict[str, Any]:
    """Map one task into NS/CS MCCT sets with per-task capacity checks.

    Order:
    1) validate structural constraints
    2) compute S_N
    3) compute S_O (LO task -> 0)
    4) check per-task capacity bounds (paper Eq.14-style)
    5) split S_N/S_O into MCCT sets
    """
    if m <= 0:
        raise MappingError("processor count m must be > 0")

    t = validate_task_params(task, strict=strict)

    # Step 1/2
    s_n = _compute_SN_from_view(t)
    s_o = _compute_SO_from_view(t, s_n)

    # Step 3: per-task capacity bounds (Eq.14 style).
    if s_n - m > EPS:
        raise MappingError("S_N exceeds processor count")
    if t.crit == "HI" and (s_o - m > EPS):
        raise MappingError("S_O exceeds processor count")

    # Step 4: split into MCCT sets.
    normal_mccts = split_load_to_mccts(s_n, "NS")
    critical_mccts = split_load_to_mccts(s_o, "CS")

    return {
        "task_id": int(getattr(task, "id", -1)),
        "crit": t.crit,
        "S_N": s_n,
        "S_O": s_o,
        "normal_mccts": normal_mccts,
        "critical_mccts": critical_mccts,
    }


def _iter_tasks(taskset_or_tasks: Any) -> Iterator[Any]:
    if hasattr(taskset_or_tasks, "HI") and hasattr(taskset_or_tasks, "LO"):
        for t in taskset_or_tasks.HI.union(taskset_or_tasks.LO):
            yield t
        return
    try:
        for t in taskset_or_tasks:
            yield t
    except TypeError as exc:
        raise MappingError("map_taskset expects a taskset (HI/LO) or an iterable of tasks") from exc


def map_taskset(taskset_or_tasks: Any, m: float, attach: bool = True, strict: bool = True) -> Dict[str, Any]:
    """Map a task set and perform separated NS/CS capacity checks.

    Important:
    - NS and CS do NOT execute simultaneously.
    - feasibility is checked separately:
      * sum_i S_N_i <= m
      * sum_{i in HI} S_O_i <= m
    """
    mapped_tasks: List[Dict[str, Any]] = []
    total_sn = 0.0
    total_so = 0.0

    for task in _iter_tasks(taskset_or_tasks):
        mapped = map_task(task, m=m, strict=strict)
        mapped_tasks.append(mapped)
        total_sn += mapped["S_N"]

        if mapped["crit"] == "HI":
            total_so += mapped["S_O"]

        if attach:
            setattr(task, "sfmc_SN", mapped["S_N"])
            setattr(task, "sfmc_SO", mapped["S_O"])
            setattr(task, "sfmc_mcct_ns", mapped["normal_mccts"])
            setattr(task, "sfmc_mcct_cs", mapped["critical_mccts"])

    feasible_ns = total_sn <= m + EPS
    feasible_cs = total_so <= m + EPS
    feasible = feasible_ns and feasible_cs

    return {
        "tasks": mapped_tasks,
        "total_SN": total_sn,
        "total_SO": total_so,
        "feasible_ns": feasible_ns,
        "feasible_cs": feasible_cs,
        "feasible": feasible,
    }


__all__ = [
    "MappingError",
    "compute_SN",
    "compute_SO",
    "compute_task_speeds",
    "compute_taskset_speeds",
    "split_load_to_mccts",
    "build_task_mccts",
    "build_taskset_mccts",
    "map_task",
    "map_taskset",
    "validate_task_params",
]
