minDelta = 0
from math import *
import copy
MAX = 10000000000000000
L_R = 0.001
L_W = 0.00001
unit_time = 10
node_number = 4
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
#判断一个任务是否可能会被抢占
def judge_preempt(mapping_list, ts):
        """兼容历史接口：单核映射下不再维护并行抢占标记。"""
        return
                             
               
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
        return [sorted(job_list, key=lambda task: task.pri, reverse=False)[0]]

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


def choose_job_new(job_list):
        """
        单核映射下，每个时刻仅执行一个作业：
        直接返回当前可运行作业中优先级最高的作业。
        """
        return [sorted(job_list, key=lambda task: task.pri, reverse=False)[0]]

def _mark_job_release(job, release_time):
        """为作业实例补充释放时刻和DAG前置约束信息。"""
        job.release_time = release_time
        job.predecessors = set(getattr(job, 'predecessors', set()))
        return job

def _dag_job_runnable(job, current_time, completed_jobs):
        """DAG约束：前置任务未完成时，当前任务不能执行。"""
        return job.release_time <= current_time and job.predecessors.issubset(completed_jobs)

def _get_runnable_jobs(job_list, current_time, completed_jobs):
        return [job for job in job_list if _dag_job_runnable(job, current_time, completed_jobs)]

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

        rLO = T.eLO
        while rLO <= T.dLO:
                current_time = 0
                current_job = _mark_job_release(copy.deepcopy(T), 0)
                current_job.predecessors = set()
                job_list = [_mark_job_release(copy.deepcopy(task), 0) for task in hp]
                for job in job_list:
                        job.predecessors = set()
                completed_jobs = set()

                while current_job.eLO != 0:
                        if current_time != 0:
                                for task in hp:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                new_job = _mark_job_release(copy.deepcopy(task), current_time)
                                                new_job.predecessors = set()
                                                job_list.append(new_job)

                        if current_time > T.dLO + unit_time:
                                return -1

                        last_exe_time = unit_time
                        while last_exe_time > 0:
                                runnable_jobs = _get_runnable_jobs(job_list, current_time, completed_jobs)
                                if len(runnable_jobs) != 0:
                                        choose_list = choose_job_new(runnable_jobs)
                                        exe_time = get_min_exe_LO(choose_list)
                                        if exe_time >= last_exe_time:
                                                for job in choose_list:
                                                        if job.eLO > last_exe_time:
                                                                job.eLO -= last_exe_time
                                                        else:
                                                                completed_jobs.add(job.id)
                                                                job_list.remove(job)
                                                last_exe_time = 0
                                        else:
                                                for job in choose_list:
                                                        if job.eLO > exe_time:
                                                                job.eLO -= exe_time
                                                        else:
                                                                completed_jobs.add(job.id)
                                                                job_list.remove(job)
                                                last_exe_time -= exe_time

                                if len(_get_runnable_jobs(job_list, current_time, completed_jobs)) == 0:
                                        if _dag_job_runnable(current_job, current_time, completed_jobs):
                                                if current_job.eLO >= last_exe_time:
                                                        current_job.eLO -= last_exe_time
                                                        last_exe_time = 0
                                                else:
                                                        last_exe_time -= current_job.eLO
                                                        current_job.eLO = 0
                                                        current_time -= last_exe_time
                                                        break
                                        else:
                                                last_exe_time = 0
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
                current_job = _mark_job_release(copy.deepcopy(T), 0)
                current_job.predecessors = set()
                job_list = [_mark_job_release(copy.deepcopy(task), 0) for task in hp]
                for job in job_list:
                        job.predecessors = set()
                completed_jobs = set()
                while current_job.eHI != 0:
                        if current_time !=0:
                                for task in hpL:
                                        if (current_time % task.pLO == 0) and current_time <= rLO:
                                                new_job = _mark_job_release(copy.deepcopy(task), current_time)
                                                new_job.predecessors = set()
                                                job_list.append(new_job)
                                for task in hpH:
                                        if (current_time % task.pHI == 0) and current_time <= rHI:
                                                new_job = _mark_job_release(copy.deepcopy(task), current_time)
                                                new_job.predecessors = set()
                                                job_list.append(new_job)
                        if current_time > T.dHI + unit_time:
                                return -1

                        last_exe_time = unit_time
                        while last_exe_time > 0:
                                runnable_jobs = _get_runnable_jobs(job_list, current_time, completed_jobs)
                                if len(runnable_jobs) != 0:
                                        choose_list = choose_job_new(runnable_jobs)
                                        exe_time = get_min_exe_HI(choose_list)
                                        if exe_time >= last_exe_time:
                                                for job in choose_list:
                                                        if job.cri:
                                                                if job.eLO > last_exe_time:
                                                                        job.eLO -= last_exe_time
                                                                else:
                                                                        completed_jobs.add(job.id)
                                                                        job_list.remove(job)
                                                        else:
                                                                if job.eHI > last_exe_time:
                                                                        job.eHI -= last_exe_time
                                                                else:
                                                                        completed_jobs.add(job.id)
                                                                        job_list.remove(job)
                                                last_exe_time = 0
                                        else:
                                                for job in choose_list:
                                                        if job.cri:
                                                                if job.eLO > exe_time:
                                                                        job.eLO -= exe_time
                                                                else:
                                                                        completed_jobs.add(job.id)
                                                                        job_list.remove(job)
                                                        else:
                                                                if job.eHI > exe_time:
                                                                        job.eHI -= exe_time
                                                                else:
                                                                        completed_jobs.add(job.id)
                                                                        job_list.remove(job)
                                                last_exe_time -= exe_time
                                if len(_get_runnable_jobs(job_list, current_time, completed_jobs)) == 0:
                                        if _dag_job_runnable(current_job, current_time, completed_jobs):
                                                if current_job.eHI >= last_exe_time:
                                                        current_job.eHI -= last_exe_time
                                                        last_exe_time = 0
                                                else:
                                                        last_exe_time -= current_job.eHI
                                                        current_job.eHI = 0
                                                        current_time -= last_exe_time
                                                        break
                                        else:
                                                last_exe_time = 0
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
        # 线性核心拓扑：I/O 距离定义为到两侧边界的最小跳数
        if not task.core_list:
                task.io_dis = 0
                return
        left = min(task.core_list)
        right = max(task.core_list)
        task.io_dis = min(left, node_number - 1 - right)

