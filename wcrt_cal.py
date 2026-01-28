minDelta = 0
from math import *
import copy
MAX = 10000000000000000
L_R = 0.001
L_W = 0.00001
unit_time = 10
'''
#判断抢占当前任务的任务是否会被其他任务抢占
def judge_preempt(mapping_list, task_to_judge, task_current_id, ts):
        for core in task_to_judge.core_id:
                for id in mapping_list[core]:
                        if id != task_current_id:
                                task_new = ts.get_task_by_id(id)
                                if task_new.pri > task_to_judge.pri:
                                       return True
        return False
'''
#判断两个任务是否重叠
def jugde_overlap(task, task_list):
        for tasks in task_list:
                intersection_set = set(task.core_list) & set(tasks.core_list)
                if len(intersection_set) > 0:
                        return True
        return False

#判断一个任务是否可能会被抢占
def judge_preempt(mapping_list, ts):
        task_set = ts.HI.union(ts.LO)
        for task in task_set:
                for core in task.core_list:
                        for content_task_id in mapping_list[core]:
                                content_task = ts.get_task_by_id(content_task_id)
                                if content_task.pri > task.pri:
                                        task.preempt = 1
                                if content_task.pri == task.pri:
                                        print("还没有给任务集赋予优先级")
                             
               
'''
def get_real_content_task_set_hi_pri(mapping_list, ts, task_number):#废案
        task_set = ts.HI.union(ts.LO)
        content_task_list = get_content_task_set(mapping_list, task_set, len(task_set))
        with open("./test_result/content_task_list.txt", "w") as file:
                for current_task_id in range(task_number):
                        file.write(content_task_list[current_task_id] + "\n")

        #获取抢占任务中的高优先级任务
        content_task_set_HI_pri = [list() for _ in range(task_number)]
        for current_task_id in range(task_number):
                task = ts.get_task_by_id(current_task_id)
                for task_id in content_task_list[current_task_id]:
                        content_task = ts.get_task_by_id(task_id)
                        if content_task.pri > task.pri:
                                content_task_set_HI_pri[current_task_id].add(content_task.id)
        with open("./test_result/content_task_set_HI_pri.txt", "w") as file:
                for current_task_id in range(task_number):
                        file.write(content_task_set_HI_pri[current_task_id] + "\n")
        
        #将抢占任务集划分为会被抢占和不会被抢占
        content_task_list_HI_pri_preempted = [list() for _ in range(task_number)]
        content_task_list_HI_pri_not_preempted = [list() for _ in range(task_number)]
        for current_task_id in range(task_number):
                for task_id in content_task_set_HI_pri[current_task_id]:
                        task = ts.get_task_by_id(task_id)
                        if judge_preempt(mapping_list, task, current_task_id, ts):
                               content_task_list_HI_pri_preempted[current_task_id].append(task)
                        else:
                               content_task_list_HI_pri_not_preempted[current_task_id].append(task)
        with open("./test_result/content_task_list_HI_pri_preempted.txt", "w") as file:
                for current_task_id in range(task_number):
                        file.write(content_task_list_HI_pri_preempted[current_task_id] + "\n")
        with open("./test_result/content_task_list_HI_pri_not_preempted.txt", "w") as file:
                for current_task_id in range(task_number):
                        file.write(content_task_list_HI_pri_not_preempted[current_task_id] + "\n")
        
        #确定抢占任务集中不会被抢占的任务是否能够同时执行
        for current_task_id in range(task_number):
                content_task_list_HI_pri_after_concurrent_exe = [list() for _ in range(task_number)]
                content_task_IP = sorted(content_task_list_HI_pri_not_preempted[current_task_id], key=lambda task:task.pri, reverse = False)
                while(len(content_task_IP) != 0):
                        choose_list = []
                        first_task = content_task_IP[0]
                        content_task_IP.remove(first_task)
                        choose_list.append(first_task)
                        for task in content_task_IP:
                                if jugde_overlap(task, choose_list) == False:
                                        content_task_IP.remove(task)
                                        choose_list.append(task)
'''

def choose_job(job_list):
        job_list = sorted(job_list, key=lambda task:task.pri, reverse = False)
        choose_list = []
        first_task = job_list[0]
        choose_list.append(first_task)
        for job in job_list[1:]:
                if jugde_overlap(job, choose_list) == False:
                        choose_list.append(job)
        return choose_list

def get_min_exe_LO(choose_list):
        min_exe = MAX
        for job in choose_list:
                min_exe = min(min_exe, job.eLO)
        return min_exe

def get_min_exe_HI(choose_list):
        min_exe = MAX
        for job in choose_list:
                if job.cri:#LO
                        min_exe = min(min_exe, job.eLO)
                else:
                        min_exe = min(min_exe, job.eHI)
        return min_exe
