import time
from task_set import Drs_gengerate
from mapping import FF_DP, WF_DU, BF_DIP, _all_mapped_dags_deadline_ok


def _reset_tasks(ts):
    for task in ts.HI.union(ts.LO):
        task.reset()


def _is_mapping_valid(mapping_list, ts):
    if mapping_list is False:
        return False
    task_ids = {task.id for task in ts.HI.union(ts.LO)}
    mapped_ids = set()
    for core_tasks in mapping_list:
        mapped_ids.update(core_tasks)
    if mapped_ids != task_ids:
        return False
    return _all_mapped_dags_deadline_ok(mapping_list, ts)


def validate_mapping_reliability(
    task_number=20,
    node_number=4,
    cycles=100,
    uti_start=0.2,
    uti_step=0.1,
    uti_points=6,
):
    """
    使用已有映射算法构建“对照式验证”：
    - 主算法: BF_DIP
    - 对照算法: FF_DP, WF_DU

    输出每个利用率下三种算法的可调度率与运行时间。
    """
    algorithms = {
        "BF_DIP": BF_DIP,
        "FF_DP": FF_DP,
        "WF_DU": WF_DU,
    }

    result = {
        name: {
            "schedulable": [0 for _ in range(uti_points)],
            "runtime": [0.0 for _ in range(uti_points)],
            "inconsistent": [0 for _ in range(uti_points)],
        }
        for name in algorithms
    }

    uti_list = []
    for j in range(uti_points):
        system_uti = uti_start + uti_step * j
        uti_list.append(system_uti)
        for _ in range(cycles):
            ts = Drs_gengerate(task_number, system_uti * node_number, 2, 0.5, node_number)
            task_set = ts.HI.union(ts.LO)
            ts.priority_assignment_DM_HI(task_set, 0)

            for name, mapper in algorithms.items():
                start = time.time()
                mapping_list = mapper(ts)
                elapsed = time.time() - start
                result[name]["runtime"][j] += elapsed

                if mapping_list is not False and not _all_mapped_dags_deadline_ok(mapping_list, ts):
                    result[name]["inconsistent"][j] += 1

                if _is_mapping_valid(mapping_list, ts):
                    result[name]["schedulable"][j] += 1

                _reset_tasks(ts)

    summary = {
        "utilization": uti_list,
        "algorithms": {},
    }

    for name in algorithms:
        summary["algorithms"][name] = {
            "schedulable_ratio": [float(x) / cycles for x in result[name]["schedulable"]],
            "avg_runtime_s": [x / cycles for x in result[name]["runtime"]],
            "inconsistent_count": result[name]["inconsistent"],
        }

    return summary


def print_validation_report(summary):
    uti_list = summary["utilization"]
    for idx, uti in enumerate(uti_list):
        print(f"[U={uti:.2f}]")
        for name, stats in summary["algorithms"].items():
            ratio = stats["schedulable_ratio"][idx]
            runtime = stats["avg_runtime_s"][idx]
            inconsistent = stats["inconsistent_count"][idx]
            print(
                f"  {name:<8} ratio={ratio:.3f} avg_runtime={runtime:.6f}s inconsistent={inconsistent}"
            )


if __name__ == "__main__":
    summary = validate_mapping_reliability()
    print_validation_report(summary)
