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


def _iter_mapping_units(task_set):
    """
    生成映射单元：优先按“子任务”映射；若任务无内部 DAG，则退化为任务级单元。
    返回项字段：task, unit_key, uLO, uHI, pri。
    """
    units = []
    for task in task_set:
        if task.internal_dag is not None and len(task.internal_dag.nodes) > 0:
            for node_id, node in sorted(task.internal_dag.nodes.items()):
                units.append({
                    'task': task,
                    'unit_key': (task.id, node_id),
                    'uLO': float(node.uLO),
                    'uHI': float(node.uHI),
                    'pri': task.pri,
                })
        else:
            units.append({
                'task': task,
                'unit_key': (task.id, None),
                'uLO': float(task.uLO),
                'uHI': float(task.uHI),
                'pri': task.pri,
            })
    return units


def _place_unit(mapping_list, unit, core_id):
    task = unit['task']
    mapping_list[core_id].append(task.id)
    task.core_list_add(core_id)


def _undo_unit(mapping_list, unit, core_id):
    task = unit['task']
    mapping_list[core_id].remove(task.id)
    if task.id not in mapping_list[core_id]:
        task.core_list_remove(core_id)


def _dag_deadline_ok(mapping_list, ts, dag_id, wcrt_algor=amc_rtb_wcrt):
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
    for unit in _iter_mapping_units(task_set):
        core_id = random.randint(0, node_number - 1)
        _place_unit(mapping_list, unit, core_id)
    return mapping_list


def order_mapping(task_set):
    mapping_list = _empty_mapping()
    for idx, unit in enumerate(_iter_mapping_units(task_set)):
        core_id = idx % node_number
        _place_unit(mapping_list, unit, core_id)
    return mapping_list


def uti_mapping(task_set):
    mapping_list = _empty_mapping()
    core_uti_list_LO = [0 for _ in range(node_number)]
    core_uti_list_HI = [0 for _ in range(node_number)]
    for unit in _iter_mapping_units(task_set):
        best_core = 0
        best_pressure = MAX
        for core_id in range(node_number):
            p = max(core_uti_list_LO[core_id] + unit['uLO'], core_uti_list_HI[core_id] + unit['uHI'])
            if p < best_pressure:
                best_pressure = p
                best_core = core_id
        _place_unit(mapping_list, unit, best_core)
        core_uti_list_LO[best_core] += unit['uLO']
        core_uti_list_HI[best_core] += unit['uHI']
    return mapping_list, core_uti_list_LO, core_uti_list_HI


def _first_fit(units, ts, wcrt_algor=amc_rtb_wcrt):
    mapping_list = _empty_mapping()
    for unit in units:
        placed = False
        for core_id in range(node_number):
            _place_unit(mapping_list, unit, core_id)
            ok = _all_mapped_dags_deadline_ok(mapping_list, ts, wcrt_algor)
            if ok:
                placed = True
                break
            _undo_unit(mapping_list, unit, core_id)
        if not placed:
            return False
    return mapping_list


def _fit_by_pressure(units, ts, descending=False, wcrt_algor=amc_rtb_wcrt):
    mapping_list = _empty_mapping()
    core_uti_list_LO = [0 for _ in range(node_number)]
    core_uti_list_HI = [0 for _ in range(node_number)]
    for unit in units:
        candidates = []
        for core_id in range(node_number):
            lo = core_uti_list_LO[core_id] + unit['uLO']
            hi = core_uti_list_HI[core_id] + unit['uHI']
            pressure = max(lo, hi)
            candidates.append((core_id, pressure, lo, hi))
        candidates.sort(key=lambda x: x[1], reverse=descending)

        placed = False
        for core_id, _, lo, hi in candidates:
            _place_unit(mapping_list, unit, core_id)
            if _all_mapped_dags_deadline_ok(mapping_list, ts, wcrt_algor):
                core_uti_list_LO[core_id] = lo
                core_uti_list_HI[core_id] = hi
                placed = True
                break
            _undo_unit(mapping_list, unit, core_id)
        if not placed:
            return False
    return mapping_list