def new_wcrt_1(task_set, T, tasks):#eLO和eHI，所有任务都有可能同时执行，只执行单位时间
        hp = tasks - set([T])
        hpH = tasks.intersection(task_set.HI) - set([T])
        hpL = tasks.intersection(task_set.LO) - task_set.HI - set([T])
        rLO = T.eLO
        while rLO <= T.dLO:
                current_time = 0
                job_list = []
                #初始化作业集
                for task in hp:
                        job_list.append(copy.deepcopy(task))
                while(len(job_list) != 0):#还有作业未完成
                        #作业生成
                        if current_time != 0:
                                for task in hp:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                job_list.append(copy.deepcopy(task))
                        choose_list = choose_job(job_list)#选择作业集
                        for job in choose_list:#执行单位时间
                                if job.eLO > unit_time:
                                        job.eLO -= unit_time
                                else:
                                        job_list.remove(job)      
                        current_time += unit_time
                R = current_time + T.eLO
                if R == rLO:
                    break
                if R > T.dLO:
                    return -1
                rLO = R
        if rLO > T.dLO:
                return -1
        if not T in task_set.HI:
                T.resp = rLO
                return rLO

        rHI = T.eHI
        while rHI <= T.dHI:
                current_time = 0
                job_list = []
                for task in hp:
                       job_list.append(copy.deepcopy(task))
                while len(job_list) != 0:
                        if current_time !=0:
                                for task in hpL:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                job_list.append(copy.deepcopy(task))
                                for task in hpH:
                                        if (current_time % task.pHI == 0) and current_time <= rHI:
                                                job_list.append(copy.deepcopy(task))
                        choose_list = choose_job(job_list)
                        for job in choose_list:
                                if job.cri:#LO
                                        if job.eLO > unit_time:
                                                job.eLO -=unit_time
                                        else:
                                                job_list.remove(job)
                                else:#HI
                                        if job.eHI > unit_time:
                                                job.eHI -= unit_time
                                        else:
                                                job_list.remove(job)
                        current_time += unit_time
                R = current_time + T.eHI
                if R == rHI:
                    break
                if R > T.dHI:
                    return -1
                rHI = R
        if rHI > T.dHI:
                return -1
        T.resp = max(rLO, rHI)
        return max(rLO, rHI)


def amc_rtb_pr_unit(task_set, T, tasks):#为作业同时执行加入额外条件
        hp = tasks - set([T])
        hpH = tasks.intersection(task_set.HI) - set([T])
        hpL = tasks.intersection(task_set.LO) - task_set.HI - set([T])
        rLO = T.eLO
        while rLO <= T.dLO:
                current_time = 0
                current_job = copy.deepcopy(T)#初始化当前作业
                job_list = []
                #初始化作业集
                for task in hp:
                        job_list.append(copy.deepcopy(task))
                while current_job.eLO != 0:#当前作业还未完成
                        #作业生成
                        if current_time != 0:
                                for task in hp:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                job_list.append(copy.deepcopy(task))
                        if len(job_list) != 0:
                                choose_list = choose_job_new(job_list)#选择作业集
                                for job in choose_list:#执行剩余时间
                                        if job.eLO > unit_time:
                                                job.eLO -= unit_time
                                        else:
                                                job_list.remove(job)    
                        if len(job_list) == 0:
                                if current_job.eLO >= unit_time:#当前作业执行剩余时间
                                        current_job.eLO -= unit_time
                                else:#当前作业执行完成
                                        current_time -= unit_time - current_job.eLO
                                        current_job.eLO = 0
                                        break
                        current_time += unit_time
                R = current_time
                if R == rLO:
                    break
                if R > T.dLO:
                    return -1
                rLO = R
        if rLO > T.dLO:
                return -1
        if not T in task_set.HI:
                T.resp = rLO
                return rLO

        rHI = T.eHI
        while rHI <= T.dHI:
                current_time = 0
                current_job = copy.deepcopy(T)#初始化当前作业
                job_list = []
                for task in hp:
                       job_list.append(copy.deepcopy(task))
                while current_job.eHI != 0:#当前作业未执行完
                        if current_time !=0:
                                for task in hpL:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                job_list.append(copy.deepcopy(task))
                                for task in hpH:
                                        if (current_time % task.pHI == 0) and current_time <= rHI:
                                                job_list.append(copy.deepcopy(task))      
                        if len(job_list) != 0:                       
                                choose_list = choose_job_new(job_list)
                                for job in choose_list:#执行剩余时间
                                        if job.cri:#LO
                                                if job.eLO > unit_time:
                                                        job.eLO -= unit_time
                                                else:
                                                        job_list.remove(job)
                                        else:#HI
                                                if job.eHI > unit_time:
                                                        job.eHI -= unit_time
                                                else:
                                                        job_list.remove(job)
                        if len(job_list) == 0:
                                if current_job.eHI >= unit_time:#当前作业执行剩余时间
                                        current_job.eHI -= unit_time
                                else:#当前作业执行完成
                                        current_time -= unit_time - current_job.eHI
                                        current_job.eHI = 0
                                        break
                        current_time += unit_time
                R = current_time
                if R == rHI:
                    break
                if R > T.dHI:
                    return -1
                rHI = R
        if rHI > T.dHI:
                return -1
        T.resp = max(rLO, rHI)
        return max(rLO, rHI)
                

