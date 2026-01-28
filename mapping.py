import random
from math import *
import copy
from wcrt_cal import *
#from task_set import Drs_gengerate
task_number = 30
node_number = cluster_col * cluster_row
MAX = 1000000000000
from task_set import task_length_max

def get_core_id(i, j):
    return i * cluster_row + j


def random_mapping(task_set):
    random_mapping_list = [list() for _ in range(node_number)]
    for task in task_set:
        start_row = random.randint(0, cluster_row - task.width + 1)
        start_col = random.randint(0, cluster_col - task.length + 1)
        for i in range(start_row, start_row + task.width):
            for j in range(start_col, start_col + task.length):
                core_id = get_core_id(i, j)
                random_mapping_list[core_id].append(task.id)
                task.core_list_add(core_id)
    return random_mapping_list

def order_mapping(task_set):
    order_mapping_list = [list() for _ in range(node_number)]
    start_col = 0
    start_row = 0
    row_max_col = 0
    for task in task_set:
        if start_col + task.length > cluster_col:
            start_row += row_max_col
            start_col = 0
        if start_row + task.width  > cluster_row:
            start_row = 0 
        for i in range(start_row, start_row + task.width):
            for j in range(start_col, start_col + task.length):
                core_id = get_core_id(i, j)
                order_mapping_list[core_id].append(task.id)
                task.core_list_add(core_id)
        start_col += task.length
        row_max_col = max(row_max_col, task.width)
    return order_mapping_list

def uti_mapping(task_set): #WF
    uti_mapping_list = [list() for _ in range(node_number)] #映射列表
    core_uti_list_LO = [0 for _ in range(node_number)] #已映射任务低关键度模式利用率分布
    core_uti_list_HI = [0 for _ in range(node_number)] #已映射任务高关键度模式利用率分布
    for task in task_set:
        total_min_uti = MAX #所以映射位置最高利用率的最低值
        final_start_row = 0 
        final_start_col = 0
        for start_row in range(0, cluster_row - task.width + 1): #遍历所有映射情况
            for start_col in range(0, cluster_col - task.length + 1):
                core_max_uti = 0 #该映射情况下所有核心的最大利用率
                for i in range(start_row, start_row + task.width):
                    for j in range(start_col, start_col + task.length):
                        core_id = get_core_id(i, j)
                        core_uti_LO = core_uti_list_LO[core_id] + task.uLO
                        core_uti_Hi = core_uti_list_HI[core_id] + task.uHI 
                        core_max_uti = max(core_max_uti, core_uti_LO, core_uti_Hi)
                if core_max_uti < total_min_uti:
                    total_min_uti = core_max_uti
                    final_start_row = start_row
                    final_start_col = start_col
        for i in range(final_start_row, final_start_row + task.width):
            for j in range(final_start_col, final_start_col + task.length):
                core_id = get_core_id(i, j)
                uti_mapping_list[core_id].append(task.id)
                task.core_list_add(core_id)
                core_uti_list_LO[core_id] += task.uLO
                core_uti_list_HI[core_id] += task.uHI
    return uti_mapping_list, core_uti_list_LO, core_uti_list_HI

def FF_DU(ts, wcrt_algor = amc_rtb_wcrt):
    task_set = ts.HI.union(ts.LO)
    FF_DU_mapping_list = [list() for _ in range(node_number)]
    #tasks_DU = sorted(task_set, key=lambda task:max(task.uLO_core,task.uHI_core), reverse = True)
    tasks_DU = sorted(task_set, key=lambda task:max(task.uLO,task.uHI), reverse = True)
    mapped_task_list = []
    for task in tasks_DU:
        schedule = 0
        for start_row in range(0, cluster_row - task.width + 1): #遍历所有映射情况
            for start_col in range(0, cluster_col - task.length + 1):
                #加入映射
                for i in range(start_row, start_row + task.width):
                    for j in range(start_col, start_col + task.length):
                        core_id = get_core_id(i, j)
                        FF_DU_mapping_list[core_id].append(task.id)
                        task.core_list_add(core_id)
                mapped_task_list.append(task)
                #计算已映射任务响应时间
                mapped_task_schedulable = 0
                for mapped_task in mapped_task_list:
                    cal_wcrt(FF_DU_mapping_list, ts, mapped_task, wcrt_algor)
                    #不可调度
                    if mapped_task.final_wcrt > mapped_task.dLO or mapped_task.wcrt_intertask == -1:
                        if (start_row == cluster_row - task.width) and (start_col == cluster_col - task.length):#该任务找不到可以调度的映射位置
                            return False
                        #清除映射
                        for i in range(start_row, start_row + task.width):
                            for j in range(start_col, start_col + task.length):
                                core_id = get_core_id(i, j)
                                FF_DU_mapping_list[core_id].remove(task.id)
                        task.reset_core_list()
                        mapped_task_list.remove(task)
                        mapped_task_schedulable = 1
                        break
                #当前映射位置可调度
                if mapped_task_schedulable == 0:
                    schedule = 1
                    break
            if schedule == 1:
                break
    return FF_DU_mapping_list

