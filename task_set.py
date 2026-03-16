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
        self.core_list.append(core)
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
        # 高关键度任务的个数
        number_HItasks = (int)(numTask * CP)
        core_nums = []
        for i in range(numTask):
            core_nums.append(1)
        #DRS生成HItask在HI模式下利用率——sumU_HI；sumU_HI的值不能大于处理器个数，一旦大于处理器个数就意味着HImode下不可能在处理器上调度
        sumU_HI = min(numCore,sumU * CF * CP ,number_HItasks-0.00001)
        if number_HItasks==0:
            u_HI_HI = []
        elif number_HItasks==1:
            u_HI_HI = [sumU_HI]
        else:
            #u_HI_HI = drs(number_HItasks, sumU_HI, [1] * number_HItasks, None) if number_HItasks>0 else []
            u_HI_HI = drs(number_HItasks, sumU_HI, core_nums[0:number_HItasks], None) if number_HItasks>0 else []
        #DRS生成所有任务在LO模式下利用率
        u_LO_upperbound = core_nums[:]
        for i in range(len(u_HI_HI)):u_LO_upperbound[i]=u_HI_HI[i]
        #print(sum(u_LO_upperbound),sumU)
        u_LO = drs(numTask, sumU,u_LO_upperbound, None)

        for i in range(numTask):
            ri = random.uniform(log(10), log(1000 + 1))
            pHI = int(exp(ri) // 1) * 1
            eLO = u_LO[i] * pHI
            eHI = u_HI_HI[i] * pHI if i<number_HItasks else 0
            cri = 0 if i<number_HItasks else 1
            T = MCTask(i,eLO/core_nums[i],eHI/core_nums[i],pHI,pHI,pHI,pHI,cri)
            #T = MCTask(i+1,eLO,eHI,pHI,pHI,pHI,pHI,core_nums[i],cri)
            for i in range(T.node_number):
                    io = random.randint(10, 1000)
                    T.io_list.append(io)
            self.add(T, T.cri)
        self._build_task_dags(dag_size_range=dag_size_range, edge_prob=edge_prob)

        if internal_subtask_enable:
            self.generate_two_level_tasksets(
                subtask_size_range=internal_subtask_size_range,
                edge_prob=internal_edge_prob,
                depth_ratio=internal_depth_ratio,
            )

    # ===== 论文方案改造（任务内 DAG 两层生成） =====
    def _add_internal_edge(self, dag: TaskInternalDAG, src_id: int, dst_id: int):
        if src_id == dst_id:
            return
        if dst_id in dag.nodes[src_id].successors:
            return
        dag.nodes[src_id].successors.add(dst_id)
        dag.nodes[dst_id].predecessors.add(src_id)

    def _build_internal_levels(self, node_count: int, depth_limit: int):
        """为内部节点分配层级，层级越大表示越靠后。"""
        levels = [0] * node_count
        if node_count == 1:
            return levels
        max_level = max(1, depth_limit - 1)
        levels[0] = 0
        levels[-1] = max_level
        for idx in range(1, node_count - 1):
            levels[idx] = random.randint(0, max_level)
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

    def build_task_internal_dag(self, task: MCTask, subtask_size_range=(5, 8), edge_prob=0.3, depth_ratio=0.5) -> TaskInternalDAG:
        """
        构建任务内部 DAG：
        1) 节点数随机取 5~8；
        2) 按概率 p 生成前向边；
        3) 深度限制 d 与节点数成比例；
        4) 强制单根单汇；
        5) 若图非弱连通则补边连通。
        """
        min_nodes, max_nodes = subtask_size_range
        min_nodes = max(1, min_nodes)
        max_nodes = max(min_nodes, max_nodes)
        node_count = random.randint(min_nodes, max_nodes)

        depth_limit = max(2, int(ceil(node_count * depth_ratio)))
        levels = self._build_internal_levels(node_count, depth_limit)

        dag = TaskInternalDAG(task_id=task.id, max_depth_limit=depth_limit, edge_prob=edge_prob)
        for node_id in range(node_count):
            dag.nodes[node_id] = SubTaskNode(node_id=node_id, tag=f"T{task.id}_N{node_id}", cri=task.cri)

        # 先构造一条覆盖所有节点的主链，确保仅有 1 个根节点和 1 个汇点
        ordered_ids = sorted(range(node_count), key=lambda nid: (levels[nid], nid))
        for idx in range(len(ordered_ids) - 1):
            self._add_internal_edge(dag, ordered_ids[idx], ordered_ids[idx + 1])

        # 再按概率添加前向边，保持 DAG 且不改变单根单汇性质
        order_pos = {node_id: idx for idx, node_id in enumerate(ordered_ids)}
        for src_id in ordered_ids:
            for dst_id in ordered_ids[order_pos[src_id] + 2:]:
                if random.random() <= edge_prob:
                    self._add_internal_edge(dag, src_id, dst_id)

        self._ensure_internal_weak_connected(dag, levels)

        dag.root_nodes = [node_id for node_id, node in dag.nodes.items() if len(node.predecessors) == 0]
        dag.sink_nodes = [node_id for node_id, node in dag.nodes.items() if len(node.successors) == 0]
        dag.longest_path_nodes = self._calc_internal_longest_path_nodes(dag)

        task.internal_dag = dag
        task.internal_node_count = node_count
        task.internal_depth_limit = depth_limit
        return dag

    def allocate_internal_subtask_utilization(self, task: MCTask):
        """
        基于任务级 uLO/uHI，再次使用 DRS 对任务内部子任务分配利用率并换算执行时间。
        """
        if task.internal_dag is None or len(task.internal_dag.nodes) == 0:
            return

        node_ids = sorted(task.internal_dag.nodes.keys())
        n = len(node_ids)

        u_lo_list = drs(n, task.uLO, [1.0] * n, None)
        if task.cri == 0:
            u_hi_list = drs(n, task.uHI, [1.0] * n, u_lo_list)
        else:
            u_hi_list = [0.0] * n

        for idx, node_id in enumerate(node_ids):
            node = task.internal_dag.nodes[node_id]
            node.uLO = float(u_lo_list[idx])
            node.uHI = float(u_hi_list[idx])
            node.eLO = node.uLO * task.pLO
            node.eHI = node.uHI * task.pHI

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

    def _can_add_edge_with_deadline_constraint(self, dag_tasks, src_task, dst_task):
        """
        在连边前进行可行性检查：若加入 src->dst 后，DAG 中任意任务都满足
        Ti.eLO + longest_path_exec_time(Ti) <= Ti.dLO，则允许加入该边。
        """
        task_by_id = {task.id: task for task in dag_tasks}
        longest_suffix = {}

        for task in reversed(dag_tasks):
            max_suffix = 0
            for succ_id in task.successors:
                succ_task = task_by_id.get(succ_id)
                if succ_task is None:
                    continue
                max_suffix = max(max_suffix, succ_task.eLO + longest_suffix.get(succ_id, 0))

            if task.id == src_task.id:
                max_suffix = max(max_suffix, dst_task.eLO + longest_suffix.get(dst_task.id, 0))

            if task.eLO + max_suffix > task.dLO:
                return False
            longest_suffix[task.id] = max_suffix
        return True

    def _build_task_dags(self, dag_size_range=(3, 6), edge_prob=0.4):
        """
        将任务划分为多个 DAG，并满足约束：
        1) 每个任务为单核任务（在 MCTask 中固定为 node_number=1）。
        2) 每个 DAG 仅有一个根节点（入度为 0）和一个汇点（出度为 0）。
        3) 每个 DAG 的最长路径（按任务数计）不少于 3。
        4) 若目标任务为 HI 关键度，则其所有前置任务也必须为 HI 关键度。
        """
        tasks = sorted(list(self.LO), key=lambda task: task.id)
        if not tasks:
            return

        min_size, max_size = dag_size_range
        min_size = max(3, min_size)
        max_size = max(min_size, max_size)

        if len(tasks) < 3:
            for task in tasks:
                task.dag_id = 0
                task.predecessors = set()
                task.successors = set()
            return

        dag_sizes = []
        remaining = len(tasks)
        while remaining > 0:
            if remaining <= max_size and remaining >= min_size:
                dag_sizes.append(remaining)
                break

            candidate_min = min_size
            candidate_max = min(max_size, remaining - min_size)
            if candidate_max < candidate_min:
                dag_sizes[-1] += remaining
                break

            dag_size = random.randint(candidate_min, candidate_max)
            dag_sizes.append(dag_size)
            remaining -= dag_size

        start = 0
        dag_id = 0
        for dag_size in dag_sizes:
            dag_tasks = tasks[start:start + dag_size]
            if not dag_tasks:
                break

            for task in dag_tasks:
                task.dag_id = dag_id
                task.predecessors = set()
                task.successors = set()

            # 先构造一条覆盖全部节点的主链，保证：
            # - 单根单汇；
            # - 最长路径至少为 dag_size（因此 >=3）。
            hi_tasks = [task for task in dag_tasks if task.cri == 0]
            lo_tasks = [task for task in dag_tasks if task.cri != 0]
            random.shuffle(hi_tasks)
            random.shuffle(lo_tasks)
            ordered_tasks = hi_tasks + lo_tasks

            for idx in range(len(ordered_tasks) - 1):
                self._add_edge(ordered_tasks[idx], ordered_tasks[idx + 1])

            # 在不破坏单根单汇的前提下，随机添加部分前向边。
            # 使用 ordered_tasks 的前向方向可保持无环，且避免 LO->HI 约束冲突。
            for src_idx in range(len(ordered_tasks) - 1):
                src_task = ordered_tasks[src_idx]
                for dst_idx in range(src_idx + 2, len(ordered_tasks)):
                    if random.random() > edge_prob:
                        continue
                    dst_task = ordered_tasks[dst_idx]
                    if dst_task.id in src_task.successors:
                        continue
                    # HI 任务的前置任务必须是 HI 任务
                    if dst_task.cri == 0 and src_task.cri != 0:
                        continue
                    if self._can_add_edge_with_deadline_constraint(dag_tasks, src_task, dst_task):
                        self._add_edge(src_task, dst_task)


            start += dag_size
            dag_id += 1
