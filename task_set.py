import random
from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional
from math import *
from utilization_generate import drs
minDelta = 0
switch_con = 0.1


@dataclass
class SubTaskNode:
    """任务内部 DAG 节点（草稿数据结构）。"""
    node_id: int
    tag: str
    cri: int
    eLO: float = 0.0
    eHI: float = 0.0
    uLO: float = 0.0
    uHI: float = 0.0
    predecessors: Set[int] = field(default_factory=set)
    successors: Set[int] = field(default_factory=set)


@dataclass
class TaskInternalDAG:
    """单个任务内部 DAG（草稿数据结构）。"""
    task_id: int
    nodes: Dict[int, SubTaskNode] = field(default_factory=dict)
    root_nodes: List[int] = field(default_factory=list)
    sink_nodes: List[int] = field(default_factory=list)
    longest_path_nodes: int = 0
    max_depth_limit: int = 0
    edge_prob: float = 0.0

class MCTask(object):
    """object for a Mixed-criticality task  """

    def __init__(self, id, eLO, eHI, dLO, dHI, pLO, pHI, cri):
        self.id = id
        self.eLO = eLO  # worst-case execution time
        self.eHI = eHI
        self.dLO = dLO  # deadline
        self.dHI = dHI  # deadline
        self.pLO = pLO  # period
        self.pHI = pHI  # period
        self.uLO = float(eLO) / pLO
        self.uHI = float(eHI) / pHI
        self.pri = dLO  ## priority
        #self.pri = pLO
        self.cri = cri  # 0, HI-crit; 1, LO-crit
        self.pts = 0
        self.resp = 0
        self.io_list = []
        self.io_dis = 0
        self.io_delay = 0
        self.wcrt_intertask = 0
        self.final_wcrt = 0
        self.core_list = []
        self.eLO_new = 0
        self.eHI_new = 0
        if self.cri == 0:
                self.slack = self.dHI - self.eHI
        else:
                self.slack = self.dLO - self.eLO
        # 单任务默认映射到单核，保持与映射和实验脚本中的属性一致
        self.node_number = 1
        # DAG 相关属性（全局任务图）
        self.dag_id = -1
        self.predecessors = set()
        self.successors = set()

        # 任务内部 DAG 属性（论文方案草稿）
        self.internal_dag: Optional[TaskInternalDAG] = None
        self.internal_node_count = 0
        self.internal_depth_limit = 0


    def info(self):
        task_info = "task_id:" + str(self.id) + "   pri:" + str(self.pri) + "   eLO:" + str(self.eLO) + "   eHI:" + str(self.eHI) + "   peried:" + str(self.dLO) + "   cri:" + str(self.cri) + "   io_delay:" + str(self.io_delay) + "   switch_delay:" + str(self.switch_delay) + "   wcrt_intertask:" + str(self.wcrt_intertask)+ "   final_wcrt:" + str(self.final_wcrt)
        return task_info
        #print("task_id:",self.id,"pri:",self.pri,"eLO:",self.eLO,"eHI",self.eHI,"peried and deadline:",self.dLO,"node_number",self.node_number,"cri",self.cri)
    def reset(self):
        #self.pri = 0
        self.pts = 0
        self.resp = 0
        self.io_dis = 0
        self.io_delay = 0
        self.switch_delay = 0
        self.wcrt_intertask = 0
        self.final_wcrt = 0
        self.core_list = []
    def core_list_add(self ,core):
        if core not in self.core_list:
            self.core_list.append(core)
    def core_list_remove(self, core):
        if core in self.core_list:
            self.core_list.remove(core)
    def reset_core_list(self):
        self.core_list = []