def FF_DP(ts, wcrt_algor = amc_rtb_wcrt):
    task_set = ts.HI.union(ts.LO)
    FF_DP_mapping_list = [list() for _ in range(node_number)]
    tasks_DP = sorted(task_set, key=lambda task:task.pri, reverse = True)
    for task in tasks_DP:
        schedule = 0
        for start_row in range(0, cluster_row - task.width + 1): #遍历所有映射情况
            for start_col in range(0, cluster_col - task.length + 1):
                #print(start_row , start_col)
                #加入映射
                for i in range(start_row, start_row + task.width):
                    for j in range(start_col, start_col + task.length):
                        core_id = get_core_id(i, j)
                        FF_DP_mapping_list[core_id].append(task.id)
                        task.core_list_add(core_id)
                #计算响应时间
                cal_wcrt(FF_DP_mapping_list, ts, task, wcrt_algor)
                #不可调度
                if task.final_wcrt > task.dLO or task.wcrt_intertask == -1:
                    if (start_row == cluster_row - task.width) and (start_col == cluster_col - task.length):#该任务找不到可以调度的映射位置
                        return False
                    #清除映射
                    for i in range(start_row, start_row + task.width):
                        for j in range(start_col, start_col + task.length):
                            core_id = get_core_id(i, j)
                            FF_DP_mapping_list[core_id].remove(task.id)
                    task.reset_core_list()
                #可以调度
                else:
                    schedule = 1
                    break
            if schedule == 1:
                break
    return FF_DP_mapping_list

