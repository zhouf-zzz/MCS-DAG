import argparse
import json
import random
from pathlib import Path

from task_set import Drs_gengerate


def task_to_dict(task):
    data = {
        "id": task.id,
        "criticality": "HI" if task.cri == 0 else "LO",
        "cri": task.cri,
        "eLO": task.eLO,
        "eHI": task.eHI,
        "dLO": task.dLO,
        "dHI": task.dHI,
        "pLO": task.pLO,
        "pHI": task.pHI,
        "uLO": task.uLO,
        "uHI": task.uHI,
        "dag_id": task.dag_id,
        "predecessors": sorted(task.predecessors),
        "successors": sorted(task.successors),
    }

    if task.internal_dag is not None:
        internal_nodes = []
        for node_id, node in sorted(task.internal_dag.nodes.items()):
            internal_nodes.append(
                {
                    "node_id": node_id,
                    "tag": node.tag,
                    "cri": node.cri,
                    "eLO": node.eLO,
                    "eHI": node.eHI,
                    "uLO": node.uLO,
                    "uHI": node.uHI,
                    "predecessors": sorted(node.predecessors),
                    "successors": sorted(node.successors),
                }
            )

        data["internal_dag"] = {
            "root_nodes": list(task.internal_dag.root_nodes),
            "sink_nodes": list(task.internal_dag.sink_nodes),
            "longest_path_nodes": task.internal_dag.longest_path_nodes,
            "max_depth_limit": task.internal_dag.max_depth_limit,
            "edge_prob": task.internal_dag.edge_prob,
            "nodes": internal_nodes,
        }

    return data


def generate_single_taskset(args):
    ts = Drs_gengerate(
        args.task_number,
        args.system_utilization,
        args.cf,
        args.cp,
        args.node_number,
    )

    tasks = sorted(ts.LO, key=lambda t: t.id)
    hi_task_ids = sorted(task.id for task in ts.HI)

    return {
        "summary": {
            "task_count": len(tasks),
            "hi_count": len(hi_task_ids),
            "lo_only_count": len(tasks) - len(hi_task_ids),
            "sum_uLO": sum(task.uLO for task in tasks),
            "sum_uHI": sum(task.uHI for task in tasks if task.cri == 0),
        },
        "hi_task_ids": hi_task_ids,
        "tasks": [task_to_dict(task) for task in tasks],
    }


def parse_args():
    parser = argparse.ArgumentParser(description="批量生成随机混合关键度任务集并保存到 JSON 文件")
    parser.add_argument("--count", type=int, default=10, help="生成任务集的数量")
    parser.add_argument("--task-number", type=int, default=10, help="每个任务集中的任务数量")
    parser.add_argument("--node-number", type=int, default=4, help="处理器核数")
    parser.add_argument("--system-utilization", type=float, default=2.0, help="系统总利用率")
    parser.add_argument("--cf", type=float, default=2.0, help="高关键度任务在 HI 模式下的放大因子")
    parser.add_argument("--cp", type=float, default=0.5, help="高关键度任务占比")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--output", type=Path, default=Path("generated_tasksets.json"), help="输出文件路径")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.count <= 0:
        raise ValueError("--count 必须为正整数")

    random.seed(args.seed)

    dataset = {
        "config": {
            "count": args.count,
            "task_number": args.task_number,
            "node_number": args.node_number,
            "system_utilization": args.system_utilization,
            "cf": args.cf,
            "cp": args.cp,
            "seed": args.seed,
        },
        "tasksets": [generate_single_taskset(args) for _ in range(args.count)],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"已生成 {args.count} 个任务集，并保存到 {args.output}")


if __name__ == "__main__":
    main()