def new_wcrt_2(task_set, T, tasks):#eLO和eHI，所有任务都有可能同时执行，执行最高优先级任务的剩余时间
        hp = tasks - set([T])
        hpH = tasks.intersection(task_set.HI) - set([T])
        hpL = tasks.intersection(task_set.LO) - task_set.HI - set([T])
        rLO = T.eLO
        while rLO <= T.dLO:
                current_time = 0
                job_list = []
                #初始化作业集
                for task in hp:
                        job_list.append(copy.deepcopy(task))
                while len(job_list) != 0:#还有作业未完成
                        #作业生成
                        if current_time != 0:
                                for task in hp:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                job_list.append(copy.deepcopy(task))
                        last_exe_time = unit_time
                        while last_exe_time >0:
                                choose_list = choose_job(job_list)#选择作业集
                                exe_time = choose_list[0].eLO
                                if exe_time >= last_exe_time:
                                        for job in choose_list:#执行剩余时间
                                                if job.eLO > last_exe_time:
                                                        job.eLO -= last_exe_time
                                                else:
                                                        job_list.remove(job)    
                                        last_exe_time = 0
                                else:
                                        for job in choose_list:#执行最高优先级任务剩余时间
                                                if job.eLO > exe_time:
                                                        job.eLO -= exe_time
                                                else:
                                                        job_list.remove(job)    
                                        last_exe_time -= exe_time
                                if len(job_list) == 0:
                                        current_time -= last_exe_time
                                        break
                        current_time += unit_time
                R = current_time + T.eLO
                if R == rLO:
                    break
                if R > T.dLO:
                    return -1
                rLO = R
        if rLO > T.dLO:
                return -1
        if not T in task_set.HI:
                T.resp = rLO
                return rLO

        rHI = T.eHI
        while rHI <= T.dHI:
                current_time = 0
                job_list = []
                for task in hp:
                       job_list.append(copy.deepcopy(task))
                while(len(job_list) != 0):
                        if current_time !=0:
                                for task in hpL:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                job_list.append(copy.deepcopy(task))
                                for task in hpH:
                                        if (current_time % task.pHI == 0) and current_time <= rHI:
                                                job_list.append(copy.deepcopy(task))
                        last_exe_time = unit_time
                        while last_exe_time > 0:                               
                                choose_list = choose_job(job_list)
                                if choose_list[0].cri:
                                        exe_time = choose_list[0].eLO
                                else:
                                        exe_time = choose_list[0].eHI
                                if exe_time >= last_exe_time:
                                        for job in choose_list:#执行剩余时间
                                                if job.cri:#LO
                                                        if job.eLO > last_exe_time:
                                                                job.eLO -= last_exe_time
                                                        else:
                                                                job_list.remove(job)
                                                else:#HI
                                                        if job.eHI > last_exe_time:
                                                                job.eHI -= last_exe_time
                                                        else:
                                                                job_list.remove(job)
                                        last_exe_time = 0
                                else:
                                        for job in choose_list:#执行最高优先级任务的剩余时间
                                                if job.cri:#LO
                                                        if job.eLO > exe_time:
                                                                job.eLO -= exe_time
                                                        else:
                                                                job_list.remove(job)
                                                else:#HI
                                                        if job.eHI > exe_time:
                                                                job.eHI -= exe_time
                                                        else:
                                                                job_list.remove(job)
                                        last_exe_time -= exe_time
                                if len(job_list) == 0:
                                        current_time -= last_exe_time
                                        break
                        current_time += unit_time
                R = current_time + T.eHI
                if R == rHI:
                    break
                if R > T.dHI:
                    return -1
                rHI = R
        if rHI > T.dHI:
                return -1
        T.resp = max(rLO, rHI)
        return max(rLO, rHI)