def BF_DU(ts, wcrt_algor = amc_rtb_wcrt):
    task_set = ts.HI.union(ts.LO)
    BF_DU_mapping_list = [list() for _ in range(node_number)] #映射列表
    core_uti_list_LO = [0 for _ in range(node_number)] #已映射任务低关键度模式利用率分布
    core_uti_list_HI = [0 for _ in range(node_number)] #已映射任务高关键度模式利用率分布
    tasks_DU = sorted(task_set, key=lambda task:max(task.uLO_core,task.uHI_core), reverse = True)
    mapped_task_list = []
    for task in tasks_DU:
        place_min_uti_dict = {}
        for start_row in range(0, cluster_row - task.width + 1): #遍历所有映射情况
            for start_col in range(0, cluster_col - task.length + 1):
                core_min_uti = MAX #该映射情况下所有核心的最大利用率
                #遍历该任务所有核心
                for i in range(start_row, start_row + task.width):
                    for j in range(start_col, start_col + task.length):
                        core_id = get_core_id(i, j)
                        if task.cri == 0:
                            core_uti_LO = core_uti_list_LO[core_id] + task.uLO_core
                            core_uti_Hi = core_uti_list_HI[core_id] + task.uHI_core
                            core_min_uti = min(core_min_uti, core_uti_LO, core_uti_Hi)
                        else:
                            core_uti_LO = core_uti_list_LO[core_id]
                            core_min_uti = min(core_min_uti, core_uti_LO)
                left_up_core_id = get_core_id(start_row, start_col)
                place_min_uti_dict[left_up_core_id] = core_min_uti
        #字典排序
        sorted_dict = dict(sorted(place_min_uti_dict.items(), key=lambda item: item[1], reverse = True))
        last_key, _ = list(sorted_dict.items())[-1]#取最后一个键值对
        #遍历字典
        for left_up_core_id, _ in sorted_dict.items():
            start_row, start_col = get_place(left_up_core_id)
            #加入映射
            for i in range(start_row, start_row + task.width):
                for j in range(start_col, start_col + task.length):
                    core_id = get_core_id(i, j)
                    BF_DU_mapping_list[core_id].append(task.id)
                    task.core_list_add(core_id)
                    core_uti_list_LO[core_id] += task.uLO_core
                    core_uti_list_HI[core_id] += task.uHI_core
            mapped_task_list.append(task)
            mapped_task_schedulable = 0
            for mapped_task in mapped_task_list:
                #计算响应时间
                cal_wcrt(BF_DU_mapping_list, ts, mapped_task, wcrt_algor)
                #不可调度
                if mapped_task.final_wcrt > mapped_task.dLO or mapped_task.wcrt_intertask == -1:
                    if left_up_core_id == last_key:#该任务找不到可以调度的映射位置
                        return False
                    #清除映射
                    for i in range(start_row, start_row + task.width):
                        for j in range(start_col, start_col + task.length):
                            core_id = get_core_id(i, j)
                            BF_DU_mapping_list[core_id].remove(task.id)
                            core_uti_list_LO[core_id] -= task.uLO_core
                            core_uti_list_HI[core_id] -= task.uHI_core
                    task.reset_core_list()
                    mapped_task_list.remove(task)
                    mapped_task_schedulable = 1
                    break
                #可调度
            if mapped_task_schedulable == 0:
                break
    return BF_DU_mapping_list

def BF_DP(ts, wcrt_algor = amc_rtb_wcrt):
    task_set = ts.HI.union(ts.LO)
    BF_DP_mapping_list = [list() for _ in range(node_number)] #映射列表
    core_uti_list_LO = [0 for _ in range(node_number)] #已映射任务低关键度模式利用率分布
    core_uti_list_HI = [0 for _ in range(node_number)] #已映射任务高关键度模式利用率分布
    tasks_DP = sorted(task_set, key=lambda task:task.pri, reverse = True)
    for task in tasks_DP:
        place_min_uti_dict = {}
        for start_row in range(0, cluster_row - task.width + 1): #遍历所有映射情况
            for start_col in range(0, cluster_col - task.length + 1):
                core_min_uti = MAX #该映射情况下所有核心的最大利用率
                #遍历该任务所有核心
                for i in range(start_row, start_row + task.width):
                    for j in range(start_col, start_col + task.length):
                        core_id = get_core_id(i, j)
                        if task.cri == 0:
                            core_uti_LO = core_uti_list_LO[core_id] + task.uLO_core
                            core_uti_Hi = core_uti_list_HI[core_id] + task.uHI_core
                            core_min_uti = min(core_min_uti, core_uti_LO, core_uti_Hi)
                        else:
                            core_uti_LO = core_uti_list_LO[core_id]
                            core_min_uti = min(core_min_uti, core_uti_LO)
                left_up_core_id = get_core_id(start_row, start_col)
                place_min_uti_dict[left_up_core_id] = core_min_uti
        #字典排序
        sorted_dict = dict(sorted(place_min_uti_dict.items(), key=lambda item: item[1], reverse = True))
        last_key, _ = list(sorted_dict.items())[-1]#取最后一个键值对
        #遍历字典
        for left_up_core_id, _ in sorted_dict.items():
            start_row, start_col = get_place(left_up_core_id)
            #加入映射
            for i in range(start_row, start_row + task.width):
                for j in range(start_col, start_col + task.length):
                    core_id = get_core_id(i, j)
                    BF_DP_mapping_list[core_id].append(task.id)
                    task.core_list_add(core_id)
                    core_uti_list_LO[core_id] += task.uLO_core
                    core_uti_list_HI[core_id] += task.uHI_core
            #计算响应时间
            cal_wcrt(BF_DP_mapping_list, ts, task, wcrt_algor)
            #不可调度
            if task.final_wcrt > task.dLO or task.wcrt_intertask == -1:
                if left_up_core_id == last_key:#该任务找不到可以调度的映射位置
                    return False
                #清除映射
                for i in range(start_row, start_row + task.width):
                    for j in range(start_col, start_col + task.length):
                        core_id = get_core_id(i, j)
                        BF_DP_mapping_list[core_id].remove(task.id)
                        core_uti_list_LO[core_id] -= task.uLO_core
                        core_uti_list_HI[core_id] -= task.uHI_core
                task.reset_core_list()
            #可调度
            else:
                break
    return BF_DP_mapping_list

