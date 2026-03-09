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
    task_set = ts.HI.union(ts.LO)
    mapped_ids = _mapped_task_ids(mapping_list)
    dag_tasks = [t for t in task_set if t.dag_id == dag_id and t.id in mapped_ids]
    if not dag_tasks:
        return True

    mapped_id_set = {t.id for t in dag_tasks}

    for task in dag_tasks:
        cal_wcrt(mapping_list, ts, task, wcrt_algor)
        if task.wcrt_intertask == -1:
            return False

    sink_tasks = [
        task for task in dag_tasks
        if len(set(task.successors).intersection(mapped_id_set)) == 0
    ]
    for sink in sink_tasks:
        cal_wcrt(mapping_list, ts, sink, wcrt_algor)
        if sink.final_wcrt == -1 or sink.final_wcrt > sink.dLO:
            return False
    return True


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


def FF_DU(ts, wcrt_algor=amc_rtb_wcrt):
    task_set = ts.HI.union(ts.LO)
    tasks = sorted(task_set, key=lambda task: max(task.uLO, task.uHI), reverse=True)
    return _first_fit(tasks, ts, wcrt_algor)

def BF_FF_DP(ts): #WF
    task_set = ts.HI.union(ts.LO)
    tasks = sorted(task_set, key=lambda task: task.pri, reverse=True)
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