def new_wcrt_3(task_set, T, tasks):#eLO和eHI，所有任务都有可能同时执行，执行选择的任务中最小的剩余执行时间
        hp = tasks - set([T])
        hpH = tasks.intersection(task_set.HI) - set([T])
        hpL = tasks.intersection(task_set.LO) - task_set.HI - set([T])
        rLO = T.eLO
        while rLO <= T.dLO:
                current_time = 0
                job_list = []
                #初始化作业集
                for task in hp:
                        job_list.append(copy.deepcopy(task))
                while len(job_list) != 0:#还有作业未完成
                        #作业生成
                        if current_time != 0:
                                for task in hp:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                job_list.append(copy.deepcopy(task))
                        last_exe_time = unit_time
                        while last_exe_time >0:
                                choose_list = choose_job(job_list)#选择作业集
                                exe_time = get_min_exe_LO(choose_list)
                                if exe_time >= last_exe_time:
                                        for job in choose_list:#执行剩余时间
                                                if job.eLO > last_exe_time:
                                                        job.eLO -= last_exe_time
                                                else:
                                                        job_list.remove(job)    
                                        last_exe_time = 0
                                else:
                                        for job in choose_list:#执行最高优先级任务剩余时间
                                                if job.eLO > exe_time:
                                                        job.eLO -= exe_time
                                                else:
                                                        job_list.remove(job)    
                                        last_exe_time -= exe_time
                                if len(job_list) == 0:
                                        current_time -= last_exe_time
                                        break
                        current_time += unit_time
                R = current_time + T.eLO
                if R == rLO:
                    break
                if R > T.dLO:
                    return -1
                rLO = R
        if rLO > T.dLO:
                return -1
        if not T in task_set.HI:
                T.resp = rLO
                return rLO

        rHI = T.eHI
        while rHI <= T.dHI:
                current_time = 0
                job_list = []
                for task in hp:
                       job_list.append(copy.deepcopy(task))
                while(len(job_list) != 0):
                        if current_time !=0:
                                for task in hpL:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                job_list.append(copy.deepcopy(task))
                                for task in hpH:
                                        if (current_time % task.pHI == 0) and current_time <= rHI:
                                                job_list.append(copy.deepcopy(task))
                        last_exe_time = unit_time
                        while last_exe_time > 0:                               
                                choose_list = choose_job(job_list)
                                exe_time = get_min_exe_HI(choose_list)
                                if exe_time >= last_exe_time:
                                        for job in choose_list:#执行剩余时间
                                                if job.cri:#LO
                                                        if job.eLO > last_exe_time:
                                                                job.eLO -= last_exe_time
                                                        else:
                                                                job_list.remove(job)
                                                else:#HI
                                                        if job.eHI > last_exe_time:
                                                                job.eHI -= last_exe_time
                                                        else:
                                                                job_list.remove(job)
                                        last_exe_time = 0
                                else:
                                        for job in choose_list:#执行最高优先级任务的剩余时间
                                                if job.cri:#LO
                                                        if job.eLO > exe_time:
                                                                job.eLO -= exe_time
                                                        else:
                                                                job_list.remove(job)
                                                else:#HI
                                                        if job.eHI > exe_time:
                                                                job.eHI -= exe_time
                                                        else:
                                                                job_list.remove(job)
                                        last_exe_time -= exe_time
                                if len(job_list) == 0:
                                        current_time -= last_exe_time
                                        break
                        current_time += unit_time
                R = current_time + T.eHI
                if R == rHI:
                    break
                if R > T.dHI:
                    return -1
                rHI = R
        if rHI > T.dHI:
                return -1
        T.resp = max(rLO, rHI)
        return max(rLO, rHI)

def choose_job_original(job_list):
        job_list = sorted(job_list, key=lambda task:task.pri, reverse = False)
        choose_list = []
        first_task = job_list[0]
        choose_list.append(first_task)
        return choose_list

def new_wcrt_4_original(task_set, T, tasks):#修改循环终止条件：从作业集为空变为当前作业执行完成
        hp = tasks - set([T])
        hpH = tasks.intersection(task_set.HI) - set([T])
        hpL = tasks.intersection(task_set.LO) - task_set.HI - set([T])
        rLO = T.eLO
        while rLO <= T.dLO:
                current_time = 0
                current_job = copy.deepcopy(T)#初始化当前作业
                job_list = []
                #初始化作业集
                for task in hp:
                        job_list.append(copy.deepcopy(task))
                while current_job.eLO != 0:#当前作业还未完成
                        #作业生成
                        if current_time != 0:
                                for task in hp:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                job_list.append(copy.deepcopy(task))
                        last_exe_time = unit_time
                        while last_exe_time > 0:
                                if len(job_list) != 0:
                                        choose_list = choose_job_original(job_list)#选择作业集
                                        exe_time = get_min_exe_LO(choose_list)
                                        if exe_time >= last_exe_time:
                                                for job in choose_list:#执行剩余时间
                                                        if job.eLO > last_exe_time:
                                                                job.eLO -= last_exe_time
                                                        else:
                                                                job_list.remove(job)    
                                                last_exe_time = 0
                                        else:
                                                for job in choose_list:#执行最高优先级任务剩余时间
                                                        if job.eLO > exe_time:
                                                                job.eLO -= exe_time
                                                        else:
                                                                job_list.remove(job)    
                                                last_exe_time -= exe_time
                                if len(job_list) == 0:
                                        if current_job.eLO >= last_exe_time:#当前作业执行剩余时间
                                                current_job.eLO -= last_exe_time
                                                last_exe_time = 0
                                        else:#当前作业执行完成
                                                last_exe_time -= current_job.eLO
                                                current_job.eLO = 0
                                                current_time -= last_exe_time
                                                break
                        current_time += unit_time
                R = current_time
                if R == rLO:
                    break
                if R > T.dLO:
                    return -1
                rLO = R
        if rLO > T.dLO:
                return -1
        if not T in task_set.HI:
                T.resp = rLO
                return rLO

        rHI = T.eHI
        while rHI <= T.dHI:
                current_time = 0
                current_job = copy.deepcopy(T)#初始化当前作业
                job_list = []
                for task in hp:
                       job_list.append(copy.deepcopy(task))
                while current_job.eHI > 0:#当前作业未执行完
                        if current_time !=0:
                                for task in hpL:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                job_list.append(copy.deepcopy(task))
                                for task in hpH:
                                        if (current_time % task.pHI == 0) and current_time <= rHI:
                                                job_list.append(copy.deepcopy(task))
                        last_exe_time = unit_time
                        while last_exe_time > 0:
                                if len(job_list) != 0:                               
                                        choose_list = choose_job_original(job_list)
                                        exe_time = get_min_exe_HI(choose_list)
                                        if exe_time >= last_exe_time:
                                                for job in choose_list:#执行剩余时间
                                                        if job.cri:#LO
                                                                if job.eLO > last_exe_time:
                                                                        job.eLO -= last_exe_time
                                                                else:
                                                                        job_list.remove(job)
                                                        else:#HI
                                                                if job.eHI > last_exe_time:
                                                                        job.eHI -= last_exe_time
                                                                else:
                                                                        job_list.remove(job)
                                                last_exe_time = 0
                                        else:
                                                for job in choose_list:#执行最高优先级任务的剩余时间
                                                        if job.cri:#LO
                                                                if job.eLO > exe_time:
                                                                        job.eLO -= exe_time
                                                                else:
                                                                        job_list.remove(job)
                                                        else:#HI
                                                                if job.eHI > exe_time:
                                                                        job.eHI -= exe_time
                                                                else:
                                                                        job_list.remove(job)
                                                last_exe_time -= exe_time
                                if len(job_list) == 0:
                                        if current_job.eHI >= last_exe_time:#当前作业执行剩余时间
                                                current_job.eHI -= last_exe_time
                                                last_exe_time = 0
                                        else:#当前作业执行完成
                                                last_exe_time -= current_job.eHI
                                                current_job.eHI = 0
                                                current_time -= last_exe_time
                                                break
                        current_time += unit_time
                R = current_time
                if R == rHI:
                    break
                if R > T.dHI:
                    return -1
                rHI = R
        if rHI > T.dHI:
                return -1
        T.resp = max(rLO, rHI)
        return max(rLO, rHI)


