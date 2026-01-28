import random
from math import *
from utilization_generate import drs
minDelta = 0
task_length_max = 3
switch_con = 0.1
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
        self.preempt = 0


    def info(self):
        task_info = "task_id:" + str(self.id) + "   pri:" + str(self.pri) + "   eLO:" + str(self.eLO) + "   eHI:" + str(self.eHI) + "   peried:" + str(self.dLO) + "   length:" + str(self.length) + "   cri:" + str(self.cri) + "   io_delay:" + str(self.io_delay) + "   switch_delay:" + str(self.switch_delay) + "   wcrt_intertask:" + str(self.wcrt_intertask)+ "   final_wcrt:" + str(self.final_wcrt)
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
                for T in self.HI.union(self.LO).union(self.HILO):
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

    def __init__(self, numTask, sumU, CF, CP, numCore=1):
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
            for i in range(T.length):
                    io = random.randint(10, 1000)
                    T.io_list.append(io)
            self.add(T, T.cri)