def WF_DU(ts): #WF_DU
    task_set = ts.HI.union(ts.LO)
    WF_DU_mapping_list = [list() for _ in range(node_number)] #映射列表
    core_uti_list_LO = [0 for _ in range(node_number)] #已映射任务低关键度模式利用率分布
    core_uti_list_HI = [0 for _ in range(node_number)] #已映射任务高关键度模式利用率分布
    mapped_task_list = []
    tasks_DP = sorted(task_set, key=lambda task:max(task.uLO_core,task.uHI_core), reverse = True)
    for task in tasks_DP:
        place_max_uti_dict = {}
        for start_row in range(0, cluster_row - task.width + 1): #遍历所有映射情况
            for start_col in range(0, cluster_col - task.length + 1):
                core_max_uti = 0 #该映射情况下所有核心的最大利用率
                #遍历该任务所有核心
                for i in range(start_row, start_row + task.width):
                    for j in range(start_col, start_col + task.length):
                        core_id = get_core_id(i, j)
                        if task.cri == 0:
                            core_uti_LO = core_uti_list_LO[core_id] + task.uLO_core
                            core_uti_Hi = core_uti_list_HI[core_id] + task.uHI_core
                            core_max_uti = max(core_max_uti, core_uti_LO, core_uti_Hi)
                        else:
                            core_uti_LO = core_uti_list_LO[core_id]
                            core_max_uti = max(core_max_uti, core_uti_LO)
                left_up_core_id = get_core_id(start_row, start_col)
                place_max_uti_dict[left_up_core_id] = core_max_uti
        #字典排序
        sorted_dict = dict(sorted(place_max_uti_dict.items(), key=lambda item: item[1]))
        last_key, _ = list(sorted_dict.items())[-1]#取最后一个键值对
        #遍历字典
        for left_up_core_id, _ in sorted_dict.items():
            start_row, start_col = get_place(left_up_core_id)
            #加入映射
            for i in range(start_row, start_row + task.width):
                for j in range(start_col, start_col + task.length):
                    core_id = get_core_id(i, j)
                    WF_DU_mapping_list[core_id].append(task.id)
                    task.core_list_add(core_id)
                    core_uti_list_LO[core_id] += task.uLO_core
                    core_uti_list_HI[core_id] += task.uHI_core
            mapped_task_list.append(task)
            mapped_task_schedulable = 0
            for mapped_task in mapped_task_list:
                #计算响应时间
                cal_wcrt(WF_DU_mapping_list, ts, mapped_task)
                #不可调度
                if mapped_task.final_wcrt > mapped_task.dLO or mapped_task.wcrt_intertask == -1:
                    if left_up_core_id == last_key:#该任务找不到可以调度的映射位置
                        return False
                    #清除映射
                    for i in range(start_row, start_row + task.width):
                        for j in range(start_col, start_col + task.length):
                            core_id = get_core_id(i, j)
                            WF_DU_mapping_list[core_id].remove(task.id)
                            core_uti_list_LO[core_id] -= task.uLO_core
                            core_uti_list_HI[core_id] -= task.uHI_core
                    task.reset_core_list()
                    mapped_task_list.remove(task)
                    mapped_task_schedulable = 1
                    break
                #可调度
            if mapped_task_schedulable == 0:
                break
    return WF_DU_mapping_list