def cal_io_delay(task):
        max_io = max(task.io_list)
        io_delay = max_io * ((task.io_dis + 1) * L_R + task.io_dis * L_W)
        task.io_delay = io_delay

def get_e_new(task):
        task.eLO_new = task.eLO + task.io_delay + task.switch_delay
        task.eHI_new = task.eHI + task.io_delay + task.switch_delay

def _get_mapped_task_ids(mapping_list):
        mapped_ids = set()
        for core_tasks in mapping_list:
                mapped_ids.update(core_tasks)
        return mapped_ids


def _calc_task_local_wcrt(mapping_list, ts, task, wcrt_algor=amc_rtb_wcrt):
        """
        计算任务在其映射核上的局部WCRT（仅考虑共享核心的高优先级干扰）。
        """
        task_set = ts.HI.union(ts.LO)
        content_task_list = get_content_task_set(mapping_list, task_set, len(task_set))
        content_task_set_HI_pri = set()
        for task_id in content_task_list[task.id]:
                content_task = ts.get_task_by_id(task_id)
                if content_task.pri > task.pri:
                        content_task_set_HI_pri.add(content_task)
        return wcrt_algor(ts, task, content_task_set_HI_pri)


def _calc_dag_finish_time(task, dag_task_dict, local_wcrt_map, memo):
        """
        忽略通信开销下的DAG端到端完成时间：
        finish(v) = local_wcrt(v) + max(finish(pred(v))).
        """
        if task.id in memo:
                return memo[task.id]
        pred_finish = 0
        for pred_id in task.predecessors:
                pred_task = dag_task_dict.get(pred_id)
                if pred_task is None:
                        continue
                pred_finish = max(pred_finish, _calc_dag_finish_time(pred_task, dag_task_dict, local_wcrt_map, memo))
        finish = local_wcrt_map[task.id] + pred_finish
        memo[task.id] = finish
        return finish


