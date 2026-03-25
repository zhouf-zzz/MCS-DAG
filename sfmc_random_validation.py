"""Random-taskset validation for SFMC offline mapping."""

from __future__ import annotations

import argparse
import time
from typing import Dict, Iterable, List

from SFMC import MappingError, compute_SN, compute_SO, map_taskset


def _topo_order_from_preds(node_ids: Iterable[int], preds: Dict[int, set], succs: Dict[int, set]) -> List[int]:
    indeg = {nid: len(preds[nid]) for nid in node_ids}
    q = sorted([nid for nid, d in indeg.items() if d == 0])
    out: List[int] = []
    while q:
        u = q.pop(0)
        out.append(u)
        for v in succs[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
                q.sort()
    if len(out) != len(indeg):
        raise ValueError("internal DAG has cycle")
    return out


def _critical_path(task, mode: str) -> float:
    dag = task.internal_dag
    if dag is None or not dag.nodes:
        return 0.0

    node_ids = sorted(dag.nodes.keys())
    preds = {nid: set(dag.nodes[nid].predecessors) for nid in node_ids}
    succs = {nid: set(dag.nodes[nid].successors) for nid in node_ids}
    topo = _topo_order_from_preds(node_ids, preds, succs)

    dist = {}
    for nid in topo:
        w = float(dag.nodes[nid].eLO if mode == "NS" else dag.nodes[nid].eHI)
        if not preds[nid]:
            dist[nid] = w
        else:
            dist[nid] = max(dist[p] for p in preds[nid]) + w
    return max(dist.values()) if dist else 0.0


def prepare_task_for_sfmc(task, d_vir_ratio: float = 0.5) -> None:
    """Inject SFMC fields onto project task object."""
    if task.internal_dag is None:
        raise ValueError(f"task {task.id} has no internal_dag")

    nodes = list(task.internal_dag.nodes.values())
    task.C_N = sum(float(n.eLO) for n in nodes)
    hi_sum = sum(float(n.eHI) for n in nodes)
    task.C_O = hi_sum if task.cri == 0 else 0.0

    task.L_N = _critical_path(task, "NS")
    task.L_O = _critical_path(task, "CS") if task.cri == 0 else 0.0

    task.D = float(task.dLO)
    task.D_vir = float(task.dLO) * d_vir_ratio


def prepare_taskset_for_sfmc(ts, d_vir_ratio: float = 0.5) -> None:
    for task in ts.HI.union(ts.LO):
        prepare_task_for_sfmc(task, d_vir_ratio=d_vir_ratio)


def _task_satisfies_sfmc_constraints(task, m: float) -> bool:
    """Per-task SFMC constraints:
    L_N < D_vir, HI: L_O < D-D_vir, S_N<=m, HI: S_O<=m
    """
    if not (task.L_N < task.D_vir):
        return False
    if int(task.cri) == 0 and not (task.L_O < (task.D - task.D_vir)):
        return False
    try:
        s_n = compute_SN(task, strict=True)
    except Exception:
        return False
    if s_n > m:
        return False
    if int(task.cri) == 0:
        try:
            s_o = compute_SO(task, s_n, strict=True)
        except Exception:
            return False
        if s_o > m:
            return False
    return True


def _taskset_satisfies_sfmc_constraints(ts, m: float) -> bool:
    for task in ts.HI.union(ts.LO):
        if not _task_satisfies_sfmc_constraints(task, m):
            return False
    return True


def validate_random_tasksets(
    task_number: int = 6,
    node_number: int = 8,
    cycles: int = 20,
    uti_start: float = 0.2,
    uti_step: float = 0.1,
    uti_points: int = 6,
    d_vir_ratio: float = 0.5,
) -> Dict:
    result = {
        "utilization": [],
        "mapping_success_ratio": [],
        "avg_mapping_time_s": [],
        "generation_attempts": [],
    }

    for j in range(uti_points):
        system_uti = uti_start + uti_step * j
        result["utilization"].append(system_uti)

        map_ok = 0
        map_time = 0.0
        valid_trials = 0

        attempts = 0
        max_attempts = max(cycles * 100, 1000)
        while valid_trials < cycles and attempts < max_attempts:
            attempts += 1
            from task_set import Drs_gengerate

            try:
                ts = Drs_gengerate(
                    task_number,
                    system_uti * node_number,
                    2,
                    0.5,
                    node_number,
                    internal_subtask_enable=True,
                )
                prepare_taskset_for_sfmc(ts, d_vir_ratio=d_vir_ratio)
            except Exception:
                # Some random seeds may violate DRS constraints during generation.
                # Skip and keep sampling. This sample does NOT count as a round.
                continue

            t0 = time.time()
            try:
                mapped = map_taskset(ts, m=node_number, strict=True)
            except MappingError:
                mapped = None
            elapsed = time.time() - t0

            # Count round only if taskset satisfies SFMC per-task constraints.
            if mapped is None or (not _taskset_satisfies_sfmc_constraints(ts, node_number)):
                continue

            valid_trials += 1
            map_time += elapsed

            if mapped is not None and mapped.get("feasible", False):
                map_ok += 1

        denom = max(1, valid_trials)
        result["mapping_success_ratio"].append(map_ok / denom)
        result["avg_mapping_time_s"].append(map_time / denom)
        result["generation_attempts"].append(attempts)

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SFMC random-taskset validation")
    parser.add_argument("--task-number", type=int, default=6)
    parser.add_argument("--node-number", type=int, default=8)
    parser.add_argument("--cycles", type=int, default=20)
    parser.add_argument("--uti-start", type=float, default=0.2)
    parser.add_argument("--uti-step", type=float, default=0.1)
    parser.add_argument("--uti-points", type=int, default=6)
    parser.add_argument("--d-vir-ratio", type=float, default=0.5)
    args = parser.parse_args()

    summary = validate_random_tasksets(
        task_number=args.task_number,
        node_number=args.node_number,
        cycles=args.cycles,
        uti_start=args.uti_start,
        uti_step=args.uti_step,
        uti_points=args.uti_points,
        d_vir_ratio=args.d_vir_ratio,
    )

    for i, u in enumerate(summary["utilization"]):
        print(
            f"U={u:.2f} map_ratio={summary['mapping_success_ratio'][i]:.3f} "
            f"avg_map_time={summary['avg_mapping_time_s'][i]:.6f}s "
            f"attempts={summary['generation_attempts'][i]}"
        )