def new_wcrt_4(task_set, T, tasks):#修改循环终止条件：从作业集为空变为当前作业执行完成
        hp = tasks - set([T])
        hpH = tasks.intersection(task_set.HI) - set([T])
        hpL = tasks.intersection(task_set.LO) - task_set.HI - set([T])
        rLO = T.eLO
        while rLO <= T.dLO:
                current_time = 0
                current_job = copy.deepcopy(T)#初始化当前作业
                job_list = []
                #初始化作业集
                for task in hp:
                        job_list.append(copy.deepcopy(task))
                while current_job.eLO != 0:#当前作业还未完成
                        #作业生成
                        if current_time != 0:
                                for task in hp:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                job_list.append(copy.deepcopy(task))
                        last_exe_time = unit_time
                        while last_exe_time > 0:
                                if len(job_list) != 0:
                                        choose_list = choose_job(job_list)#选择作业集
                                        exe_time = get_min_exe_LO(choose_list)
                                        if exe_time >= last_exe_time:
                                                for job in choose_list:#执行剩余时间
                                                        if job.eLO > last_exe_time:
                                                                job.eLO -= last_exe_time
                                                        else:
                                                                job_list.remove(job)    
                                                last_exe_time = 0
                                        else:
                                                for job in choose_list:#执行最高优先级任务剩余时间
                                                        if job.eLO > exe_time:
                                                                job.eLO -= exe_time
                                                        else:
                                                                job_list.remove(job)    
                                                last_exe_time -= exe_time
                                if len(job_list) == 0:
                                        if current_job.eLO >= last_exe_time:#当前作业执行剩余时间
                                                current_job.eLO -= last_exe_time
                                                last_exe_time = 0
                                        else:#当前作业执行完成
                                                last_exe_time -= current_job.eLO
                                                current_job.eLO = 0
                                                current_time -= last_exe_time
                                                break
                        current_time += unit_time
                R = current_time
                if R == rLO:
                    break
                if R > T.dLO:
                    return -1
                rLO = R
        if rLO > T.dLO:
                return -1
        if not T in task_set.HI:
                T.resp = rLO
                return rLO

        rHI = T.eHI
        while rHI <= T.dHI:
                current_time = 0
                current_job = copy.deepcopy(T)#初始化当前作业
                job_list = []
                for task in hp:
                       job_list.append(copy.deepcopy(task))
                while current_job.eHI > 0:#当前作业未执行完
                        if current_time !=0:
                                for task in hpL:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                job_list.append(copy.deepcopy(task))
                                for task in hpH:
                                        if (current_time % task.pHI == 0) and current_time <= rHI:
                                                job_list.append(copy.deepcopy(task))
                        last_exe_time = unit_time
                        while last_exe_time > 0:
                                if len(job_list) != 0:                               
                                        choose_list = choose_job(job_list)
                                        exe_time = get_min_exe_HI(choose_list)
                                        if exe_time >= last_exe_time:
                                                for job in choose_list:#执行剩余时间
                                                        if job.cri:#LO
                                                                if job.eLO > last_exe_time:
                                                                        job.eLO -= last_exe_time
                                                                else:
                                                                        job_list.remove(job)
                                                        else:#HI
                                                                if job.eHI > last_exe_time:
                                                                        job.eHI -= last_exe_time
                                                                else:
                                                                        job_list.remove(job)
                                                last_exe_time = 0
                                        else:
                                                for job in choose_list:#执行最高优先级任务的剩余时间
                                                        if job.cri:#LO
                                                                if job.eLO > exe_time:
                                                                        job.eLO -= exe_time
                                                                else:
                                                                        job_list.remove(job)
                                                        else:#HI
                                                                if job.eHI > exe_time:
                                                                        job.eHI -= exe_time
                                                                else:
                                                                        job_list.remove(job)
                                                last_exe_time -= exe_time
                                if len(job_list) == 0:
                                        if current_job.eHI >= last_exe_time:#当前作业执行剩余时间
                                                current_job.eHI -= last_exe_time
                                                last_exe_time = 0
                                        else:#当前作业执行完成
                                                last_exe_time -= current_job.eHI
                                                current_job.eHI = 0
                                                current_time -= last_exe_time
                                                break
                        current_time += unit_time
                R = current_time
                if R == rHI:
                    break
                if R > T.dHI:
                    return -1
                rHI = R
        if rHI > T.dHI:
                return -1
        T.resp = max(rLO, rHI)
        return max(rLO, rHI)