def WF_DP(ts, wcrt_algor = amc_rtb_wcrt): #WF
    task_set = ts.HI.union(ts.LO)
    WF_DP_mapping_list = [list() for _ in range(node_number)] #映射列表
    core_uti_list_LO = [0 for _ in range(node_number)] #已映射任务低关键度模式利用率分布
    core_uti_list_HI = [0 for _ in range(node_number)] #已映射任务高关键度模式利用率分布
    tasks_DP = sorted(task_set, key=lambda task:task.pri, reverse = True)
    for task in tasks_DP:
        place_max_uti_dict = {}
        for start_row in range(0, cluster_row - task.width + 1): #遍历所有映射情况
            for start_col in range(0, cluster_col - task.length + 1):
                core_max_uti = 0 #该映射情况下所有核心的最大利用率
                #遍历该任务所有核心
                for i in range(start_row, start_row + task.width):
                    for j in range(start_col, start_col + task.length):
                        core_id = get_core_id(i, j)
                        if task.cri == 0:
                            core_uti_LO = core_uti_list_LO[core_id] + task.uLO_core
                            core_uti_Hi = core_uti_list_HI[core_id] + task.uHI_core
                            core_max_uti = max(core_max_uti, core_uti_LO, core_uti_Hi)
                        else:
                            core_uti_LO = core_uti_list_LO[core_id]
                            core_max_uti = max(core_max_uti, core_uti_LO)
                left_up_core_id = get_core_id(start_row, start_col)
                place_max_uti_dict[left_up_core_id] = core_max_uti
        #字典排序
        sorted_dict = dict(sorted(place_max_uti_dict.items(), key=lambda item: item[1]))
        last_key, _ = list(sorted_dict.items())[-1]#取最后一个键值对
        #遍历字典
        for left_up_core_id, _ in sorted_dict.items():
            start_row, start_col = get_place(left_up_core_id)
            #加入映射
            for i in range(start_row, start_row + task.width):
                for j in range(start_col, start_col + task.length):
                    core_id = get_core_id(i, j)
                    WF_DP_mapping_list[core_id].append(task.id)
                    task.core_list_add(core_id)
                    core_uti_list_LO[core_id] += task.uLO_core
                    core_uti_list_HI[core_id] += task.uHI_core
            #计算响应时间
            cal_wcrt(WF_DP_mapping_list, ts, task, wcrt_algor)
            #不可调度
            if task.final_wcrt > task.dLO or task.wcrt_intertask == -1:
                if left_up_core_id == last_key:#该任务找不到可以调度的映射位置
                    return False
                #清除映射
                for i in range(start_row, start_row + task.width):
                    for j in range(start_col, start_col + task.length):
                        core_id = get_core_id(i, j)
                        WF_DP_mapping_list[core_id].remove(task.id)
                        core_uti_list_LO[core_id] -= task.uLO_core
                        core_uti_list_HI[core_id] -= task.uHI_core
                task.reset_core_list()
            #可调度
            else:
                break
    return WF_DP_mapping_list

