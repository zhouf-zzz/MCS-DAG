import random
from wcrt_cal import *

# 线性核心模型：不再使用二维行/列拓扑
node_number = 16
MAX = 1000000000000


def _task_u_lo(task):
    return getattr(task, "uLO_core", task.uLO)


def _task_u_hi(task):
    return getattr(task, "uHI_core", task.uHI)


def _empty_mapping():
    return [list() for _ in range(node_number)]


def _try_place(mapping_list, task, core_id):
    mapping_list[core_id].append(task.id)
    task.core_list_add(core_id)


def _undo_place(mapping_list, task, core_id):
    mapping_list[core_id].remove(task.id)
    task.reset_core_list()


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
            ok = True
            for mapped_task in mapped_task_list:
                cal_wcrt(mapping_list, ts, mapped_task, wcrt_algor)
                if mapped_task.final_wcrt > mapped_task.dLO or mapped_task.wcrt_intertask == -1:
                    ok = False
                    break
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
            cal_wcrt(mapping_list, ts, task, wcrt_algor)
            if task.final_wcrt <= task.dLO and task.wcrt_intertask != -1:
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


def FF_DP(ts, wcrt_algor=amc_rtb_wcrt):
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