class MCTaskSet(object):
        """object for a Mixed-criticality taskset  """

        def __init__(self):
                self.LO = set()  #  LO-mode taskset
                self.HI = set()   # HI-mode taskset
                self.sch =  True   # sch represents whether the mixed-criticality taskset is schedulable.
                
        def reset(self):
                for T in self.HI.union(self.LO):
                        T.reset()


        def add(self, T, cri):
                if cri:
                        self.LO.add(T)
                else:
                        self.LO.add(T)
                        self.HI.add(T)

        def remove(self, T, cri):
                if cri==1 and T in self.LO:
                        self.LO.remove(T)
                if cri==0 and T in self.HI:
                        self.LO.remove(T)
                        self.HI.remove(T)

        def clear(self):
                self.LO = set()
                self.HI = set()
        def get_task_by_id(self, id):
                for task in self.LO:
                        if task.id == id:
                                return task
                for task in self.HI:
                        if task.id == id:
                                return task

        def priority_assignment_DM_HI (self, tasks, pri):    # correct
                # first according to DM, if two tasks have the same deadline,
                # we assign higher priority to the task with higher criticality.
                tasksList = list(tasks)
                n = len (tasksList)
                for T in tasksList:
                        T.pri = pri
                for i in range(n):
                        T = tasksList[i]
                        for Tk in tasksList[i+1:]:
                                if (T.dLO < Tk.dLO):
                                        T.pri += 1
                                elif (T.dLO == Tk.dLO) and (T in self.HI):
                                        T.pri += 1
                                else:
                                        Tk.pri += 1
                for T in tasksList:
                        T.pts = T.pri
        
        def priority_assignment_Slack (self, tasks, pri):    # correct
                # first according to DM, if two tasks have the same deadline,
                # we assign higher priority to the task with higher criticality.
                tasksList = list(tasks)
                n = len (tasksList)
                for T in tasksList:
                        T.pri = pri
                for i in range(n):
                        T = tasksList[i]
                        for Tk in tasksList[i+1:]:
                                if (T.slack < Tk.slack):
                                        T.pri += 1
                                elif (T.slack == Tk.slack) and (T in self.HI):
                                        T.pri += 1
                                else:
                                        Tk.pri += 1
                for T in tasksList:
                        T.pts = T.pri

        def priority_assignment_CRMS (self, tasks):
                for task in tasks:
                        task.pri = 0
                tasksHI = list(tasks.intersection(self.HI))
                tasksLO = list(tasks.intersection(self.LO.difference(self.HI)))

                tasksLO = sorted(tasksLO,key=lambda task:task.pHI,reverse = True)
                tasksHI = sorted(tasksHI,key=lambda task:task.pHI,reverse = True)
                nLO = len(tasksLO)
                nHI = len(tasksHI)
                for i in range(nLO):
                        tasksLO[i].pri = i + 1
                        tasksLO[i].pts = i + 1
                for i in range(nHI):
                        tasksHI[i].pri = nLO+i+1
                        tasksHI[i].pts = nLO +i+1
        
        def priority_assignment_node_number (self, tasks):
                tasksList = list(tasks)
                n = len (tasksList)
                for task in tasks:
                        task.pri = 0
                for i in range(n):
                       T = tasksList[i]
                       for Tk in tasksList[i+1:]:
                                if (T.node_number < Tk.node_number):
                                        T.pri += 1
                                elif (T.node_number == Tk.node_number) and (T.dLO < Tk.dLO):
                                        T.pri += 1
                                elif (T.node_number == Tk.node_number) and (T.dLO == Tk.dLO) and (T in self.HI):
                                        T.pri += 1
                                else:
                                        Tk.pri += 1
                for T in tasksList:
                        T.pts = T.pri
        


        def amc_rtb_pts_wcrt_btTask_sch(self, T, hp, btT = None):
                
                """DO NOT CONSIDER LBP after mode change, and totally use the AMC-MAX method in [Baruah11]"""
                # Our own work
                
                #self.assert_implicit_deadline_sporadic()               
                        

                def block_time_LO(T,lpTasks):
                        btL=0                        
                        for Tp in lpTasks:
                                if Tp.pri >= T.pri:
                                        btL=max(btL,Tp.eLO-minDelta)
                        return btL               
                        

                def worst_case_start_time_LO_sch(q,T,bt,hpTasks):   ## correct
                      
                        st1 = bt +(q-1)*T.eLO
                        wcst = st1
                        bound = q * T.dLO
                        while True:
                                st = 0
                                for Tp in hpTasks:
                                        st = st + (1+ (wcst//Tp.pLO ))* Tp.eLO
                                st=st+st1
                                if st == wcst :
                                        break
                                wcst = st
                                if wcst > bound :
                                        return -1
                        if wcst > bound:
                                wcst = -1
                        return wcst
             
                def worst_case_finish_time_LO_sch(q,T,bt,hpTasks,htTasks):  ## correct                        
##                        
                        wcst = worst_case_start_time_LO_sch(q,T,bt,hpTasks)
                        if wcst == -1 :
                                return -1
                        st1 = wcst + T.eLO
                        wcftL = st1
                        bound = (q-1) * T.pLO + T.dHI
                        while  wcftL <= bound:
                                ft = st1 + sum([(ceil(wcftL / Tp.pLO) - (1+ (int(wcst / Tp.pLO )))) * Tp.eLO for Tp in htTasks])
                                if ft==wcftL:
                                        break
                                wcftL = ft
                        if wcftL > bound:
                                return -1  
                        return wcftL
                    
                def longest_busy_period_LO (T,bt,hpTasks):   ## correct                                     
                        lbp = 0
                        #所有任务低关键度执行时间总和
                        for Tp in hpTasks:
                                lbp=lbp+Tp.eLO
                        lbp = bt + T.eLO + lbp
                        bound = lbp*1000               ###############it is a bound  TODO20200411
                        while True :

                                temp = bt + ceil( lbp / T.pLO ) * T.eLO + sum ( ceil( lbp / Tp.pLO ) * Tp.eLO for Tp in hpTasks)
                                if temp == lbp:
                                        break
                                lbp = temp
                                if lbp>bound:
                                        break
                        return lbp


                def worst_case_response_time_LO_sch(T,bt,hpTasks,htTasks):   ## T：当前任务；bt：0；hpTasks：除该任务外所有任务；htTasks：所有能抢占该任务的任务
                    
                        lbpL = longest_busy_period_LO (T,bt,hpTasks)                        
                        maxqL = (floor (lbpL / T.pLO)) + 1                        
                        q = 1                        
                        wcrt = 0                 
                        while ( q  <= maxqL ):                                
                                wcft = worst_case_finish_time_LO_sch (q,T,bt,hpTasks,htTasks) 
                                if wcft == -1:
                                        return -1
                                rt = wcft -(q-1) * T.pLO
                                if rt > T.dHI:
                                        return -1
                                wcrt = max ( rt, wcrt)
                                q = q + 1
                        return wcrt 
                

                def block_time_HI(T,lpH):   ## correct
                        
                        btH=0                        
                        for Tp in lpH:
                                if Tp.pri >= T.pri:
                                        btH=max(btH,Tp.eHI-minDelta)
                        return btH
                
                

                def worst_case_start_time_HI_sch(q,T,bt,hpH):  ## correct
                        
                        st1 = bt + (q-1)*T.eHI
                        wcst = st1
                        bound = (q-1) * T.pLO + T.dHI
                        while wcst <= bound :
                                st=0
                                for Tp in hpH :
                                        st=st+(1+ (int(wcst/Tp.pLO )))*Tp.eHI
                                st = st1 + st
                                if st == wcst :
                                        break
                                wcst = st
                                if st > bound:
                                        return -1
                        if wcst > bound :
                                wcst = -1  
                        return wcst
                        
                        
                def worst_case_finish_time_HI_sch(q,T,bt,hpH, htH):  ## correct
                                                
                        wcst = worst_case_start_time_HI_sch(q,T,bt,hpH)
                        if wcst == -1 :
                                return -1
                        st1 = wcst + T.eHI
                        wcftL = st1
                        bound =(q-1) * T.pLO + T.dHI
                        while wcftL <= bound :
                                ft = st1 + sum([(ceil(wcftL / Tp.pLO) - (1+ (int(wcst / Tp.pLO )))) * Tp.eHI for Tp in htH])
                                if ft==wcftL:
                                        break
                                wcftL = ft
                        if wcftL > bound:
                                return -1  
                        return wcftL
                    
                def longest_busy_period_HI (T,btH,hpH):  ## correct                                             
                                                               
                        lbpH = T.eHI + sum([Tp.eHI for Tp in hpH]) + btH
                        #print('lbp=%d' %lbpH )
                        bound = lbpH*1000
                        while True:
                                #print('lbp=%d' %lbpH )
                                temp = btH + ceil( lbpH / T.pLO ) * T.eHI + sum ( ceil( lbpH / Tp.pHI ) * Tp.eHI for Tp in hpH )
                                if temp == lbpH:
                                        break
                                lbpH = temp
                                if lbpH > bound:
                                       break
                        return lbpH
                
                def worst_case_response_time_HI_sch(T,bt,hpH,htH):  ## correct

                        lbpH = longest_busy_period_HI(T,bt,hpH)
                        maxqH = (floor(lbpH / T.pLO)) + 1                        
                        q = 1
                        wcrt = 0
                        #print('ub, lbpH, maxqH, q, wcft')
                        while ( q  <= maxqH ):
                                wcft = worst_case_finish_time_HI_sch(q, T, bt, hpH, htH)
                                if wcft  == -1:
                                        return -1                                
                                rt = wcft -(q-1) * T.pLO
                                if rt > T.dHI:
                                        return -1
                                #print([bt, lbpH, maxqH, q, wcft])
                                wcrt = max ( rt, wcrt)
                                q = q + 1
                        return wcrt
                    
                def worst_case_finish_time_MC_btTask_sch(qs,T,hpL,hpH,htH,htL,wcstL, wcftL, btT):
                        
                        """mode change occurs before wcstL:""" 
                        IL = sum([(1+ (int(wcstL / Tp.pLO ))) * Tp.eLO for Tp in hpL ])
                        bt = 0     
                        if not (btT ==  None):                    
                                bt = max(btT.eLO,btT.eHI)-minDelta if qs==1 else btT.eLO - minDelta
                        st1 = bt + (qs-1)*T.eLO + IL
                        wcstMC = st1
                        bound = (qs-1) * T.pHI + T.dHI

                        while wcstMC <= bound:
                                st = st1 + sum((1+ (int(wcstMC / Tp.pHI ))) * Tp.eHI for Tp in hpH)
                                if st == wcstMC:
                                        break
                                if st > bound:
                                        return -1
                                wcstMC = st
                        if wcstMC > bound :
                                return -1
                                
                        ft1 = wcstMC + T.eHI
                        wcftH = ft1                                
                        while wcftH <= bound:
                                ft = ft1 + sum([(ceil(wcftH / Tp.pHI) - (1+ floor(wcstMC / Tp.pHI ))) * Tp.eHI for Tp in htH])
                                if ft == wcftH :
                                        break
                                wcftH = ft
                        if wcftH > bound :
                                return -1                        
                        wcftMC1 = wcftH
                                

                        """ mode change occurs between wcstL and wcftL"""                                        
                        IL = sum([(ceil(wcftL / Tp.pLO) - (1+ floor(wcstL / Tp.pLO ))) * Tp.eLO for Tp in htL ])
                        ft1 = wcstL + T.eHI + IL
                        wcftH = ft1                        
                        while wcftH <= bound:
                                ft = ft1 + sum([(ceil(wcftH / Tp.pHI) - (1+ floor(wcstL / Tp.pHI ))) * Tp.eHI for Tp in htH])
                                if ft == wcftH :
                                        break
                                wcftH = ft
                        if wcftH > bound :
                                return -1
                        wcftMC2 = wcftH
                        return max(wcftMC1,wcftMC2)                       
                    
                            
                def wcrt_cc_func_btTask_sch (T,hpTasks,htTasks,hpH,htH,btT): #Mode change
                        hpL = hpTasks - hpH                                                
                        htL = htTasks - htH
                        hntTasks = hpTasks - htTasks
                        hntH = hntTasks.intersection(self.HI)
                        hntL = hntTasks - hntH                       


                        wcrt = 0  
                        bt = 0
                        if not btT == None:    
                                bt = btT.eLO - minDelta                
                        lbpL = longest_busy_period_LO (T,bt,hpTasks)                        
                        maxqL = (floor (lbpL / T.pLO)) + 1
                        qs = 1
                        
                        #print('qs, wcstL, wcftL, lbpLO, maxqMC, wcftMC')
                        while qs <= maxqL:
                                wcstL = worst_case_start_time_LO_sch(qs,T,bt,hpTasks)
                                if wcstL == -1:
                                        return -1
                                wcftL = worst_case_finish_time_LO_sch(qs,T,bt,hpTasks,htTasks)
                                if wcftL == -1:
                                        return -1  
                                               
                                wcftMC = worst_case_finish_time_MC_btTask_sch(qs,T,hpL,hpH,htH,htL,wcstL, wcftL, btT)
                                if wcftMC == -1:
                                        return -1
                                rt = wcftMC -(qs-1) * T.pLO
                                if rt > T.dHI:
                                        return -1                                
                                wcrt = max(wcrt, rt)                               
                                qs = qs + 1
                        return wcrt 
                    
                
                def worst_case_reponse_time_btTask_sch(T, hp, btT = None):
                        hpTasks = hp - set([T])
                        #LO mode
                        htTasks = set()                        
                        for Tp in hpTasks :
                                if Tp.pri > T.pri :
                                        htTasks.add(Tp)
                        bt = 0
                        if not (btT == None):
                                bt =  btT.eLO - minDelta 
                        wcrtL= worst_case_response_time_LO_sch(T,bt,hpTasks,htTasks)
                        if wcrtL== -1:
                                return -1
                        if not T in self.HI:
                                T.resp = wcrtL
                                return wcrtL
                            
                        #HI mode
                        bt = 0                         
                        if not (btT == None) and  btT in self.HI:
                                bt = btT.eHI - minDelta
                        hpH = hpTasks.intersection(self.HI)
                        htH = htTasks.intersection(self.HI)                       
                        wcrtH = worst_case_response_time_HI_sch(T,bt,hpH,htH)
                        if wcrtH== -1:
                                return -1
                        
                        #Mode change
                        wcrtMC = wcrt_cc_func_btTask_sch(T,hpTasks,htTasks,hpH,htH,btT) 
                        if wcrtMC == -1:
                                return -1                       
                        wcrt = max(wcrtL,wcrtH,wcrtMC)
                        T.resp = wcrt
                        return wcrt
                return worst_case_reponse_time_btTask_sch(T, hp, btT)
        



class Drs_gengerate(MCTaskSet):

    def __init__(self, numTask, sumU, CF, CP, numCore=1, dag_size_range=(3, 6), edge_prob=0.4, internal_subtask_enable=True, internal_subtask_size_range=(5, 8), internal_edge_prob=0.3, internal_depth_ratio=0.5):
        MCTaskSet.__init__(self)
        self._sfmc_num_core = numCore
        self._sfmc_b = (3.67 * float(numCore) / float(numCore - 1)) if numCore > 1 else None
        max_retry = 200
        for _ in range(max_retry):
            self.clear()
            # 高关键度任务的个数
            number_HItasks = (int)(numTask * CP)
            core_nums = [1 for _ in range(numTask)]
            # DRS生成HItask在HI模式下利用率——sumU_HI（不再限制单任务利用率上界）
            sumU_HI = sumU * CF * CP
            if number_HItasks == 0:
                u_HI_HI = []
            elif number_HItasks == 1:
                u_HI_HI = [sumU_HI]
            else:
                hi_upper = [2.0 for _ in range(number_HItasks)]
                u_HI_HI = drs(number_HItasks, sumU_HI, hi_upper, None) if number_HItasks > 0 else []
            # DRS生成所有任务在LO模式下利用率（不再限制单任务利用率上界）
            lo_upper = [1.0 for _ in range(numTask)]
            u_LO = drs(numTask, sumU, lo_upper, None)

            for task_idx in range(numTask):
                ri = random.uniform(log(10), log(1000 + 1))
                pHI = int(exp(ri) // 1) * 1
                eLO = u_LO[task_idx] * pHI
                eHI = u_HI_HI[task_idx] * pHI if task_idx < number_HItasks else 0
                cri = 0 if task_idx < number_HItasks else 1
                # 保证 HI 任务满足 uHI > uLO，避免后续内部 DRS 以 uLO 作为 lower_constraints 时无解。
                if cri == 0 and eHI <= eLO:
                    eHI = eLO * 1.001
                task = MCTask(task_idx, eLO / core_nums[task_idx], eHI / core_nums[task_idx], pHI, pHI, pHI, pHI, cri)
                for _ in range(task.node_number):
                    io = random.randint(10, 1000)
                    task.io_list.append(io)
                self.add(task, task.cri)
            self._build_task_dags(dag_size_range=dag_size_range, edge_prob=edge_prob)

            if internal_subtask_enable:
                self.generate_two_level_tasksets(
                    subtask_size_range=internal_subtask_size_range,
                    edge_prob=internal_edge_prob,
                    depth_ratio=internal_depth_ratio,
                )

            if self._apply_sfmc_constraints(numCore):
                return

        raise ValueError(f"Failed to generate an SFMC-constrained taskset after {max_retry} retries")

    def _critical_path_weight(self, task: MCTask, mode: str) -> float:
        dag = task.internal_dag
        if dag is None or not dag.nodes:
            return float(task.eLO if mode == "NS" else task.eHI)

        node_ids = sorted(dag.nodes.keys())
        indeg = {nid: len(dag.nodes[nid].predecessors) for nid in node_ids}
        queue = sorted([nid for nid in node_ids if indeg[nid] == 0])
        topo = []
        while queue:
            current = queue.pop(0)
            topo.append(current)
            for succ_id in dag.nodes[current].successors:
                indeg[succ_id] -= 1
                if indeg[succ_id] == 0:
                    queue.append(succ_id)
                    queue.sort()
        if len(topo) != len(node_ids):
            return -1.0

        dist = {}
        for nid in topo:
            wcet = float(dag.nodes[nid].eLO if mode == "NS" else dag.nodes[nid].eHI)
            preds = dag.nodes[nid].predecessors
            if not preds:
                dist[nid] = wcet
            else:
                dist[nid] = max(dist[p] for p in preds) + wcet
        return max(dist.values()) if dist else 0.0

    def _apply_sfmc_constraints(self, m: int) -> bool:
        if m <= 1:
            return False

        b = 3.67 * float(m) / float(m - 1)
        if b <= 1.0:
            return False

        for task in self.LO:
            task.C_N = float(task.eLO)
            task.C_O = float(task.eHI) if task.cri == 0 else 0.0
            task.D = float(task.dLO)
            task.D_vir = task.D / (b - 1.0)

            if task.internal_dag is None or not task.internal_dag.nodes:
                ns_cap = max(1e-12, task.D_vir * 0.5)
                task.L_N = min(task.C_N, ns_cap)
                if task.cri == 0:
                    cs_cap = max(1e-12, (task.D - task.D_vir) * 0.5)
                    task.L_O = min(task.C_O, cs_cap)
                else:
                    task.L_O = 0.0
            else:
                task.L_N = self._critical_path_weight(task, "NS")
                task.L_O = self._critical_path_weight(task, "CS") if task.cri == 0 else 0.0

            if task.L_N <= 0:
                return False
            if task.cri == 0 and task.L_O <= 0:
                return False

            # 约束改为“最长路径执行时间不高于窗口上界”。
            if task.L_N - task.D_vir > 1e-12:
                return False
            if task.cri == 0 and (task.L_O - (task.D - task.D_vir) > 1e-12):
                return False

            u_n = task.C_N / task.D_vir
            if u_n <= 1.0:
                s_n = u_n
            else:
                denom_n = task.D_vir - task.L_N
                if denom_n <= 0:
                    return False
                s_n = (task.C_N - task.L_N) / denom_n
            if s_n > m:
                return False
            task.sfmc_SN = max(0.0, float(s_n))

            if task.cri == 0:
                denom_uo = task.D - task.D_vir
                if denom_uo <= 0:
                    return False
                u_o = (task.C_O - task.sfmc_SN * task.D_vir) / denom_uo
                if u_o <= 1.0:
                    s_o = u_o
                else:
                    denom_o = task.D - task.D_vir - task.L_O
                    if denom_o <= 0:
                        return False
                    s_o = (task.C_O - task.sfmc_SN * task.D_vir - task.L_O) / denom_o
                if s_o > m:
                    return False
                task.sfmc_SO = max(0.0, float(s_o))
            else:
                task.sfmc_SO = 0.0

        return True

    # ===== 论文方案改造（任务内 DAG 两层生成） =====
    def _add_internal_edge(self, dag: TaskInternalDAG, src_id: int, dst_id: int):
        if src_id == dst_id:
            return
        if dst_id in dag.nodes[src_id].successors:
            return
        dag.nodes[src_id].successors.add(dst_id)
        dag.nodes[dst_id].predecessors.add(src_id)

    def _can_add_internal_edge(self, dag: TaskInternalDAG, src_id: int, dst_id: int):
        if src_id == dst_id:
            return False
        if dst_id in dag.nodes[src_id].successors:
            return False
        return True

    def _build_internal_levels(self, node_count: int, depth_limit: int):
        """为内部节点分配层级，层级越大表示越靠后（仅首尾层保留唯一 root/sink）。"""
        levels = [0] * node_count
        if node_count <= 1:
            return levels
        max_level = max(2, depth_limit - 1)
        levels[0] = 0
        levels[-1] = max_level
        for idx in range(1, node_count - 1):
            levels[idx] = random.randint(1, max_level - 1)
        return levels

    def _ensure_internal_weak_connected(self, dag: TaskInternalDAG, levels):
        """若内部图非弱连通，通过补边将连通分量串联。"""
        node_ids = list(dag.nodes.keys())
        visited = set()
        components = []

        for node_id in node_ids:
            if node_id in visited:
                continue
            stack = [node_id]
            comp = []
            visited.add(node_id)
            while stack:
                current = stack.pop()
                comp.append(current)
                neighbors = dag.nodes[current].successors.union(dag.nodes[current].predecessors)
                for nxt in neighbors:
                    if nxt not in visited:
                        visited.add(nxt)
                        stack.append(nxt)
            components.append(comp)

        if len(components) <= 1:
            return

        components.sort(key=lambda comp: min((levels[n], n) for n in comp))
        for idx in range(len(components) - 1):
            left = components[idx]
            right = components[idx + 1]
            left_node = min(left, key=lambda n: (levels[n], n))
            right_node = max(right, key=lambda n: (levels[n], n))
            if (levels[left_node], left_node) <= (levels[right_node], right_node):
                self._add_internal_edge(dag, left_node, right_node)
            else:
                self._add_internal_edge(dag, right_node, left_node)

    def _calc_internal_longest_path_nodes(self, dag: TaskInternalDAG):
        node_ids = sorted(dag.nodes.keys())
        indegree = {node_id: len(dag.nodes[node_id].predecessors) for node_id in node_ids}
        queue = [node_id for node_id in node_ids if indegree[node_id] == 0]
        topo = []
        while queue:
            current = queue.pop(0)
            topo.append(current)
            for succ_id in dag.nodes[current].successors:
                indegree[succ_id] -= 1
                if indegree[succ_id] == 0:
                    queue.append(succ_id)

        if len(topo) != len(node_ids):
            return 0

        dp = {node_id: 1 for node_id in topo}
        for node_id in topo:
            for succ_id in dag.nodes[node_id].successors:
                candidate = dp[node_id] + 1
                if candidate > dp[succ_id]:
                    dp[succ_id] = candidate
        return max(dp.values()) if dp else 0

    def _calc_internal_min_max_path_nodes(self, dag: TaskInternalDAG):
        """返回 root->sink 的最短/最长路径节点数；若非法 DAG 返回 (0,0)。"""
        if len(dag.root_nodes) != 1 or len(dag.sink_nodes) != 1:
            return 0, 0

        root_id = dag.root_nodes[0]
        sink_id = dag.sink_nodes[0]
        node_ids = sorted(dag.nodes.keys())

        indegree = {node_id: len(dag.nodes[node_id].predecessors) for node_id in node_ids}
        queue = [node_id for node_id in node_ids if indegree[node_id] == 0]
        topo = []
        while queue:
            current = queue.pop(0)
            topo.append(current)
            for succ_id in dag.nodes[current].successors:
                indegree[succ_id] -= 1
                if indegree[succ_id] == 0:
                    queue.append(succ_id)
        if len(topo) != len(node_ids):
            return 0, 0

        inf = 10 ** 9
        min_dp = {node_id: inf for node_id in node_ids}
        max_dp = {node_id: -inf for node_id in node_ids}
        min_dp[root_id] = 1
        max_dp[root_id] = 1

        for node_id in topo:
            if max_dp[node_id] < 0:
                continue
            for succ_id in dag.nodes[node_id].successors:
                min_dp[succ_id] = min(min_dp[succ_id], min_dp[node_id] + 1)
                max_dp[succ_id] = max(max_dp[succ_id], max_dp[node_id] + 1)

        if max_dp[sink_id] < 0 or min_dp[sink_id] >= inf:
            return 0, 0
        return int(min_dp[sink_id]), int(max_dp[sink_id])

    def _internal_hi_predecessor_rule_ok(self, dag: TaskInternalDAG):
        """若目标子任务为 HI 关键度（cri=0），其所有前驱也必须为 HI。"""
        for node_id, node in dag.nodes.items():
            if node.cri != 0:
                continue
            for pred_id in node.predecessors:
                pred = dag.nodes.get(pred_id)
                if pred is None:
                    continue
                if pred.cri != 0:
                    return False
        return True

    def _refresh_internal_dag_summary(self, dag: TaskInternalDAG):
        dag.root_nodes = [node_id for node_id, node in dag.nodes.items() if len(node.predecessors) == 0]
        dag.sink_nodes = [node_id for node_id, node in dag.nodes.items() if len(node.successors) == 0]
        dag.longest_path_nodes = self._calc_internal_longest_path_nodes(dag)

    def _internal_dag_constraints_ok(self, dag: TaskInternalDAG):
        self._refresh_internal_dag_summary(dag)
        min_path_nodes, max_path_nodes = self._calc_internal_min_max_path_nodes(dag)
        return (
            len(dag.root_nodes) == 1
            and len(dag.sink_nodes) == 1
            and dag.longest_path_nodes >= 3
            and min_path_nodes >= 3
            and (max_path_nodes - min_path_nodes) <= 1
            and self._internal_hi_predecessor_rule_ok(dag)
        )

    def build_task_internal_dag(self, task: MCTask, subtask_size_range=(5, 8), edge_prob=0.3, depth_ratio=0.5) -> TaskInternalDAG:
        """
        构建任务内部 DAG：
        1) 单根单汇；
        2) root->sink 最短/最长路径差 <= 1；
        3) 子任务入度<=3、出度<=2；
        4) 最短路径（按节点数）>=3。
        """
        max_retry = 80
        for _ in range(max_retry):
            # 为了提高高利用率下生成可行任务集的概率，压缩深度并增加并行度。
            # 层数使用 [3, 5]，在保持最短路径>=3 的同时降低关键路径执行量。
            level_count = random.randint(3, 5)
            depth_limit = level_count

            # 每层节点数改为 [2, 8]（首末层固定 1），提高并行潜力。
            counts = [1 for _ in range(level_count)]
            for lv in range(1, level_count - 1):
                counts[lv] = random.randint(2, 8)
            node_count = sum(counts)

            dag = TaskInternalDAG(task_id=task.id, max_depth_limit=depth_limit, edge_prob=edge_prob)
            for node_id in range(node_count):
                dag.nodes[node_id] = SubTaskNode(node_id=node_id, tag=f"T{task.id}_N{node_id}", cri=task.cri)

            # 根据层分组节点
            level_groups = []
            cursor = 0
            for c in counts:
                level_groups.append(list(range(cursor, cursor + c)))
                cursor += c

            # 逐层连边：保证每个 dst 至少一个前驱、每个 src 至少一个后继
            ok = True
            for lv in range(level_count - 1):
                src_nodes = level_groups[lv]
                dst_nodes = level_groups[lv + 1]

                out_used = {sid: 0 for sid in src_nodes}
                in_used = {did: 0 for did in dst_nodes}

                # step1: 每个 dst 至少一个前驱
                dst_order = dst_nodes[:]
                random.shuffle(dst_order)
                for dst_id in dst_order:
                    candidates = [sid for sid in src_nodes if self._can_add_internal_edge(dag, sid, dst_id)]
                    if not candidates:
                        ok = False
                        break
                    min_out = min(out_used[sid] for sid in candidates)
                    choose = [sid for sid in candidates if out_used[sid] == min_out]
                    src_id = random.choice(choose)
                    self._add_internal_edge(dag, src_id, dst_id)
                    out_used[src_id] += 1
                    in_used[dst_id] += 1
                if not ok:
                    break

                # step2: 每个 src 至少一个后继
                src_order = src_nodes[:]
                random.shuffle(src_order)
                for src_id in src_order:
                    if out_used[src_id] > 0:
                        continue
                    candidates = [did for did in dst_nodes if self._can_add_internal_edge(dag, src_id, did)]
                    if not candidates:
                        ok = False
                        break
                    min_in = min(in_used[did] for did in candidates)
                    choose = [did for did in candidates if in_used[did] == min_in]
                    dst_id = random.choice(choose)
                    self._add_internal_edge(dag, src_id, dst_id)
                    out_used[src_id] += 1
                    in_used[dst_id] += 1
                if not ok:
                    break

                # step3: 概率补边（受入/出度约束）
                for src_id in src_nodes:
                    for dst_id in dst_nodes:
                        if random.random() <= edge_prob and self._can_add_internal_edge(dag, src_id, dst_id):
                            self._add_internal_edge(dag, src_id, dst_id)
                            out_used[src_id] += 1
                            in_used[dst_id] += 1

            if not ok:
                continue

            self._refresh_internal_dag_summary(dag)
            if self._internal_dag_constraints_ok(dag):
                task.internal_dag = dag
                task.internal_node_count = node_count
                task.internal_depth_limit = depth_limit
                return dag

        raise ValueError(f"Task {task.id} internal DAG does not satisfy required constraints after {max_retry} retries")

    def allocate_internal_subtask_utilization(self, task: MCTask):
        """
        基于任务级 uLO/uHI，再次使用 DRS 对任务内部子任务分配利用率并换算执行时间。
        """
        if task.internal_dag is None or len(task.internal_dag.nodes) == 0:
            return

        node_ids = sorted(task.internal_dag.nodes.keys())
        n = len(node_ids)

        d_vir_limit = None
        hi_window_limit = None
        if self._sfmc_b is not None and self._sfmc_b > 1.0:
            d_vir_limit = float(task.dLO) / (self._sfmc_b - 1.0)
            hi_window_limit = float(task.dLO) - d_vir_limit

        max_retry = 80
        assigned = False
        for _ in range(max_retry):
            u_lo_list = drs(n, task.uLO, [0.8] * n, None)
            if task.cri == 0:
                u_hi_list = drs(n, task.uHI, [0.8] * n, u_lo_list)
            else:
                u_hi_list = [0.0] * n

            for idx, node_id in enumerate(node_ids):
                node = task.internal_dag.nodes[node_id]
                node.uLO = float(u_lo_list[idx])
                node.uHI = float(u_hi_list[idx])
                node.eLO = node.uLO * task.pLO
                node.eHI = node.uHI * task.pHI

            if d_vir_limit is None:
                assigned = True
                break

            l_n = self._critical_path_weight(task, "NS")
            if l_n - d_vir_limit > 1e-12:
                continue
            if task.cri == 0:
                l_o = self._critical_path_weight(task, "CS")
                if l_o - hi_window_limit > 1e-12:
                    continue
            assigned = True
            break

        if not assigned:
            # 回退到最近一次分配结果，交由外层任务集约束筛选是否接受该样本。
            return

        # 更新 tag：标注 root/sink/inner
        root_set = set(task.internal_dag.root_nodes)
        sink_set = set(task.internal_dag.sink_nodes)
        for node_id in node_ids:
            role = "inner"
            if node_id in root_set:
                role = "root"
            elif node_id in sink_set:
                role = "sink"
            task.internal_dag.nodes[node_id].tag = f"T{task.id}_{role}_N{node_id}"

    def generate_two_level_tasksets(self, subtask_size_range=(5, 8), edge_prob=0.3, depth_ratio=0.5):
        """执行两层生成流程：任务级已生成 -> 逐任务构建内部 DAG 并分配子任务执行时间。"""
        for task in sorted(self.LO, key=lambda t: t.id):
            self.build_task_internal_dag(
                task,
                subtask_size_range=subtask_size_range,
                edge_prob=edge_prob,
                depth_ratio=depth_ratio,
            )
            self.allocate_internal_subtask_utilization(task)

    # 向后兼容：保留 draft 方法名
    def build_task_internal_dag_draft(self, task: MCTask, subtask_size_range=(5, 8), edge_prob=0.3, depth_ratio=0.5) -> TaskInternalDAG:
        return self.build_task_internal_dag(task, subtask_size_range, edge_prob, depth_ratio)

    def allocate_internal_subtask_utilization_draft(self, task: MCTask):
        return self.allocate_internal_subtask_utilization(task)

    def _add_edge(self, src_task, dst_task):
        src_task.successors.add(dst_task.id)
        dst_task.predecessors.add(src_task.id)

    def _build_task_dags(self, dag_size_range=(3, 6), edge_prob=0.4):
        """
        任务级仅保留“集合”概念，不再建立任务间前驱/后继关系。
        每个任务视作独立 DAG（dag_id = task.id），
        子任务级依赖由 `internal_dag` 维护。
        """
        tasks = sorted(list(self.LO), key=lambda task: task.id)
        for task in tasks:
            task.dag_id = task.id
            task.predecessors = set()
            task.successors = set()