def choose_job_new(job_list):
        job_list = sorted(job_list, key=lambda task:task.pri, reverse = False)
        choose_list = []
        first_job = job_list[0]
        choose_list.append(first_job)
        if first_job.preempt == 1:
               return choose_list
        else:
                for job in job_list[1:]:
                        if job.preempt == 1:
                                continue
                        else:
                                if jugde_overlap(job, choose_list) == False:
                                        choose_list.append(job)
        return choose_list

def new_wcrt_5(task_set, T, tasks):#为作业同时执行加入额外条件
        hp = tasks - set([T])
        hpH = tasks.intersection(task_set.HI) - set([T])
        hpL = tasks.intersection(task_set.LO) - task_set.HI - set([T])
        rLO = T.eLO
        while rLO <= T.dLO:
                current_time = 0
                current_job = copy.deepcopy(T)#初始化当前作业
                job_list = []
                #初始化作业集
                for task in hp:
                        job_list.append(copy.deepcopy(task))
                while current_job.eLO != 0:#当前作业还未完成
                        #作业生成
                        if current_time != 0:
                                for task in hp:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                job_list.append(copy.deepcopy(task))
                        last_exe_time = unit_time
                        while last_exe_time > 0:
                                if len(job_list) != 0:
                                        choose_list = choose_job_new(job_list)#选择作业集
                                        exe_time = get_min_exe_LO(choose_list)
                                        if exe_time >= last_exe_time:
                                                for job in choose_list:#执行剩余时间
                                                        if job.eLO > last_exe_time:
                                                                job.eLO -= last_exe_time
                                                        else:
                                                                job_list.remove(job)    
                                                last_exe_time = 0
                                        else:
                                                for job in choose_list:#执行最高优先级任务剩余时间
                                                        if job.eLO > exe_time:
                                                                job.eLO -= exe_time
                                                        else:
                                                                job_list.remove(job)    
                                                last_exe_time -= exe_time
                                if len(job_list) == 0:
                                        if current_job.eLO >= last_exe_time:#当前作业执行剩余时间
                                                current_job.eLO -= last_exe_time
                                                last_exe_time = 0
                                        else:#当前作业执行完成
                                                last_exe_time -= current_job.eLO
                                                current_job.eLO = 0
                                                current_time -= last_exe_time
                                                break
                        current_time += unit_time
                R = current_time
                if R == rLO:
                    break
                if R > T.dLO:
                    return -1
                rLO = R
        if rLO > T.dLO:
                return -1
        if not T in task_set.HI:
                T.resp = rLO
                return rLO

        rHI = T.eHI
        while rHI <= T.dHI:
                current_time = 0
                current_job = copy.deepcopy(T)#初始化当前作业
                job_list = []
                for task in hp:
                       job_list.append(copy.deepcopy(task))
                while current_job.eHI != 0:#当前作业未执行完
                        if current_time !=0:
                                for task in hpL:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                job_list.append(copy.deepcopy(task))
                                for task in hpH:
                                        if (current_time % task.pHI == 0) and current_time <= rHI:
                                                job_list.append(copy.deepcopy(task))
                        last_exe_time = unit_time
                        while last_exe_time > 0:        
                                if len(job_list) != 0:                       
                                        choose_list = choose_job_new(job_list)
                                        exe_time = get_min_exe_HI(choose_list)
                                        if exe_time >= last_exe_time:
                                                for job in choose_list:#执行剩余时间
                                                        if job.cri:#LO
                                                                if job.eLO > last_exe_time:
                                                                        job.eLO -= last_exe_time
                                                                else:
                                                                        job_list.remove(job)
                                                        else:#HI
                                                                if job.eHI > last_exe_time:
                                                                        job.eHI -= last_exe_time
                                                                else:
                                                                        job_list.remove(job)
                                                last_exe_time = 0
                                        else:
                                                for job in choose_list:#执行最高优先级任务的剩余时间
                                                        if job.cri:#LO
                                                                if job.eLO > exe_time:
                                                                        job.eLO -= exe_time
                                                                else:
                                                                        job_list.remove(job)
                                                        else:#HI
                                                                if job.eHI > exe_time:
                                                                        job.eHI -= exe_time
                                                                else:
                                                                        job_list.remove(job)
                                                last_exe_time -= exe_time
                                if len(job_list) == 0:
                                        if current_job.eHI >= last_exe_time:#当前作业执行剩余时间
                                                current_job.eHI -= last_exe_time
                                                last_exe_time = 0
                                        else:#当前作业执行完成
                                                last_exe_time -= current_job.eHI
                                                current_job.eHI = 0
                                                current_time -= last_exe_time
                                                break
                        current_time += unit_time
                R = current_time
                if R == rHI:
                    break
                if R > T.dHI:
                    return -1
                rHI = R
        if rHI > T.dHI:
                return -1
        T.resp = max(rLO, rHI)
        return max(rLO, rHI)
        