def _core_hp_interference_score(core_task_ids, task_by_id, task):
    score = 0.0
    for task_id in set(core_task_ids):
        core_task = task_by_id.get(task_id)
        if core_task is None:
            continue
        if core_task.pri > task.pri:
            score += max(_task_u_lo(core_task), _task_u_hi(core_task))
    return score


def _dag_criticality_impact(task_by_id, mapped_ids, task, target_core):
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
    task_set = ts.HI.union(ts.LO)
    units = sorted(_iter_mapping_units(task_set), key=lambda u: max(u['uLO'], u['uHI']), reverse=True)
    task_by_id = {task.id: task for task in task_set}

    mapping_list = _empty_mapping()
    core_uti_list_LO = [0.0 for _ in range(node_number)]
    core_uti_list_HI = [0.0 for _ in range(node_number)]

    for unit in units:
        task = unit['task']
        mapped_ids = _mapped_task_ids(mapping_list)
        candidates = []
        for core_id in range(node_number):
            lo = core_uti_list_LO[core_id] + unit['uLO']
            hi = core_uti_list_HI[core_id] + unit['uHI']
            utilization_pressure = max(lo, hi)
            hp_interference = _core_hp_interference_score(mapping_list[core_id], task_by_id, task)
            dag_impact = _dag_criticality_impact(task_by_id, mapped_ids, task, core_id)
            score = alpha * utilization_pressure + beta * hp_interference + gamma * dag_impact
            candidates.append((core_id, score, lo, hi))

        candidates.sort(key=lambda x: x[1])

        placed = False
        for core_id, _, lo, hi in candidates:
            _place_unit(mapping_list, unit, core_id)
            if _all_mapped_dags_deadline_ok(mapping_list, ts, wcrt_algor):
                core_uti_list_LO[core_id] = lo
                core_uti_list_HI[core_id] = hi
                placed = True
                break
            _undo_unit(mapping_list, unit, core_id)

        if not placed:
            return False

    return mapping_list


def FF_DU(ts, wcrt_algor=amc_rtb_wcrt):
    task_set = ts.HI.union(ts.LO)
    units = sorted(_iter_mapping_units(task_set), key=lambda u: max(u['uLO'], u['uHI']), reverse=True)
    return _first_fit(units, ts, wcrt_algor)


def BF_DU(ts, wcrt_algor=amc_rtb_wcrt):
    task_set = ts.HI.union(ts.LO)
    units = sorted(_iter_mapping_units(task_set), key=lambda u: max(u['uLO'], u['uHI']), reverse=True)
    return _fit_by_pressure(units, ts, descending=True, wcrt_algor=wcrt_algor)


def BF_DP(ts, wcrt_algor=amc_rtb_wcrt):
    task_set = ts.HI.union(ts.LO)
    units = sorted(_iter_mapping_units(task_set), key=lambda u: u['pri'], reverse=True)
    return _fit_by_pressure(units, ts, descending=True, wcrt_algor=wcrt_algor)


def WF_DU(ts):
    task_set = ts.HI.union(ts.LO)
    units = sorted(_iter_mapping_units(task_set), key=lambda u: max(u['uLO'], u['uHI']), reverse=True)
    return _fit_by_pressure(units, ts, descending=False, wcrt_algor=amc_rtb_wcrt)


def WF_DP(ts, wcrt_algor=amc_rtb_wcrt):
    task_set = ts.HI.union(ts.LO)
    units = sorted(_iter_mapping_units(task_set), key=lambda u: u['pri'], reverse=True)
    return _fit_by_pressure(units, ts, descending=False, wcrt_algor=wcrt_algor)


def WF_DP_new(ts, wcrt_algor=amc_rtb_wcrt):
    return WF_DP(ts, wcrt_algor)


def BF_FF_DP(ts):
    task_set = ts.HI.union(ts.LO)
    units = sorted(_iter_mapping_units(task_set), key=lambda u: (u['task'].cri, u['pri']), reverse=True)
    return _fit_by_pressure(units, ts, descending=True, wcrt_algor=amc_rtb_wcrt)