def WF_DP_new(ts, wcrt_algor = amc_rtb_wcrt): #error
    task_set = ts.HI.union(ts.LO)
    WF_DP_mapping_list = [list() for _ in range(node_number)] #映射列表
    core_uti_list_LO = [0 for _ in range(node_number)] #已映射任务低关键度模式利用率分布
    core_uti_list_HI = [0 for _ in range(node_number)] #已映射任务高关键度模式利用率分布
    tasks_DP = sorted(task_set, key=lambda task:task.pri, reverse = True)
    for task in tasks_DP:
        place_max_uti_dict = {}
        for start_row in range(0, cluster_row - task.width + 1): #遍历所有映射情况
            for start_col in range(0, cluster_col - task.length + 1):
                core_max_uti = 0 #该映射情况下所有核心的最大利用率\
                sum_uti_LO = 0
                sum_uti_HI = 0
                #遍历该任务所有核心
                for i in range(start_row, start_row + task.width):
                    for j in range(start_col, start_col + task.length):
                        core_id = get_core_id(i, j)
                        core_uti_LO = core_uti_list_LO[core_id]
                        core_uti_Hi = core_uti_list_HI[core_id]
                        sum_uti_LO += core_uti_LO
                        sum_uti_HI += core_uti_Hi
                core_max_uti = (max(sum_uti_LO,sum_uti_HI))/task.node_number
                left_up_core_id = get_core_id(start_row, start_col)
                place_max_uti_dict[left_up_core_id] = core_max_uti
        #字典排序
        sorted_dict = dict(sorted(place_max_uti_dict.items(), key=lambda item: item[1]))
        last_key, _ = list(sorted_dict.items())[-1]#取最后一个键值对
        #遍历字典
        for left_up_core_id, _ in sorted_dict.items():
            start_row, start_col = get_place(left_up_core_id)
            #加入映射
            for i in range(start_row, start_row + task.width):
                for j in range(start_col, start_col + task.length):
                    core_id = get_core_id(i, j)
                    WF_DP_mapping_list[core_id].append(task.id)
                    task.core_list_add(core_id)
                    core_uti_list_LO[core_id] += task.uLO_core
                    core_uti_list_HI[core_id] += task.uHI_core
            #计算响应时间
            cal_wcrt(WF_DP_mapping_list, ts, task, wcrt_algor)
            #不可调度
            if task.final_wcrt > task.dLO or task.wcrt_intertask == -1:
                if left_up_core_id == last_key:#该任务找不到可以调度的映射位置
                    return False
                #清除映射
                for i in range(start_row, start_row + task.width):
                    for j in range(start_col, start_col + task.length):
                        core_id = get_core_id(i, j)
                        WF_DP_mapping_list[core_id].remove(task.id)
                        core_uti_list_LO[core_id] -= task.uLO_core
                        core_uti_list_HI[core_id] -= task.uHI_core
                task.reset_core_list()
            #可调度
            else:
                break
    return WF_DP_mapping_list

