import random
from wcrt_cal import *

# 线性核心模型：不再使用二维行/列拓扑
node_number = 4
MAX = 1000000000000


def _task_u_lo(task):
    return getattr(task, "uLO_core", task.uLO)


def _task_u_hi(task):
    return getattr(task, "uHI_core", task.uHI)


def _empty_mapping():
    return [list() for _ in range(node_number)]


def _mapped_task_ids(mapping_list):
    ids = set()
    for core_tasks in mapping_list:
        ids.update(core_tasks)
    return ids


def _try_place(mapping_list, task, core_id):
    mapping_list[core_id].append(task.id)
    task.core_list_add(core_id)


def _undo_place(mapping_list, task, core_id):
    mapping_list[core_id].remove(task.id)
    task.reset_core_list()


def _dag_deadline_ok(mapping_list, ts, dag_id, wcrt_algor=amc_rtb_wcrt):
    """
    判定已映射 DAG 的截止期：
    1) DAG 内已映射节点的局部 WCRT 不能为 -1；
    2) DAG 出口节点（无后继或后继未映射）的 end-to-end 完成时间 `final_wcrt`
       不得超过该出口节点的 dLO（当前项目中作为 DAG 截止期约束口径）。
    """
    analysis = analyze_dag_partitioned_fp(mapping_list, ts, dag_id, wcrt_algor)
    return analysis['schedulable']


def _all_mapped_dags_deadline_ok(mapping_list, ts, wcrt_algor=amc_rtb_wcrt):
    task_set = ts.HI.union(ts.LO)
    mapped_ids = _mapped_task_ids(mapping_list)
    dag_ids = {t.dag_id for t in task_set if t.id in mapped_ids}
    for dag_id in dag_ids:
        if not _dag_deadline_ok(mapping_list, ts, dag_id, wcrt_algor):
            return False
    return True


def random_mapping(task_set):
    mapping_list = _empty_mapping()
    for task in task_set:
        core_id = random.randint(0, node_number - 1)
        _try_place(mapping_list, task, core_id)
    return mapping_list


def order_mapping(task_set):
    mapping_list = _empty_mapping()
    for idx, task in enumerate(task_set):
        core_id = idx % node_number
        _try_place(mapping_list, task, core_id)
    return mapping_list


def uti_mapping(task_set):
    mapping_list = _empty_mapping()
    core_uti_list_LO = [0 for _ in range(node_number)]
    core_uti_list_HI = [0 for _ in range(node_number)]
    for task in task_set:
        best_core = 0
        best_pressure = MAX
        for core_id in range(node_number):
            p = max(core_uti_list_LO[core_id] + task.uLO, core_uti_list_HI[core_id] + task.uHI)
            if p < best_pressure:
                best_pressure = p
                best_core = core_id
        _try_place(mapping_list, task, best_core)
        core_uti_list_LO[best_core] += task.uLO
        core_uti_list_HI[best_core] += task.uHI
    return mapping_list, core_uti_list_LO, core_uti_list_HI


def _first_fit(tasks, ts, wcrt_algor=amc_rtb_wcrt):
    mapping_list = _empty_mapping()
    mapped_task_list = []
    for task in tasks:
        placed = False
        for core_id in range(node_number):
            _try_place(mapping_list, task, core_id)
            mapped_task_list.append(task)
            ok = _all_mapped_dags_deadline_ok(mapping_list, ts, wcrt_algor)
            if ok:
                placed = True
                break
            _undo_place(mapping_list, task, core_id)
            mapped_task_list.remove(task)
        if not placed:
            return False
    return mapping_list


def _fit_by_pressure(tasks, ts, descending=False, wcrt_algor=amc_rtb_wcrt):
    mapping_list = _empty_mapping()
    core_uti_list_LO = [0 for _ in range(node_number)]
    core_uti_list_HI = [0 for _ in range(node_number)]
    for task in tasks:
        candidates = []
        for core_id in range(node_number):
            lo = core_uti_list_LO[core_id] + _task_u_lo(task)
            hi = core_uti_list_HI[core_id] + _task_u_hi(task)
            pressure = max(lo, hi)
            candidates.append((core_id, pressure, lo, hi))
        candidates.sort(key=lambda x: x[1], reverse=descending)

        placed = False
        for core_id, _, lo, hi in candidates:
            _try_place(mapping_list, task, core_id)
            if _all_mapped_dags_deadline_ok(mapping_list, ts, wcrt_algor):
                core_uti_list_LO[core_id] = lo
                core_uti_list_HI[core_id] = hi
                placed = True
                break
            _undo_place(mapping_list, task, core_id)
        if not placed:
            return False
    return mapping_list


