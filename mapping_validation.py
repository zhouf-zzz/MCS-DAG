import os
import time
from mapping import _all_mapped_dags_deadline_ok, _expected_unit_keys


def _check_runtime_dependencies():
    """提前检查运行时依赖并返回缺失项，避免在深层 import 处报错。"""
    missing = []
    for module_name in ("numpy", "scipy", "matplotlib", "tqdm"):
        try:
            __import__(module_name)
        except ModuleNotFoundError:
            missing.append(module_name)
    return missing


def _reset_tasks(ts):
    for task in ts.HI.union(ts.LO):
        task.reset()


def _is_mapping_valid(mapping_list, ts):
    if mapping_list is False:
        return False
    expected_units = _expected_unit_keys(ts.HI.union(ts.LO))
    mapped_units = set()
    for core_tasks in mapping_list:
        for unit_key in core_tasks:
            if isinstance(unit_key, tuple):
                mapped_units.add(unit_key)
            else:
                mapped_units.add((unit_key, None))
    if mapped_units != expected_units:
        return False
    return _all_mapped_dags_deadline_ok(mapping_list, ts)


def validate_mapping_reliability(
    task_number=6,
    node_number=8,
    cycles=100,
    uti_start=0.2,
    uti_step=0.1,
    uti_points=6,
    disable_internal_subtask=False,
    show_progress=True,
    progress_interval=0,
):
    """
    使用已有映射算法构建“对照式验证”：
    - 主算法: BF_DIP
    - 对照算法: BF_DP, WF_DU

    输出每个利用率下三种算法的可调度率与运行时间。
    """
    from task_set import Drs_gengerate
    from mapping import BF_DP, WF_DU, BF_DIP

    algorithms = {
        "BF_DIP": BF_DIP,
        "BF_DP": BF_DP,
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
        cycle_range = range(cycles)
        if show_progress:
            from tqdm import tqdm

            tqdm_kwargs = {
                "desc": f"U={system_uti:.2f} ({j + 1}/{uti_points})",
                "unit": "items",
                "ncols": 100,
            }
            if progress_interval > 0:
                tqdm_kwargs["miniters"] = progress_interval
            cycle_range = tqdm(cycle_range, **tqdm_kwargs)

        for cycle_idx in cycle_range:
            ts = Drs_gengerate(
                task_number,
                system_uti * node_number,
                2,
                0.5,
                node_number,
                internal_subtask_enable=not disable_internal_subtask,
            )
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
        "meta": {
            "task_number": task_number,
            "node_number": node_number,
            "cycles": cycles,
            "uti_start": uti_start,
            "uti_step": uti_step,
            "uti_points": uti_points,
            "disable_internal_subtask": disable_internal_subtask,
            "show_progress": show_progress,
            "progress_interval": progress_interval,
        },
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


def plot_validation_summary(summary, out_dir="result", prefix="mapping_validation"):
    """绘制并保存三类图：可调度率、平均运行时间、不一致次数。"""
    os.makedirs(out_dir, exist_ok=True)

    uti_list = summary["utilization"]
    algos = summary["algorithms"]
    colors = {
        "BF_DIP": "royalblue",
        "BF_DP": "seagreen",
        "WF_DU": "darkorange",
    }
    markers = {
        "BF_DIP": "o",
        "BF_DP": "s",
        "WF_DU": "^",
    }

    import matplotlib.pyplot as plt

    def _plot(metric_key, y_label, filename):
        plt.figure(figsize=(7, 4.5))
        for name, stats in algos.items():
            plt.plot(
                uti_list,
                stats[metric_key],
                linewidth=1.5,
                marker=markers.get(name, "o"),
                color=colors.get(name, None),
                label=name,
            )
        plt.xlabel("System Utilization")
        plt.ylabel(y_label)
        plt.grid(True, linestyle="--", alpha=0.4)
        plt.legend()
        plt.tight_layout()
        png_path = os.path.join(out_dir, f"{prefix}_{filename}.png")
        pdf_path = os.path.join(out_dir, f"{prefix}_{filename}.pdf")
        plt.savefig(png_path, bbox_inches="tight")
        plt.savefig(pdf_path, bbox_inches="tight")
        plt.close()
        return png_path, pdf_path

    paths = {
        "schedulable_ratio": _plot("schedulable_ratio", "Schedulable Ratio", "schedulable_ratio"),
        "avg_runtime_s": _plot("avg_runtime_s", "Average Runtime (s)", "avg_runtime"),
        "inconsistent_count": _plot("inconsistent_count", "Inconsistent Count", "inconsistent"),
    }
    return paths


def run_validation_with_plots(
    task_number=6,
    node_number=8,
    cycles=100,
    uti_start=0.2,
    uti_step=0.1,
    uti_points=6,
    out_dir="result",
    disable_internal_subtask=False,
    show_progress=True,
    progress_interval=0,
):
    summary = validate_mapping_reliability(
        task_number=task_number,
        node_number=node_number,
        cycles=cycles,
        uti_start=uti_start,
        uti_step=uti_step,
        uti_points=uti_points,
        disable_internal_subtask=disable_internal_subtask,
        show_progress=show_progress,
        progress_interval=progress_interval,
    )
    print_validation_report(summary)
    figure_paths = plot_validation_summary(summary, out_dir=out_dir)
    return summary, figure_paths


if __name__ == "__main__":
    missing_modules = _check_runtime_dependencies()
    if missing_modules:
        raise SystemExit(
            "缺少运行依赖："
            + ", ".join(missing_modules)
            + "。请先执行 `python3 -m pip install "
            + " ".join(missing_modules)
            + "` 后重试。"
        )

    summary, figure_paths = run_validation_with_plots()
    print("\nSaved figures:")
    for metric, paths in figure_paths.items():
        print(f"  {metric}: {paths[0]}, {paths[1]}")