def amc_rtb_pr(task_set, T, tasks):#rLO后移除低关键度任务
        hp = tasks - set([T])
        hpH = tasks.intersection(task_set.HI) - set([T])
        hpL = tasks.intersection(task_set.LO) - task_set.HI - set([T])
        rLO = T.eLO
        while rLO <= T.dLO:
                current_time = 0
                current_job = copy.deepcopy(T)#初始化当前作业
                job_list = []
                #初始化作业集
                for task in hp:
                        job_list.append(copy.deepcopy(task))
                while current_job.eLO != 0:#当前作业还未完成
                        #作业生成
                        if current_time != 0:
                                for task in hp:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                job_list.append(copy.deepcopy(task))
                        
                        if current_time >= rLO:
                                for job in job_list:
                                        if job.cri:
                                                job_list.remove(job)

                        last_exe_time = unit_time
                        while last_exe_time > 0:
                                if len(job_list) != 0:
                                        choose_list = choose_job_new(job_list)#选择作业集
                                        exe_time = get_min_exe_LO(choose_list)
                                        if exe_time >= last_exe_time:
                                                for job in choose_list:#执行剩余时间
                                                        if job.eLO > last_exe_time:
                                                                job.eLO -= last_exe_time
                                                        else:
                                                                job_list.remove(job)    
                                                last_exe_time = 0
                                        else:
                                                for job in choose_list:#执行最高优先级任务剩余时间
                                                        if job.eLO > exe_time:
                                                                job.eLO -= exe_time
                                                        else:
                                                                job_list.remove(job)    
                                                last_exe_time -= exe_time
                                if len(job_list) == 0:
                                        if current_job.eLO >= last_exe_time:#当前作业执行剩余时间
                                                current_job.eLO -= last_exe_time
                                                last_exe_time = 0
                                        else:#当前作业执行完成
                                                last_exe_time -= current_job.eLO
                                                current_job.eLO = 0
                                                current_time -= last_exe_time
                                                break
                        current_time += unit_time
                R = current_time
                if R == rLO:
                    break
                if R > T.dLO:
                    return -1
                rLO = R
        if rLO > T.dLO:
                return -1
        if not T in task_set.HI:
                T.resp = rLO
                return rLO

        rHI = T.eHI
        while rHI <= T.dHI:
                current_time = 0
                current_job = copy.deepcopy(T)#初始化当前作业
                job_list = []
                for task in hp:
                       job_list.append(copy.deepcopy(task))
                while current_job.eHI != 0:#当前作业未执行完
                        if current_time !=0:
                                for task in hpL:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                job_list.append(copy.deepcopy(task))
                                for task in hpH:
                                        if (current_time % task.pHI == 0) and current_time <= rHI:
                                                job_list.append(copy.deepcopy(task))
                        last_exe_time = unit_time
                        while last_exe_time > 0:
                                if len(job_list) != 0:                               
                                        choose_list = choose_job_new(job_list)
                                        exe_time = get_min_exe_HI(choose_list)
                                        if exe_time >= last_exe_time:
                                                for job in choose_list:#执行剩余时间
                                                        if job.cri:#LO
                                                                if job.eLO > last_exe_time:
                                                                        job.eLO -= last_exe_time
                                                                else:
                                                                        job_list.remove(job)
                                                        else:#HI
                                                                if job.eHI > last_exe_time:
                                                                        job.eHI -= last_exe_time
                                                                else:
                                                                        job_list.remove(job)
                                                last_exe_time = 0
                                        else:
                                                for job in choose_list:#执行最高优先级任务的剩余时间
                                                        if job.cri:#LO
                                                                if job.eLO > exe_time:
                                                                        job.eLO -= exe_time
                                                                else:
                                                                        job_list.remove(job)
                                                        else:#HI
                                                                if job.eHI > exe_time:
                                                                        job.eHI -= exe_time
                                                                else:
                                                                        job_list.remove(job)
                                                last_exe_time -= exe_time
                                if len(job_list) == 0:
                                        if current_job.eHI >= last_exe_time:#当前作业执行剩余时间
                                                current_job.eHI -= last_exe_time
                                                last_exe_time = 0
                                        else:#当前作业执行完成
                                                last_exe_time -= current_job.eHI
                                                current_job.eHI = 0
                                                current_time -= last_exe_time
                                                break
                        current_time += unit_time
                R = current_time
                if R == rHI:
                    break
                if R > T.dHI:
                    return -1
                rHI = R
        if rHI > T.dHI:
                return -1
        T.resp = max(rLO, rHI)
        return max(rLO, rHI)                         
                             