def _core_hp_interference_score(core_task_ids, task_by_id, task):
    """估计把 task 放入当前核心后受到的高优先级干扰强度。"""
    score = 0.0
    for task_id in core_task_ids:
        core_task = task_by_id.get(task_id)
        if core_task is None:
            continue
        if core_task.pri > task.pri:
            score += max(_task_u_lo(core_task), _task_u_hi(core_task))
    return score


def _dag_criticality_impact(task_by_id, mapped_ids, task, target_core):
    """估计将任务放到目标核心后对 DAG 关键链带来的跨核边压力（忽略通信开销时用于排序）。"""
    impact = 0.0

    for pred_id in task.predecessors:
        pred = task_by_id.get(pred_id)
        if pred is None or pred_id not in mapped_ids or len(pred.core_list) == 0:
            continue
        if pred.core_list[0] != target_core:
            impact += 1.0

    for succ_id in task.successors:
        succ = task_by_id.get(succ_id)
        if succ is None or succ_id not in mapped_ids or len(succ.core_list) == 0:
            continue
        if succ.core_list[0] != target_core:
            impact += 1.0

    return impact


def BF_DIP(ts, alpha=0.4, beta=0.4, gamma=0.2, wcrt_algor=amc_rtb_wcrt):
    """
    Best-Fit Decreasing by Interference Pressure:
    score(core) = alpha * utilization_pressure + beta * hp_interference + gamma * dag_impact
    """
    task_set = ts.HI.union(ts.LO)
    tasks = sorted(task_set, key=lambda task: max(_task_u_lo(task), _task_u_hi(task)), reverse=True)
    task_by_id = {task.id: task for task in task_set}

    mapping_list = _empty_mapping()
    core_uti_list_LO = [0.0 for _ in range(node_number)]
    core_uti_list_HI = [0.0 for _ in range(node_number)]

    for task in tasks:
        mapped_ids = _mapped_task_ids(mapping_list)
        candidates = []
        for core_id in range(node_number):
            lo = core_uti_list_LO[core_id] + _task_u_lo(task)
            hi = core_uti_list_HI[core_id] + _task_u_hi(task)
            utilization_pressure = max(lo, hi)
            hp_interference = _core_hp_interference_score(mapping_list[core_id], task_by_id, task)
            dag_impact = _dag_criticality_impact(task_by_id, mapped_ids, task, core_id)
            score = alpha * utilization_pressure + beta * hp_interference + gamma * dag_impact
            candidates.append((core_id, score, lo, hi))

        candidates.sort(key=lambda x: x[1])

        placed = False
        for core_id, _, lo, hi in candidates:
            _try_place(mapping_list, task, core_id)
            if _all_mapped_dags_deadline_ok(mapping_list, ts, wcrt_algor):
                core_uti_list_LO[core_id] = lo
                core_uti_list_HI[core_id] = hi
                placed = True
                break
            _undo_place(mapping_list, task, core_id)

        if not placed:
            return False

    return mapping_list


def FF_DU(ts, wcrt_algor=amc_rtb_wcrt):
    task_set = ts.HI.union(ts.LO)
    tasks = sorted(task_set, key=lambda task: max(task.uLO, task.uHI), reverse=True)
    return _first_fit(tasks, ts, wcrt_algor)

def BF_DU(ts, wcrt_algor=amc_rtb_wcrt):
    task_set = ts.HI.union(ts.LO)
    tasks = sorted(task_set, key=lambda task: max(_task_u_lo(task), _task_u_hi(task)), reverse=True)
    return _fit_by_pressure(tasks, ts, descending=True, wcrt_algor=wcrt_algor)


def BF_DP(ts, wcrt_algor=amc_rtb_wcrt):
    task_set = ts.HI.union(ts.LO)
    tasks = sorted(task_set, key=lambda task: task.pri, reverse=True)
    return _fit_by_pressure(tasks, ts, descending=True, wcrt_algor=wcrt_algor)


def WF_DU(ts):
    task_set = ts.HI.union(ts.LO)
    tasks = sorted(task_set, key=lambda task: max(_task_u_lo(task), _task_u_hi(task)), reverse=True)
    return _fit_by_pressure(tasks, ts, descending=False, wcrt_algor=amc_rtb_wcrt)


def WF_DP(ts, wcrt_algor=amc_rtb_wcrt):
    task_set = ts.HI.union(ts.LO)
    tasks = sorted(task_set, key=lambda task: task.pri, reverse=True)
    return _fit_by_pressure(tasks, ts, descending=False, wcrt_algor=wcrt_algor)


def WF_DP_new(ts, wcrt_algor=amc_rtb_wcrt):
    return WF_DP(ts, wcrt_algor)


def BF_FF_DP(ts):
    task_set = ts.HI.union(ts.LO)
    tasks = sorted(task_set, key=lambda task: (task.cri, task.pri), reverse=True)
    return _fit_by_pressure(tasks, ts, descending=True, wcrt_algor=amc_rtb_wcrt)