def _topo_order_mapped_dag(dag_tasks):
        """返回已映射 DAG 节点的拓扑序（若图非法则返回空列表）。"""
        task_by_id = {task.id: task for task in dag_tasks}
        indegree = {task.id: 0 for task in dag_tasks}
        for task in dag_tasks:
                for pred_id in task.predecessors:
                        if pred_id in task_by_id:
                                indegree[task.id] += 1

        queue = [task_id for task_id, deg in indegree.items() if deg == 0]
        order = []
        while queue:
                current = queue.pop(0)
                order.append(current)
                for succ_id in task_by_id[current].successors:
                        if succ_id not in indegree:
                                continue
                        indegree[succ_id] -= 1
                        if indegree[succ_id] == 0:
                                queue.append(succ_id)
        if len(order) != len(dag_tasks):
                return []
        return order


def analyze_dag_partitioned_fp(mapping_list, ts, dag_id, wcrt_algor=amc_rtb_wcrt):
        """
        Partitioned 固定优先级 + 两层分析：
        层1（核内）：每个节点在其映射核上做 AMC-RTB 局部 WCRT。
        层2（DAG 全局）：按前驱关系做全局 RTA 聚合。

        当前版本忽略通信开销，DAG 截止期口径为：每个 sink 节点满足 finish<=sink.dLO。
        """
        task_set = ts.HI.union(ts.LO)
        mapped_ids = _get_mapped_task_ids(mapping_list)
        dag_tasks = [task for task in task_set if task.dag_id == dag_id and task.id in mapped_ids]
        if not dag_tasks:
                return {
                        'schedulable': True,
                        'dag_tasks': [],
                        'local_wcrt_map': {},
                        'finish_map': {},
                        'sink_ids': [],
                }

        local_wcrt_map = {}
        for task in dag_tasks:
                wcrt = _calc_task_local_wcrt(mapping_list, ts, task, wcrt_algor)
                local_wcrt_map[task.id] = wcrt
                task.wcrt_intertask = wcrt
                if wcrt == -1:
                        task.final_wcrt = -1
                        return {
                                'schedulable': False,
                                'dag_tasks': dag_tasks,
                                'local_wcrt_map': local_wcrt_map,
                                'finish_map': {},
                                'sink_ids': [],
                        }

        order = _topo_order_mapped_dag(dag_tasks)
        if not order:
                return {
                        'schedulable': False,
                        'dag_tasks': dag_tasks,
                        'local_wcrt_map': local_wcrt_map,
                        'finish_map': {},
                        'sink_ids': [],
                }

        task_by_id = {task.id: task for task in dag_tasks}
        finish_map = {}
        for task_id in order:
                task = task_by_id[task_id]
                pred_finish = 0
                for pred_id in task.predecessors:
                        if pred_id in finish_map:
                                pred_finish = max(pred_finish, finish_map[pred_id])
                finish_map[task_id] = local_wcrt_map[task_id] + pred_finish
                task.final_wcrt = finish_map[task_id]

        mapped_id_set = set(task_by_id.keys())
        sink_ids = [
                task.id for task in dag_tasks
                if len(set(task.successors).intersection(mapped_id_set)) == 0
        ]
        for sink_id in sink_ids:
                sink = task_by_id[sink_id]
                if finish_map[sink_id] > sink.dLO:
                        return {
                                'schedulable': False,
                                'dag_tasks': dag_tasks,
                                'local_wcrt_map': local_wcrt_map,
                                'finish_map': finish_map,
                                'sink_ids': sink_ids,
                        }

        return {
                'schedulable': True,
                'dag_tasks': dag_tasks,
                'local_wcrt_map': local_wcrt_map,
                'finish_map': finish_map,
                'sink_ids': sink_ids,
        }


def cal_wcrt(mapping_list, ts, task, wcrt_algor = amc_rtb_wcrt):
        """
        多核DAG场景（暂不计通信开销）：
        1) 先计算目标DAG内已映射任务的局部WCRT；
        2) 再按前驱关系聚合得到目标任务的端到端完成时间上界。
        """
        mapped_ids = _get_mapped_task_ids(mapping_list)
        if task.id not in mapped_ids:
                task.wcrt_intertask = 0
                task.final_wcrt = 0
                return

        analysis = analyze_dag_partitioned_fp(mapping_list, ts, task.dag_id, wcrt_algor)
        if task.id not in analysis['local_wcrt_map']:
                task.wcrt_intertask = 0
                task.final_wcrt = 0
                return

        task.wcrt_intertask = analysis['local_wcrt_map'][task.id]
        if task.wcrt_intertask == -1:
                task.final_wcrt = -1
                return
        task.final_wcrt = analysis['finish_map'][task.id]

        