def get_place(core_id):
    if core_id % cluster_row == 0:
        row = floor(core_id / cluster_row)
    else:
        row = core_id // cluster_row
    col = core_id % cluster_row
    return row, col

def get_content_task_set(mapping_list, task_set, task_number):
    content_task_set = [list() for _ in range(task_number)]
    for task in task_set:
        for core in task.core_list:
            for id in mapping_list[core]:
                if id not in content_task_set[task.id]:
                    content_task_set[task.id].append(id)
    return content_task_set

def amc_rtb_wcrt(task_set, T, tasks):
        hp = tasks - set([T])
        hpH = tasks.intersection(task_set.HI) - set([T])
        hpL = tasks.intersection(task_set.LO) - task_set.HI - set([T])

        rLO = T.eLO + sum([Tp.eLO for Tp in hp])
        while rLO <= T.dLO:
                R = T.eLO + sum([ceil(float(rLO) / Tp.pLO) * Tp.eLO for Tp in hp])
                if R == rLO:
                    break
                if R > T.dLO:
                    return -1
                rLO = R
        if rLO > T.dLO:
                return -1
        if not T in task_set.HI:
                T.resp = rLO
                return rLO

        rHI = T.eHI + sum([Tp.eHI for Tp in hpH]) + sum([Tp.eLO for Tp in hpL])
        while rHI <= T.dHI:
                R = (T.eHI + sum([ceil(float(rHI) / Tp.pHI) * Tp.eHI for Tp in hpH]) + sum([ceil(float(rLO) / Tp.pLO) * Tp.eLO for Tp in hpL]))
                if R == rHI:
                    break
                if R > T.dHI:
                    return -1
                rHI = R
        if rHI > T.dHI:
                return -1
        T.resp = max(rLO, rHI)
        return max(rLO, rHI)

def amc_rtb_wcrt_new(task_set, T, tasks):
        hp = tasks - set([T])
        hpH = tasks.intersection(task_set.HI) - set([T])
        hpL = tasks.intersection(task_set.LO) - task_set.HI - set([T])

        rLO = T.eLO_new + sum([Tp.eLO_new for Tp in hp])
        while rLO <= T.dLO:
                R = T.eLO_new + sum([ceil(float(rLO) / Tp.pLO) * Tp.eLO_new for Tp in hp])
                if R == rLO:
                    break
                if R > T.dLO:
                    return -1
                rLO = R
        if rLO > T.dLO:
                return -1
        if not T in task_set.HI:
                T.resp = rLO
                return rLO

        rHI = T.eHI_new + sum([Tp.eHI_new for Tp in hpH]) + sum([Tp.eLO_new for Tp in hpL])
        while rHI <= T.dHI:
                R = (T.eHI_new + sum([ceil(float(rHI) / Tp.pHI) * Tp.eHI_new for Tp in hpH]) + sum([ceil(float(rLO) / Tp.pLO) * Tp.eLO_new for Tp in hpL]))
                if R == rHI:
                    break
                if R > T.dHI:
                    return -1
                rHI = R
        if rHI > T.dHI:
                return -1
        T.resp = max(rLO, rHI)
        return max(rLO, rHI)

def get_io_dis(task):
        up_left_core = task.core_list[0]
        #down_right_core = up_left_core + cluster_row * (task.length - 1) + (task.width - 1)
        down_right_core = task.core_list[-1]
        up_dis, left_dis = get_place(up_left_core)
        down, right = get_place(down_right_core)
        down_dis = cluster_col - down - 1
        right_dis = cluster_row - right - 1
        dis_list = [up_dis, left_dis, down_dis, right_dis]
        min_dis = min(dis_list)
        task.io_dis = min_dis

def cal_io_delay(task):
        max_io = max(task.io_list)
        io_delay = max_io * ((task.io_dis + 1) * L_R + task.io_dis * L_W)
        task.io_delay = io_delay

def get_e_new(task):
        task.eLO_new = task.eLO + task.io_delay + task.switch_delay
        task.eHI_new = task.eHI + task.io_delay + task.switch_delay

def cal_wcrt(mapping_list, ts, task, wcrt_algor = amc_rtb_wcrt):
        #get_io_dis(task)
        #cal_io_delay(task)
        #get_e_new(task)
        task_set = ts.HI.union(ts.LO)
        content_task_list = get_content_task_set(mapping_list, task_set, len(task_set))
        content_task_set_HI_pri = set()
        for id in content_task_list[task.id]:
                content_task = ts.get_task_by_id(id)
                if content_task.pri > task.pri:
                        content_task_set_HI_pri.add(content_task)
        #wcrt = amc_rtb_pts_wcrt_btTask_sch(ts, task, content_task_set_HI_pri)
        wcrt = wcrt_algor(ts, task, content_task_set_HI_pri)
        task.wcrt_intertask = wcrt
        task.final_wcrt = wcrt

        