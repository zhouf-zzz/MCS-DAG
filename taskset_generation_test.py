import argparse
import random
from collections import defaultdict

from task_set import Drs_gengerate


def _longest_path_nodes(dag_tasks):
    dag_ids = {task.id for task in dag_tasks}
    succ = {task.id: [sid for sid in task.successors if sid in dag_ids] for task in dag_tasks}
    indegree = {task.id: 0 for task in dag_tasks}
    for task in dag_tasks:
        for sid in succ[task.id]:
            indegree[sid] += 1

    queue = [tid for tid, deg in indegree.items() if deg == 0]
    topo = []
    while queue:
        current = queue.pop(0)
        topo.append(current)
        for sid in succ[current]:
            indegree[sid] -= 1
            if indegree[sid] == 0:
                queue.append(sid)

    if len(topo) != len(dag_tasks):
        return 0

    longest = {tid: 1 for tid in topo}
    for tid in topo:
        for sid in succ[tid]:
            candidate = longest[tid] + 1
            if candidate > longest[sid]:
                longest[sid] = candidate
    return max(longest.values()) if longest else 0


def analyze_taskset(ts):
    tasks = sorted(ts.LO, key=lambda t: t.id)
    hi_tasks = [t for t in tasks if t.cri == 0]
    lo_only_tasks = [t for t in tasks if t.cri == 1]

    issues = []

    # Basic consistency checks
    hi_ids = {t.id for t in ts.HI}
    lo_ids = {t.id for t in ts.LO}
    if not hi_ids.issubset(lo_ids):
        issues.append("HI 集不是 LO 集子集")

    for t in tasks:
        if t.id == -1:
            issues.append("存在非法 task.id=-1")
        if t.dag_id == -1:
            issues.append(f"任务 {t.id} 没有分配 dag_id")
        if t.cri == 0 and t.id not in hi_ids:
            issues.append(f"HI 关键度任务 {t.id} 未进入 ts.HI")
        if t.cri == 1 and t.id in hi_ids:
            issues.append(f"LO 关键度任务 {t.id} 错误进入 ts.HI")

    task_by_id = {t.id: t for t in tasks}
    dag_to_tasks = defaultdict(list)
    for t in tasks:
        dag_to_tasks[t.dag_id].append(t)

    # Edge consistency + HI predecessor rule
    for t in tasks:
        for p in t.predecessors:
            if p not in task_by_id:
                issues.append(f"任务 {t.id} 的前驱 {p} 不存在")
                continue
            if t.id not in task_by_id[p].successors:
                issues.append(f"任务 {t.id} 与前驱 {p} 的边不对称")
            if task_by_id[p].dag_id != t.dag_id:
                issues.append(f"跨 DAG 前驱边: {p}->{t.id}")
            if t.cri == 0 and task_by_id[p].cri != 0:
                issues.append(f"HI 任务 {t.id} 存在 LO 前驱 {p}")

        for s in t.successors:
            if s not in task_by_id:
                issues.append(f"任务 {t.id} 的后继 {s} 不存在")
                continue
            if t.id not in task_by_id[s].predecessors:
                issues.append(f"任务 {t.id} 与后继 {s} 的边不对称")
            if task_by_id[s].dag_id != t.dag_id:
                issues.append(f"跨 DAG 后继边: {t.id}->{s}")

    # DAG summary
    dag_summary = []
    for dag_id, dag_tasks in sorted(dag_to_tasks.items(), key=lambda x: x[0]):
        node_count = len(dag_tasks)
        edge_count = sum(len(t.successors) for t in dag_tasks)
        roots = [t.id for t in dag_tasks if not t.predecessors]
        sinks = [t.id for t in dag_tasks if not t.successors]
        hi_count = sum(1 for t in dag_tasks if t.cri == 0)
        lo_count = node_count - hi_count
        longest_path_nodes = _longest_path_nodes(dag_tasks)
        dag_summary.append(
            {
                "dag_id": dag_id,
                "nodes": node_count,
                "edges": edge_count,
                "roots": roots,
                "sinks": sinks,
                "hi_count": hi_count,
                "lo_count": lo_count,
                "longest_path_nodes": longest_path_nodes,
            }
        )

        if len(roots) != 1:
            issues.append(f"DAG {dag_id} 根节点数量不是 1，而是 {len(roots)}")
        if len(sinks) != 1:
            issues.append(f"DAG {dag_id} 汇点数量不是 1，而是 {len(sinks)}")
        if longest_path_nodes < 3:
            issues.append(f"DAG {dag_id} 最长路径任务数小于 3（当前 {longest_path_nodes}）")

    data = {
        "task_count": len(tasks),
        "hi_count": len(hi_tasks),
        "lo_only_count": len(lo_only_tasks),
        "sum_uLO": sum(t.uLO for t in tasks),
        "sum_uHI": sum(t.uHI for t in hi_tasks),
        "dag_count": len(dag_to_tasks),
        "dag_summary": dag_summary,
        "issues": issues,
    }
    return data


def main():
    parser = argparse.ArgumentParser(description="检查 Drs_gengerate 生成任务集的结构一致性")
    parser.add_argument("--task-number", type=int, default=20)
    parser.add_argument("--node-number", type=int, default=4)
    parser.add_argument("--system-utilization", type=float, default=2.0)
    parser.add_argument("--cf", type=float, default=2)
    parser.add_argument("--cp", type=float, default=0.5)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    for run_idx in range(args.runs):
        ts = Drs_gengerate(
            args.task_number,
            args.system_utilization,
            args.cf,
            args.cp,
            args.node_number,
        )
        report = analyze_taskset(ts)

        print(f"=== Run {run_idx + 1}/{args.runs} ===")
        print(
            f"tasks={report['task_count']} hi={report['hi_count']} lo_only={report['lo_only_count']} "
            f"sum_uLO={report['sum_uLO']:.6f} sum_uHI={report['sum_uHI']:.6f} dags={report['dag_count']}"
        )

        for dag in report["dag_summary"]:
            print(
                f"  DAG {dag['dag_id']}: nodes={dag['nodes']} edges={dag['edges']} "
                f"HI={dag['hi_count']} LO={dag['lo_count']} roots={dag['roots']} sinks={dag['sinks']} "
                f"longest_path_nodes={dag['longest_path_nodes']}"
            )

        if report["issues"]:
            print("  [FAIL] 发现问题:")
            for issue in report["issues"]:
                print(f"    - {issue}")
        else:
            print("  [PASS] 未发现结构一致性问题")


if __name__ == "__main__":
    main()