def BF_FF_DP(ts): #WF
    task_set = ts.HI.union(ts.LO)
    WF_FF_DP_mapping_list = [list() for _ in range(node_number)] #映射列表
    core_uti_list_LO = [0 for _ in range(node_number)] #已映射任务低关键度模式利用率分布
    core_uti_list_HI = [0 for _ in range(node_number)] #已映射任务高关键度模式利用率分布
    tasks_DP = sorted(task_set, key=lambda task:task.pri, reverse = True)
    for task in tasks_DP:
        if task.cri == 0:#高关键度最差
            '''
            place_max_uti_dict = {}
            for start_row in range(0, cluster_row - task.width): #遍历所有映射情况
                for start_col in range(0, cluster_col - task.length):
                    core_max_uti = 0 #该映射情况下所有核心的最大利用率
                    #遍历该任务所有核心
                    for i in range(start_row, start_row + task.width):
                        for j in range(start_col, start_col + task.length):
                            core_id = get_core_id(i, j)
                            core_uti_LO = core_uti_list_LO[core_id] + task.uLO
                            core_uti_Hi = core_uti_list_HI[core_id] + task.uHI 
                            core_max_uti = max(core_max_uti, core_uti_LO, core_uti_Hi)
                    left_up_core_id = get_core_id(start_row, start_col)
                    place_max_uti_dict[left_up_core_id] = core_max_uti
            sorted_dict = dict(sorted(place_max_uti_dict.items(), key=lambda item: item[1]))
            last_key, _ = list(sorted_dict.items())[-1]#取最后一个键值对
            #遍历字典
            for left_up_core_id, _ in sorted_dict.items():
                start_row, start_col = get_place(left_up_core_id)
                #加入映射
                for i in range(start_row, start_row + task.width):
                    for j in range(start_col, start_col + task.length):
                        core_id = get_core_id(i, j)
                        WF_FF_DP_mapping_list[core_id].append(task.id)
                        task.core_list_add(core_id)
                        core_uti_list_LO[core_id] += task.uLO
                        core_uti_list_HI[core_id] += task.uHI
                #计算响应时间
                cal_wcrt(WF_FF_DP_mapping_list, ts, task)
                #不可调度
                if task.final_wcrt > task.dLO or task.wcrt_intertask == -1:
                    if left_up_core_id == last_key:#该任务找不到可以调度的映射位置
                        return False
                    #清除映射
                    for i in range(start_row, start_row + task.width):
                        for j in range(start_col, start_col + task.length):
                            core_id = get_core_id(i, j)
                            WF_FF_DP_mapping_list[core_id].remove(task.id)
                            core_uti_list_LO[core_id] -= task.uLO
                            core_uti_list_HI[core_id] -= task.uHI
                    task.reset_core_list()
                #可调度
                else:
                    break
            '''
            place_min_uti_dict = {}
            for start_row in range(0, cluster_row - task.width + 1): #遍历所有映射情况
                for start_col in range(0, cluster_col - task.length + 1):
                    core_min_uti = MAX #该映射情况下所有核心的最大利用率
                    #遍历该任务所有核心
                    for i in range(start_row, start_row + task.width):
                        for j in range(start_col, start_col + task.length):
                            core_id = get_core_id(i, j)
                            if task.cri == 0:
                                core_uti_LO = core_uti_list_LO[core_id] + task.uLO_core
                                core_uti_Hi = core_uti_list_HI[core_id] + task.uHI_core
                                core_min_uti = min(core_min_uti, core_uti_LO, core_uti_Hi)
                            else:
                                core_uti_LO = core_uti_list_LO[core_id]
                                core_min_uti = min(core_min_uti, core_uti_LO)
                    left_up_core_id = get_core_id(start_row, start_col)
                    place_min_uti_dict[left_up_core_id] = core_min_uti
            #字典排序
            sorted_dict = dict(sorted(place_min_uti_dict.items(), key=lambda item: item[1], reverse = True))
            last_key, _ = list(sorted_dict.items())[-1]#取最后一个键值对
            #遍历字典
            for left_up_core_id, _ in sorted_dict.items():
                start_row, start_col = get_place(left_up_core_id)
                #加入映射
                for i in range(start_row, start_row + task.width):
                    for j in range(start_col, start_col + task.length):
                        core_id = get_core_id(i, j)
                        WF_FF_DP_mapping_list[core_id].append(task.id)
                        task.core_list_add(core_id)
                        core_uti_list_LO[core_id] += task.uLO_core
                        core_uti_list_HI[core_id] += task.uHI_core
                #计算响应时间
                cal_wcrt(WF_FF_DP_mapping_list, ts, task)
                #不可调度
                if task.final_wcrt > task.dLO or task.wcrt_intertask == -1:
                    if left_up_core_id == last_key:#该任务找不到可以调度的映射位置
                        return False
                    #清除映射
                    for i in range(start_row, start_row + task.width):
                        for j in range(start_col, start_col + task.length):
                            core_id = get_core_id(i, j)
                            WF_FF_DP_mapping_list[core_id].remove(task.id)
                            core_uti_list_LO[core_id] -= task.uLO_core
                            core_uti_list_HI[core_id] -= task.uHI_core
                    task.reset_core_list()
                #可调度
                else:
                    break
        elif task.cri == 1:#低关键度首次
            schedule = 0
            for start_row in range(0, cluster_row - task.width + 1): #遍历所有映射情况
                for start_col in range(0, cluster_col - task.length + 1):
                    #加入映射
                    for i in range(start_row, start_row + task.width):
                        for j in range(start_col, start_col + task.length):
                            core_id = get_core_id(i, j)
                            WF_FF_DP_mapping_list[core_id].append(task.id)
                            task.core_list_add(core_id)
                    #计算响应时间
                    cal_wcrt(WF_FF_DP_mapping_list, ts, task)
                    #不可调度
                    if task.final_wcrt > task.dLO or task.wcrt_intertask == -1:
                        if (start_row == cluster_row - task.width) and (start_col == cluster_col - task.length):#该任务找不到可以调度的映射位置
                            return False
                        #清除映射
                        for i in range(start_row, start_row + task.width):
                            for j in range(start_col, start_col + task.length):
                                core_id = get_core_id(i, j)
                                WF_FF_DP_mapping_list[core_id].remove(task.id)
                        task.reset_core_list()
                    #可以调度
                    else:
                        schedule = 1
                        break
                if schedule == 1:
                    break

    return WF_FF_DP_mapping_list



                



                






