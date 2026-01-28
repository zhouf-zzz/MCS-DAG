from tqdm import tqdm
from math import *
import random
from task_set import Drs_gengerate
from mapping import *
from wcrt_cal import *
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd

# 指定中文使用宋体，英文使用Times New Roman
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['SimSun', 'Times New Roman']  # 首先尝试宋体，如果找不到则尝试Times New Roman


# 设置中文字体为宋体，英文字体为Times New Roman
# plt.rcParams['font.family'] = 'SimSun'  # 中文默认字体（宋体）
# plt.rcParams['font.sans-serif'] = ['SimSun']  # 中文备用字体列表（可选）
# plt.rcParams['font.serif'] = ['Times New Roman']  # 英文默认衬线字体
# plt.rcParams['mathttext.fontset'] = 'stix'  # 数学公式字体（可选，避免乱码）

# plt.rcParams['font.sans-serif'] = ['SimSun'] # 设置显示中文字体
# plt.rcParams['axes.unicode_minus'] = False  # 设置正常显示符号
# mpl.rcParams['font.family'] = 'sans-serif'
# mpl.rcParams['font.sans-serif'] = ['Times New Roman']
import time
FigWordSize = 16
marker_ku = ["o", 'x', '*', 'p', 'v', 'h', '+', '1', '3', 'd']
color_ku = ['royalblue', 'red', 'seagreen', 'darkorange', 'mediumpurple', 'sienna', 'darkcyan', 'slategray', 'orchid',
            'pink']

if task_number == 20:
    max_exe_time = 0.03

if task_number == 30:
    max_exe_time = 0.2

def cal_sys_uti(ts):
    sys_uLO = 0
    sys_uHI = 0
    task_set = task_set = ts.HI.union(ts.LO)
    for task in task_set:
        sys_uLO += task.uLO * task.node_number
        sys_uHI += task.uHI * task.node_number
    return sys_uLO, sys_uHI

def cal_schedulable(mapping_list, ts, wcrt_algor = amc_rtb_wcrt):
    if mapping_list == False:
        return 0
    return 1

def mapping_uti_exper():
    mapping_Algorithm = ['FF_DU','FF_DP','BF_DU','BF_DP','WF_DU','WF_DP','BF_FF_DP']
    #mapping_Algorithm = ['random','order','min_uti','FF_DU','FF_DP','BF_DU','BF_DP','WF_DU','WF_DP','WF_FF_DP']
    uti_list = []
    num_tries = {}
    exe_time = {}
    uti_number = 10
    for i in mapping_Algorithm:
        num_tries[i]=[0 for _ in range(uti_number)]
    for i in mapping_Algorithm:
        exe_time[i]=[0 for _ in range(uti_number)]
    cycle_index = 1000
    system_uti_start = 0.2
    system_uti_dis = 0.05
    for j in range(uti_number):
        system_uti = system_uti_start + system_uti_dis * j
        uti_list.append(system_uti)
        for i in tqdm(range(cycle_index), desc="Processing", unit="items", ncols=100):
            #任务集生成
            ts = Drs_gengerate(task_number, system_uti * node_number, 2, 0.5, node_number)
            task_set = ts.HI.union(ts.LO)
            ts.priority_assignment_DM_HI(task_set,0)
            '''
            #随机映射
            random_mapping_list = random_mapping(task_set)
            num_tries['random'][j] += cal_schedulable(random_mapping_list, ts)

            for task in task_set:
                task.reset()
            #顺序映射
            order_mapping_list = order_mapping(task_set)
            num_tries['order'][j] += cal_schedulable(order_mapping_list, ts)
            
            for task in task_set:
                task.reset()
            #最低利用率映射
            uti_mapping_list, _, _ = uti_mapping(task_set)
            num_tries['min_uti'][j] += cal_schedulable(uti_mapping_list, ts)

            for task in task_set:
                task.reset()
            '''
            #FF_DU
            # start_time1 = time.time()
            FF_DU_mapping_list = FF_DU(ts)
            num_tries['FF_DU'][j] += cal_schedulable(FF_DU_mapping_list, ts)
            # end_time1 = time.time()
            # if cal_schedulable(FF_DU_mapping_list, ts):
            #     exe_time['FF_DU'][j] += end_time1 - start_time1
            # else:
            #     exe_time['FF_DU'][j] += max_exe_time

            for task in task_set:
                task.reset()
            
            #FF_DP
            # start_time2 = time.time()
            FF_DP_mapping_list = FF_DP(ts)
            num_tries['FF_DP'][j] += cal_schedulable(FF_DP_mapping_list, ts)
            # end_time2 = time.time()
            # if cal_schedulable(FF_DP_mapping_list, ts):
            #     exe_time['FF_DP'][j] += end_time2 - start_time2
            # else:
            #     exe_time['FF_DP'][j] += max_exe_time

            for task in task_set:
                task.reset()
                
            #BF_DU
            # start_time3 = time.time()
            BF_DU_mapping_list = BF_DU(ts)
            num_tries['BF_DU'][j] += cal_schedulable(BF_DU_mapping_list, ts)
            # end_time3 = time.time()
            # if cal_schedulable(BF_DU_mapping_list, ts):
            #     exe_time['BF_DU'][j] += end_time3 - start_time3
            # else:
            #     exe_time['BF_DU'][j] += max_exe_time

            for task in task_set:
                task.reset()

            #BF_DP
            # start_time4 = time.time()
            BF_DP_mapping_list = BF_DP(ts)
            num_tries['BF_DP'][j] += cal_schedulable(BF_DP_mapping_list, ts)
            # end_time4 = time.time()
            # if cal_schedulable(BF_DP_mapping_list, ts):
            #     exe_time['BF_DP'][j] += end_time4 - start_time4
            # else:
            #     exe_time['BF_DP'][j] += max_exe_time

            for task in task_set:
                task.reset()
            
            #WF_DU
            # start_time5 = time.time()
            WF_DU_mapping_list = WF_DU(ts)
            num_tries['WF_DU'][j] += cal_schedulable(WF_DU_mapping_list, ts)
            # end_time5 = time.time()
            # if cal_schedulable(WF_DU_mapping_list, ts):
            #     exe_time['WF_DU'][j] += end_time5 - start_time5
            # else:
            #     exe_time['WF_DU'][j] += max_exe_time

            for task in task_set:
                task.reset()
            
            #WF_DP
            # start_time6 = time.time()
            WF_DP_mapping_list = WF_DP(ts)
            num_tries['WF_DP'][j] += cal_schedulable(WF_DP_mapping_list, ts)
            # end_time6 = time.time()
            # if cal_schedulable(WF_DP_mapping_list, ts):
            #     exe_time['WF_DP'][j] += end_time6 - start_time6
            # else:
            #     exe_time['WF_DP'][j] += max_exe_time

            for task in task_set:
                task.reset()
                       
            #BF_FF_DP
            # start_time7 = time.time()
            BF_FF_DP_mapping_list = BF_FF_DP(ts)
            num_tries['BF_FF_DP'][j] += cal_schedulable(BF_FF_DP_mapping_list, ts)
            # end_time7 = time.time()
            # if cal_schedulable(BF_FF_DP_mapping_list, ts):
            #     exe_time['BF_FF_DP'][j] += end_time7 - start_time7
            # else:
            #     exe_time['BF_FF_DP'][j] += max_exe_time
            
    
            
        '''
        print('系统利用率：'+ str(system_uti) + '  随机映射可调度率：' + str( num_tries['random'][j]) + '  顺序映射可调度率：' + str( num_tries['order'][j]) + \
                '  最低利用率映射可调度率：' + str(num_tries['min_uti'][j]) + '  FF_DU可调度率：' + str(num_tries['FF_DU'][j]) + '  FF_DP可调度率：' + str(num_tries['FF_DP'][j]) +\
                    '  BF_DU可调度率：' + str(num_tries['BF_DU'][j]) +'  BF_DP可调度率：' + str(num_tries['BF_DP'][j]) + '  WF_DU可调度率：' + str(num_tries['WF_DU'][j])\
                          + '  WF_DP可调度率：' + str(num_tries['WF_DP'][j]) + '  WF_FF_DP可调度率：' + str(num_tries['WF_FF_DP'][j]))
        '''
        print('系统利用率：'+ str(system_uti) + '  FF_DU可调度率：' + str(num_tries['FF_DU'][j]) + '  FF_DP可调度率：' + str(num_tries['FF_DP'][j]) +\
                    '  BF_DU可调度率：' + str(num_tries['BF_DU'][j]) +'  BF_DP可调度率：' + str(num_tries['BF_DP'][j]) + '  WF_DU可调度率：' + str(num_tries['WF_DU'][j])\
                          + '  WF_DP可调度率：' + str(num_tries['WF_DP'][j]) + '  BF_FF_DP可调度率：' + str(num_tries['BF_FF_DP'][j]))
        
        # print('系统利用率：'+ str(system_uti) + '  FF_DU总时间：' + str(exe_time['FF_DU'][j]) + '  FF_DP总时间：' + str(exe_time['FF_DP'][j]) +\
        #             '  BF_DU总时间：' + str(exe_time['BF_DU'][j]) +'  BF_DP总时间：' + str(exe_time['BF_DP'][j]) + '  WF_DU总时间：' + str(exe_time['WF_DU'][j])\
        #                   + '  WF_DP总时间：' + str(exe_time['WF_DP'][j]) + '  BF_FF_DP总时间：' + str(exe_time['BF_FF_DP'][j]))
        

    
    # plt.figure()
    # xx = -1
    # for i in mapping_Algorithm:
    #     xx += 1
    #     if i not in num_tries:continue
    #     schedulable = []
    #     for x in num_tries[i]:
    #         if x!=None: schedulable.append(float(x) / cycle_index * 100)
    #     plt.plot(uti_list, schedulable, linewidth=1, linestyle='-.',color= color_ku[xx%len(color_ku)], marker=marker_ku[xx % len(marker_ku)], label= i)
    # plt.ylabel('任务集的可调度率',size = FigWordSize)
    # plt.xlabel('系统在低关键度模式下的利用率',size = FigWordSize)
    # plt.xlim(system_uti_start-0.01, system_uti_start + system_uti_dis * (uti_number - 1) + 0.01)
    # # plt.ylim(-12, 104)
    # plt.xticks(fontproperties = 'Times New Roman', size = FigWordSize)
    # plt.yticks(fontproperties='Times New Roman', size=FigWordSize)
    # plt.legend(fontsize=FigWordSize)
    # #plt.title("per-processor utilization")pdf
    # plt.savefig('./result/mapping_LO_uti_%d_%d.png'%(cluster_col, task_number),bbox_inches = 'tight')
    # plt.savefig('./result/mapping_LO_uti_%d_%d.pdf'%(cluster_col, task_number),bbox_inches = 'tight')
    # plt.savefig('./result/mapping_LO_uti_%d_%d.svg'%(cluster_col, task_number),format='svg',bbox_inches = 'tight')
    # plt.show()

    # 颜色映射：为每种主要算法分配固定颜色
    color_map = {
        'FF': 'royalblue',
        'BF': 'seagreen',
        'WF': 'darkorange',
        'BF_FF': 'mediumpurple'
    }

    marker_map = {
        'FF': 'o',
        'BF': 's',
        'WF': '^',
        'BF_FF': 'D'
    }

    # 线型映射：DU用虚线，DP用实线
    linestyle_map = {
        'DU': '--',
        'DP': '-'
    }

    df = pd.DataFrame(num_tries)
    #df[mapping_Algorithm] = df[mapping_Algorithm]/1000
    df.to_excel("LO_uti_20.xlsx", index=False)
    if task_number == 20:
        df.to_excel("LO_uti_20.xlsx", index=False)
    else:
        df.to_excel("LO_uti_30.xlsx", index=False)
    plt.figure()
    for i in mapping_Algorithm:
        if i not in num_tries:
            continue

        # 拆分算法名称
        parts = i.split('_')
        main_alg = '_'.join(parts[:-1]) if len(parts) > 2 else parts[0]
        mode = parts[-1]  # DU 或 DP

        schedulable = [float(x) / cycle_index * 100 for x in num_tries[i] if x is not None]

        plt.plot(
            uti_list,
            schedulable,
            linewidth=1.5,
            linestyle=linestyle_map.get(mode, '-'),
            color=color_map.get(main_alg, 'gray'),
            marker=marker_map.get(main_alg, 'o'),
            label=i
        )

    plt.ylabel('Task Schedulability Ratio', size=FigWordSize)
    plt.xlabel('System Low-Criticality Utilization Level', size=FigWordSize)
    plt.xlim(system_uti_start - 0.01, system_uti_start + system_uti_dis * (uti_number - 1) + 0.01)
    plt.xticks(fontproperties='Times New Roman', size=FigWordSize)
    plt.yticks(fontproperties='Times New Roman', size=FigWordSize)
    plt.legend(fontsize=FigWordSize)
    plt.savefig(f'./result/mapping_LO_uti_{cluster_col}_{task_number}.png', bbox_inches='tight')
    plt.savefig(f'./result/mapping_LO_uti_{cluster_col}_{task_number}.pdf', bbox_inches='tight')
    plt.savefig(f'./result/mapping_LO_uti_{cluster_col}_{task_number}.svg', format='svg', bbox_inches='tight')
    plt.show()
    # plt.figure()
    # xx = -1
    # for i in mapping_Algorithm:
    #     xx += 1
    #     if i not in exe_time:continue
    #     schedulable = []
    #     for x in exe_time[i]:
    #         if x!=None: schedulable.append(float(x) / cycle_index)
    #     plt.plot(uti_list, schedulable, linewidth=1, linestyle='-.',color= color_ku[xx%len(color_ku)], marker=marker_ku[xx % len(marker_ku)], label= i)
    # plt.ylabel('算法所用时间',size = FigWordSize)
    # plt.xlabel('系统在低关键度模式下的利用率',size = FigWordSize)
    # plt.xlim(system_uti_start-0.01, system_uti_start + system_uti_dis * (uti_number - 1) + 0.01)
    # # plt.ylim(-12, 104)
    # plt.xticks(fontproperties = 'Times New Roman', size = FigWordSize)
    # plt.yticks(fontproperties='Times New Roman', size=FigWordSize)
    # plt.legend(fontsize=FigWordSize)
    # #plt.title("per-processor utilization")pdf
    # plt.savefig('./result/mapping_LO_uti_time_%d_%d.png'%(cluster_col, task_number),bbox_inches = 'tight')
    # plt.savefig('./result/mapping_LO_uti_time_%d_%d.pdf'%(cluster_col, task_number),bbox_inches = 'tight')
    # plt.savefig('./result/mapping_LO_uti_time_%d_%d.svg'%(cluster_col, task_number),format='svg',bbox_inches = 'tight')
    # plt.show()

def mapping_CP_exper():
    mapping_Algorithm = ['FF_DU', 'FF_DP', 'BF_DU', 'BF_DP', 'WF_DU', 'WF_DP', 'BF_FF_DP']
    # mapping_Algorithm = ['random','order','min_uti','FF_DU','FF_DP','BF_DU','BF_DP','WF_DU','WF_DP','WF_FF_DP']
    uti_list = []
    num_tries = {}
    exe_time = {}
    uti_number = 9
    for i in mapping_Algorithm:
        num_tries[i] = [0 for _ in range(uti_number)]
    for i in mapping_Algorithm:
        exe_time[i] = [0 for _ in range(uti_number)]
    cycle_index = 1000
    system_CP_start = 0.3
    system_CP_dis = 0.05
    for j in range(uti_number):
        system_CP = system_CP_start + system_CP_dis * j
        uti_list.append(system_CP)
        for i in tqdm(range(cycle_index), desc="Processing", unit="items", ncols=100):
            # 任务集生成
            ts = Drs_gengerate(task_number, 0.4 * node_number, 2, system_CP, node_number)
            task_set = ts.HI.union(ts.LO)
            ts.priority_assignment_DM_HI(task_set, 0)
            '''
            #随机映射
            random_mapping_list = random_mapping(task_set)
            num_tries['random'][j] += cal_schedulable(random_mapping_list, ts)

            for task in task_set:
                task.reset()
            #顺序映射
            order_mapping_list = order_mapping(task_set)
            num_tries['order'][j] += cal_schedulable(order_mapping_list, ts)

            for task in task_set:
                task.reset()
            #最低利用率映射
            uti_mapping_list, _, _ = uti_mapping(task_set)
            num_tries['min_uti'][j] += cal_schedulable(uti_mapping_list, ts)

            for task in task_set:
                task.reset()
            '''
            # FF_DU
            # start_time1 = time.time()
            FF_DU_mapping_list = FF_DU(ts)
            num_tries['FF_DU'][j] += cal_schedulable(FF_DU_mapping_list, ts)
            # end_time1 = time.time()
            # if cal_schedulable(FF_DU_mapping_list, ts):
            #     exe_time['FF_DU'][j] += end_time1 - start_time1
            # else:
            #     exe_time['FF_DU'][j] += max_exe_time

            for task in task_set:
                task.reset()

            # FF_DP
            # start_time2 = time.time()
            FF_DP_mapping_list = FF_DP(ts)
            num_tries['FF_DP'][j] += cal_schedulable(FF_DP_mapping_list, ts)
            # end_time2 = time.time()
            # if cal_schedulable(FF_DP_mapping_list, ts):
            #     exe_time['FF_DP'][j] += end_time2 - start_time2
            # else:
            #     exe_time['FF_DP'][j] += max_exe_time

            for task in task_set:
                task.reset()

            # BF_DU
            # start_time3 = time.time()
            BF_DU_mapping_list = BF_DU(ts)
            num_tries['BF_DU'][j] += cal_schedulable(BF_DU_mapping_list, ts)
            # end_time3 = time.time()
            # if cal_schedulable(BF_DU_mapping_list, ts):
            #     exe_time['BF_DU'][j] += end_time3 - start_time3
            # else:
            #     exe_time['BF_DU'][j] += max_exe_time

            for task in task_set:
                task.reset()

            # BF_DP
            # start_time4 = time.time()
            BF_DP_mapping_list = BF_DP(ts)
            num_tries['BF_DP'][j] += cal_schedulable(BF_DP_mapping_list, ts)
            # end_time4 = time.time()
            # if cal_schedulable(BF_DP_mapping_list, ts):
            #     exe_time['BF_DP'][j] += end_time4 - start_time4
            # else:
            #     exe_time['BF_DP'][j] += max_exe_time

            for task in task_set:
                task.reset()

            # WF_DU
            # start_time5 = time.time()
            WF_DU_mapping_list = WF_DU(ts)
            num_tries['WF_DU'][j] += cal_schedulable(WF_DU_mapping_list, ts)
            # end_time5 = time.time()
            # if cal_schedulable(WF_DU_mapping_list, ts):
            #     exe_time['WF_DU'][j] += end_time5 - start_time5
            # else:
            #     exe_time['WF_DU'][j] += max_exe_time

            for task in task_set:
                task.reset()

            # WF_DP
            # start_time6 = time.time()
            WF_DP_mapping_list = WF_DP(ts)
            num_tries['WF_DP'][j] += cal_schedulable(WF_DP_mapping_list, ts)
            # end_time6 = time.time()
            # if cal_schedulable(WF_DP_mapping_list, ts):
            #     exe_time['WF_DP'][j] += end_time6 - start_time6
            # else:
            #     exe_time['WF_DP'][j] += max_exe_time

            for task in task_set:
                task.reset()

            # BF_FF_DP
            # start_time7 = time.time()
            BF_FF_DP_mapping_list = BF_FF_DP(ts)
            num_tries['BF_FF_DP'][j] += cal_schedulable(BF_FF_DP_mapping_list, ts)
            # end_time7 = time.time()
            # if cal_schedulable(BF_FF_DP_mapping_list, ts):
            #     exe_time['BF_FF_DP'][j] += end_time7 - start_time7
            # else:
            #     exe_time['BF_FF_DP'][j] += max_exe_time

        '''
        print('系统利用率：'+ str(system_uti) + '  随机映射可调度率：' + str( num_tries['random'][j]) + '  顺序映射可调度率：' + str( num_tries['order'][j]) + \
                '  最低利用率映射可调度率：' + str(num_tries['min_uti'][j]) + '  FF_DU可调度率：' + str(num_tries['FF_DU'][j]) + '  FF_DP可调度率：' + str(num_tries['FF_DP'][j]) +\
                    '  BF_DU可调度率：' + str(num_tries['BF_DU'][j]) +'  BF_DP可调度率：' + str(num_tries['BF_DP'][j]) + '  WF_DU可调度率：' + str(num_tries['WF_DU'][j])\
                          + '  WF_DP可调度率：' + str(num_tries['WF_DP'][j]) + '  WF_FF_DP可调度率：' + str(num_tries['WF_FF_DP'][j]))
        '''
        print('系统利用率：' + str(system_CP) + '  FF_DU可调度率：' + str(
            num_tries['FF_DU'][j]) + '  FF_DP可调度率：' + str(num_tries['FF_DP'][j]) + \
              '  BF_DU可调度率：' + str(num_tries['BF_DU'][j]) + '  BF_DP可调度率：' + str(
            num_tries['BF_DP'][j]) + '  WF_DU可调度率：' + str(num_tries['WF_DU'][j]) \
              + '  WF_DP可调度率：' + str(num_tries['WF_DP'][j]) + '  BF_FF_DP可调度率：' + str(num_tries['BF_FF_DP'][j]))

        # print('系统利用率：'+ str(system_uti) + '  FF_DU总时间：' + str(exe_time['FF_DU'][j]) + '  FF_DP总时间：' + str(exe_time['FF_DP'][j]) +\
        #             '  BF_DU总时间：' + str(exe_time['BF_DU'][j]) +'  BF_DP总时间：' + str(exe_time['BF_DP'][j]) + '  WF_DU总时间：' + str(exe_time['WF_DU'][j])\
        #                   + '  WF_DP总时间：' + str(exe_time['WF_DP'][j]) + '  BF_FF_DP总时间：' + str(exe_time['BF_FF_DP'][j]))

    # plt.figure()
    # xx = -1
    # for i in mapping_Algorithm:
    #     xx += 1
    #     if i not in num_tries:continue
    #     schedulable = []
    #     for x in num_tries[i]:
    #         if x!=None: schedulable.append(float(x) / cycle_index * 100)
    #     plt.plot(uti_list, schedulable, linewidth=1, linestyle='-.',color= color_ku[xx%len(color_ku)], marker=marker_ku[xx % len(marker_ku)], label= i)
    # plt.ylabel('任务集的可调度率',size = FigWordSize)
    # plt.xlabel('系统在低关键度模式下的利用率',size = FigWordSize)
    # plt.xlim(system_uti_start-0.01, system_uti_start + system_uti_dis * (uti_number - 1) + 0.01)
    # # plt.ylim(-12, 104)
    # plt.xticks(fontproperties = 'Times New Roman', size = FigWordSize)
    # plt.yticks(fontproperties='Times New Roman', size=FigWordSize)
    # plt.legend(fontsize=FigWordSize)
    # #plt.title("per-processor utilization")pdf
    # plt.savefig('./result/mapping_LO_uti_%d_%d.png'%(cluster_col, task_number),bbox_inches = 'tight')
    # plt.savefig('./result/mapping_LO_uti_%d_%d.pdf'%(cluster_col, task_number),bbox_inches = 'tight')
    # plt.savefig('./result/mapping_LO_uti_%d_%d.svg'%(cluster_col, task_number),format='svg',bbox_inches = 'tight')
    # plt.show()

    # 颜色映射：为每种主要算法分配固定颜色
    color_map = {
        'FF': 'royalblue',
        'BF': 'seagreen',
        'WF': 'darkorange',
        'BF_FF': 'mediumpurple'
    }

    # 线型映射：DU用虚线，DP用实线
    linestyle_map = {
        'DU': '--',
        'DP': '-'
    }

    marker_map = {
        'FF': 'o',
        'BF': 's',
        'WF': '^',
        'BF_FF': 'D'
    }

    df = pd.DataFrame(num_tries)
    df.to_excel("CP_20.xlsx", index=False)
    #df[mapping_Algorithm] = df[mapping_Algorithm]/1000
    if task_number == 20:
        df.to_excel("CP_20.xlsx", index=False)
    else:
        df.to_excel("CP_30.xlsx", index=False)
    plt.figure()
    for i in mapping_Algorithm:
        if i not in num_tries:
            continue

        # 拆分算法名称
        parts = i.split('_')
        main_alg = '_'.join(parts[:-1]) if len(parts) > 2 else parts[0]
        mode = parts[-1]  # DU 或 DP

        schedulable = [float(x) / cycle_index * 100 for x in num_tries[i] if x is not None]

        plt.plot(
            uti_list,
            schedulable,
            linewidth=1.5,
            linestyle=linestyle_map.get(mode, '-'),
            color=color_map.get(main_alg, 'gray'),
            marker=marker_map.get(main_alg, 'o'),
            label=i
        )

    plt.ylabel('Task Schedulability Ratio', size=FigWordSize)
    plt.xlabel('CP', size=FigWordSize)
    plt.xlim(system_CP_start - 0.01, system_CP_start + system_CP_dis * (uti_number - 1) + 0.01)
    plt.xticks(fontproperties='Times New Roman', size=FigWordSize)
    plt.yticks(fontproperties='Times New Roman', size=FigWordSize)
    plt.legend(fontsize=FigWordSize)
    plt.savefig(f'./result/mapping_CP_{cluster_col}_{task_number}.png', bbox_inches='tight')
    plt.savefig(f'./result/mapping_CP_{cluster_col}_{task_number}.pdf', bbox_inches='tight')
    plt.savefig(f'./result/mapping_CP_{cluster_col}_{task_number}.svg', format='svg', bbox_inches='tight')
    plt.show()
    # plt.figure()
    # xx = -1
    # for i in mapping_Algorithm:
    #     xx += 1
    #     if i not in exe_time:continue
    #     schedulable = []
    #     for x in exe_time[i]:
    #         if x!=None: schedulable.append(float(x) / cycle_index)
    #     plt.plot(uti_list, schedulable, linewidth=1, linestyle='-.',color= color_ku[xx%len(color_ku)], marker=marker_ku[xx % len(marker_ku)], label= i)
    # plt.ylabel('算法所用时间',size = FigWordSize)
    # plt.xlabel('系统在低关键度模式下的利用率',size = FigWordSize)
    # plt.xlim(system_uti_start-0.01, system_uti_start + system_uti_dis * (uti_number - 1) + 0.01)
    # # plt.ylim(-12, 104)
    # plt.xticks(fontproperties = 'Times New Roman', size = FigWordSize)
    # plt.yticks(fontproperties='Times New Roman', size=FigWordSize)
    # plt.legend(fontsize=FigWordSize)
    # #plt.title("per-processor utilization")pdf
    # plt.savefig('./result/mapping_LO_uti_time_%d_%d.png'%(cluster_col, task_number),bbox_inches = 'tight')
    # plt.savefig('./result/mapping_LO_uti_time_%d_%d.pdf'%(cluster_col, task_number),bbox_inches = 'tight')
    # plt.savefig('./result/mapping_LO_uti_time_%d_%d.svg'%(cluster_col, task_number),format='svg',bbox_inches = 'tight')
    # plt.show()

def mapping_CF_exper():
    mapping_Algorithm = ['FF_DU', 'FF_DP', 'BF_DU', 'BF_DP', 'WF_DU', 'WF_DP', 'BF_FF_DP']
    # mapping_Algorithm = ['random','order','min_uti','FF_DU','FF_DP','BF_DU','BF_DP','WF_DU','WF_DP','WF_FF_DP']
    uti_list = []
    num_tries = {}
    exe_time = {}
    uti_number = 10
    for i in mapping_Algorithm:
        num_tries[i] = [0 for _ in range(uti_number)]
    for i in mapping_Algorithm:
        exe_time[i] = [0 for _ in range(uti_number)]
    cycle_index = 1000
    system_CF_start = 1.5
    system_CF_dis = 0.1
    for j in range(uti_number):
        system_CF = system_CF_start + system_CF_dis * j
        uti_list.append(system_CF)
        for i in tqdm(range(cycle_index), desc="Processing", unit="items", ncols=100):
            # 任务集生成
            ts = Drs_gengerate(task_number, 0.4 * node_number, system_CF, 0.5, node_number)
            task_set = ts.HI.union(ts.LO)
            ts.priority_assignment_DM_HI(task_set, 0)
            '''
            #随机映射
            random_mapping_list = random_mapping(task_set)
            num_tries['random'][j] += cal_schedulable(random_mapping_list, ts)

            for task in task_set:
                task.reset()
            #顺序映射
            order_mapping_list = order_mapping(task_set)
            num_tries['order'][j] += cal_schedulable(order_mapping_list, ts)

            for task in task_set:
                task.reset()
            #最低利用率映射
            uti_mapping_list, _, _ = uti_mapping(task_set)
            num_tries['min_uti'][j] += cal_schedulable(uti_mapping_list, ts)

            for task in task_set:
                task.reset()
            '''
            # FF_DU
            # start_time1 = time.time()
            FF_DU_mapping_list = FF_DU(ts)
            num_tries['FF_DU'][j] += cal_schedulable(FF_DU_mapping_list, ts)
            # end_time1 = time.time()
            # if cal_schedulable(FF_DU_mapping_list, ts):
            #     exe_time['FF_DU'][j] += end_time1 - start_time1
            # else:
            #     exe_time['FF_DU'][j] += max_exe_time

            for task in task_set:
                task.reset()

            # FF_DP
            # start_time2 = time.time()
            FF_DP_mapping_list = FF_DP(ts)
            num_tries['FF_DP'][j] += cal_schedulable(FF_DP_mapping_list, ts)
            # end_time2 = time.time()
            # if cal_schedulable(FF_DP_mapping_list, ts):
            #     exe_time['FF_DP'][j] += end_time2 - start_time2
            # else:
            #     exe_time['FF_DP'][j] += max_exe_time

            for task in task_set:
                task.reset()

            # BF_DU
            # start_time3 = time.time()
            BF_DU_mapping_list = BF_DU(ts)
            num_tries['BF_DU'][j] += cal_schedulable(BF_DU_mapping_list, ts)
            # end_time3 = time.time()
            # if cal_schedulable(BF_DU_mapping_list, ts):
            #     exe_time['BF_DU'][j] += end_time3 - start_time3
            # else:
            #     exe_time['BF_DU'][j] += max_exe_time

            for task in task_set:
                task.reset()

            # BF_DP
            # start_time4 = time.time()
            BF_DP_mapping_list = BF_DP(ts)
            num_tries['BF_DP'][j] += cal_schedulable(BF_DP_mapping_list, ts)
            # end_time4 = time.time()
            # if cal_schedulable(BF_DP_mapping_list, ts):
            #     exe_time['BF_DP'][j] += end_time4 - start_time4
            # else:
            #     exe_time['BF_DP'][j] += max_exe_time

            for task in task_set:
                task.reset()

            # WF_DU
            # start_time5 = time.time()
            WF_DU_mapping_list = WF_DU(ts)
            num_tries['WF_DU'][j] += cal_schedulable(WF_DU_mapping_list, ts)
            # end_time5 = time.time()
            # if cal_schedulable(WF_DU_mapping_list, ts):
            #     exe_time['WF_DU'][j] += end_time5 - start_time5
            # else:
            #     exe_time['WF_DU'][j] += max_exe_time

            for task in task_set:
                task.reset()

            # WF_DP
            # start_time6 = time.time()
            WF_DP_mapping_list = WF_DP(ts)
            num_tries['WF_DP'][j] += cal_schedulable(WF_DP_mapping_list, ts)
            # end_time6 = time.time()
            # if cal_schedulable(WF_DP_mapping_list, ts):
            #     exe_time['WF_DP'][j] += end_time6 - start_time6
            # else:
            #     exe_time['WF_DP'][j] += max_exe_time

            for task in task_set:
                task.reset()

            # BF_FF_DP
            # start_time7 = time.time()
            BF_FF_DP_mapping_list = BF_FF_DP(ts)
            num_tries['BF_FF_DP'][j] += cal_schedulable(BF_FF_DP_mapping_list, ts)
            # end_time7 = time.time()
            # if cal_schedulable(BF_FF_DP_mapping_list, ts):
            #     exe_time['BF_FF_DP'][j] += end_time7 - start_time7
            # else:
            #     exe_time['BF_FF_DP'][j] += max_exe_time

        '''
        print('系统利用率：'+ str(system_uti) + '  随机映射可调度率：' + str( num_tries['random'][j]) + '  顺序映射可调度率：' + str( num_tries['order'][j]) + \
                '  最低利用率映射可调度率：' + str(num_tries['min_uti'][j]) + '  FF_DU可调度率：' + str(num_tries['FF_DU'][j]) + '  FF_DP可调度率：' + str(num_tries['FF_DP'][j]) +\
                    '  BF_DU可调度率：' + str(num_tries['BF_DU'][j]) +'  BF_DP可调度率：' + str(num_tries['BF_DP'][j]) + '  WF_DU可调度率：' + str(num_tries['WF_DU'][j])\
                          + '  WF_DP可调度率：' + str(num_tries['WF_DP'][j]) + '  WF_FF_DP可调度率：' + str(num_tries['WF_FF_DP'][j]))
        '''
        print('系统利用率：' + str(system_CF) + '  FF_DU可调度率：' + str(
            num_tries['FF_DU'][j]) + '  FF_DP可调度率：' + str(num_tries['FF_DP'][j]) + \
              '  BF_DU可调度率：' + str(num_tries['BF_DU'][j]) + '  BF_DP可调度率：' + str(
            num_tries['BF_DP'][j]) + '  WF_DU可调度率：' + str(num_tries['WF_DU'][j]) \
              + '  WF_DP可调度率：' + str(num_tries['WF_DP'][j]) + '  BF_FF_DP可调度率：' + str(num_tries['BF_FF_DP'][j]))

        # print('系统利用率：'+ str(system_uti) + '  FF_DU总时间：' + str(exe_time['FF_DU'][j]) + '  FF_DP总时间：' + str(exe_time['FF_DP'][j]) +\
        #             '  BF_DU总时间：' + str(exe_time['BF_DU'][j]) +'  BF_DP总时间：' + str(exe_time['BF_DP'][j]) + '  WF_DU总时间：' + str(exe_time['WF_DU'][j])\
        #                   + '  WF_DP总时间：' + str(exe_time['WF_DP'][j]) + '  BF_FF_DP总时间：' + str(exe_time['BF_FF_DP'][j]))

    # plt.figure()
    # xx = -1
    # for i in mapping_Algorithm:
    #     xx += 1
    #     if i not in num_tries:continue
    #     schedulable = []
    #     for x in num_tries[i]:
    #         if x!=None: schedulable.append(float(x) / cycle_index * 100)
    #     plt.plot(uti_list, schedulable, linewidth=1, linestyle='-.',color= color_ku[xx%len(color_ku)], marker=marker_ku[xx % len(marker_ku)], label= i)
    # plt.ylabel('任务集的可调度率',size = FigWordSize)
    # plt.xlabel('系统在低关键度模式下的利用率',size = FigWordSize)
    # plt.xlim(system_uti_start-0.01, system_uti_start + system_uti_dis * (uti_number - 1) + 0.01)
    # # plt.ylim(-12, 104)
    # plt.xticks(fontproperties = 'Times New Roman', size = FigWordSize)
    # plt.yticks(fontproperties='Times New Roman', size=FigWordSize)
    # plt.legend(fontsize=FigWordSize)
    # #plt.title("per-processor utilization")pdf
    # plt.savefig('./result/mapping_LO_uti_%d_%d.png'%(cluster_col, task_number),bbox_inches = 'tight')
    # plt.savefig('./result/mapping_LO_uti_%d_%d.pdf'%(cluster_col, task_number),bbox_inches = 'tight')
    # plt.savefig('./result/mapping_LO_uti_%d_%d.svg'%(cluster_col, task_number),format='svg',bbox_inches = 'tight')
    # plt.show()

    # 颜色映射：为每种主要算法分配固定颜色
    color_map = {
        'FF': 'royalblue',
        'BF': 'seagreen',
        'WF': 'darkorange',
        'BF_FF': 'mediumpurple'
    }

    # 线型映射：DU用虚线，DP用实线
    linestyle_map = {
        'DU': '--',
        'DP': '-'
    }

    marker_map = {
        'FF': 'o',
        'BF': 's',
        'WF': '^',
        'BF_FF': 'D'
    }

    df = pd.DataFrame(num_tries)
    df.to_excel("CF_20.xlsx", index=False)
    #df[mapping_Algorithm] = df[mapping_Algorithm]/1000
    if task_number == 20:
        df.to_excel("CF_20.xlsx", index=False)
    else:
        df.to_excel("CF_30.xlsx", index=False)
    plt.figure()
    for i in mapping_Algorithm:
        if i not in num_tries:
            continue

        # 拆分算法名称
        parts = i.split('_')
        main_alg = '_'.join(parts[:-1]) if len(parts) > 2 else parts[0]
        mode = parts[-1]  # DU 或 DP

        schedulable = [float(x) / cycle_index * 100 for x in num_tries[i] if x is not None]

        plt.plot(
            uti_list,
            schedulable,
            linewidth=1.5,
            linestyle=linestyle_map.get(mode, '-'),
            color=color_map.get(main_alg, 'gray'),
            marker=marker_map.get(main_alg, 'o'),
            label=i
        )

    plt.ylabel('Task Schedulability Ratio', size=FigWordSize)
    plt.xlabel('CF', size=FigWordSize)
    plt.xlim(system_CF_start - 0.01, system_CF_start + system_CF_dis * (uti_number - 1) + 0.01)
    plt.xticks(fontproperties='Times New Roman', size=FigWordSize)
    plt.yticks(fontproperties='Times New Roman', size=FigWordSize)
    plt.legend(fontsize=FigWordSize)
    plt.savefig(f'./result/mapping_CF_{cluster_col}_{task_number}.png', bbox_inches='tight')
    plt.savefig(f'./result/mapping_CF_{cluster_col}_{task_number}.pdf', bbox_inches='tight')
    plt.savefig(f'./result/mapping_CF_{cluster_col}_{task_number}.svg', format='svg', bbox_inches='tight')
    plt.show()
    # plt.figure()
    # xx = -1
    # for i in mapping_Algorithm:
    #     xx += 1
    #     if i not in exe_time:continue
    #     schedulable = []
    #     for x in exe_time[i]:
    #         if x!=None: schedulable.append(float(x) / cycle_index)
    #     plt.plot(uti_list, schedulable, linewidth=1, linestyle='-.',color= color_ku[xx%len(color_ku)], marker=marker_ku[xx % len(marker_ku)], label= i)
    # plt.ylabel('算法所用时间',size = FigWordSize)
    # plt.xlabel('系统在低关键度模式下的利用率',size = FigWordSize)
    # plt.xlim(system_uti_start-0.01, system_uti_start + system_uti_dis * (uti_number - 1) + 0.01)
    # # plt.ylim(-12, 104)
    # plt.xticks(fontproperties = 'Times New Roman', size = FigWordSize)
    # plt.yticks(fontproperties='Times New Roman', size=FigWordSize)
    # plt.legend(fontsize=FigWordSize)
    # #plt.title("per-processor utilization")pdf
    # plt.savefig('./result/mapping_LO_uti_time_%d_%d.png'%(cluster_col, task_number),bbox_inches = 'tight')
    # plt.savefig('./result/mapping_LO_uti_time_%d_%d.pdf'%(cluster_col, task_number),bbox_inches = 'tight')
    # plt.savefig('./result/mapping_LO_uti_time_%d_%d.svg'%(cluster_col, task_number),format='svg',bbox_inches = 'tight')
    # plt.show()

def mapping_uti_exper_time():
    mapping_Algorithm = ['FF_DU','FF_DP','BF_DU','BF_DP','WF_DU','WF_DP','BF_FF_DP']
    uti_list = []
    exe_time = {}
    uti_number = 6
    for i in mapping_Algorithm:
        exe_time[i]=[0 for _ in range(uti_number)]
    all_schedulable = [0 for _ in range(uti_number)]
    cycle_index = 1000
    system_uti_start = 0.1
    system_uti_dis = 0.05
    for j in range(uti_number):
        system_uti = system_uti_start + system_uti_dis * j
        uti_list.append(system_uti)
        for i in tqdm(range(cycle_index), desc="Processing", unit="items", ncols=100):
            #任务集生成
            ts = Drs_gengerate(task_number, system_uti * node_number, 2, 0.5, node_number)
            task_set = ts.HI.union(ts.LO)
            ts.priority_assignment_DM_HI(task_set,0)

            flag = 1

            #FF_DU
            start_time1 = time.time()
            FF_DU_mapping_list = FF_DU(ts)
            end_time1 = time.time()
            time1 = end_time1 - start_time1
            if not cal_schedulable(FF_DU_mapping_list, ts):
                flag = 0

            for task in task_set:
                task.reset()
            
            #FF_DP
            start_time2 = time.time()
            FF_DP_mapping_list = FF_DP(ts)
            end_time2 = time.time()
            time2 = end_time2 - start_time2
            if not cal_schedulable(FF_DP_mapping_list, ts):
                flag = 0

            for task in task_set:
                task.reset()
                
            #BF_DU
            start_time3 = time.time()
            BF_DU_mapping_list = BF_DU(ts)
            end_time3 = time.time()
            time3 = end_time3 - start_time3
            if not cal_schedulable(BF_DU_mapping_list, ts):
                flag = 0
            
            for task in task_set:
                task.reset()

            #BF_DP
            start_time4 = time.time()
            BF_DP_mapping_list = BF_DP(ts)
            end_time4 = time.time()
            time4 = end_time4 - start_time4
            if not cal_schedulable(BF_DP_mapping_list, ts):
                flag = 0

            for task in task_set:
                task.reset()
            
            #WF_DU
            start_time5 = time.time()
            WF_DU_mapping_list = WF_DU(ts)
            end_time5 = time.time()
            time5 = end_time5 - start_time5
            if not cal_schedulable(WF_DU_mapping_list, ts):
                flag = 0

            for task in task_set:
                task.reset()
            
            #WF_DP
            start_time6 = time.time()
            WF_DP_mapping_list = WF_DP(ts)
            end_time6 = time.time()
            time6 = end_time6 - start_time6
            if not cal_schedulable(WF_DP_mapping_list, ts):
                flag = 0

            for task in task_set:
                task.reset()
            
            #BF_FF_DP
            start_time7 = time.time()
            BF_FF_DP_mapping_list = BF_FF_DP(ts)
            end_time7 = time.time()
            time7 = end_time7 - start_time7
            if not cal_schedulable(BF_FF_DP_mapping_list, ts):
                flag = 0
            
            if flag:
                exe_time['FF_DU'][j] += time1
                exe_time['FF_DP'][j] += time2
                exe_time['BF_DU'][j] += time3
                exe_time['BF_DP'][j] += time4
                exe_time['WF_DU'][j] += time5
                exe_time['WF_DP'][j] += time6
                exe_time['BF_FF_DP'][j] += time7
                all_schedulable[j] += 1

            
    
            
        '''
        print('系统利用率：'+ str(system_uti) + '  随机映射可调度率：' + str( num_tries['random'][j]) + '  顺序映射可调度率：' + str( num_tries['order'][j]) + \
                '  最低利用率映射可调度率：' + str(num_tries['min_uti'][j]) + '  FF_DU可调度率：' + str(num_tries['FF_DU'][j]) + '  FF_DP可调度率：' + str(num_tries['FF_DP'][j]) +\
                    '  BF_DU可调度率：' + str(num_tries['BF_DU'][j]) +'  BF_DP可调度率：' + str(num_tries['BF_DP'][j]) + '  WF_DU可调度率：' + str(num_tries['WF_DU'][j])\
                          + '  WF_DP可调度率：' + str(num_tries['WF_DP'][j]) + '  WF_FF_DP可调度率：' + str(num_tries['WF_FF_DP'][j]))
        '''
        # print('系统利用率：'+ str(system_uti) + '  FF_DU可调度率：' + str(num_tries['FF_DU'][j]) + '  FF_DP可调度率：' + str(num_tries['FF_DP'][j]) +\
        #             '  BF_DU可调度率：' + str(num_tries['BF_DU'][j]) +'  BF_DP可调度率：' + str(num_tries['BF_DP'][j]) + '  WF_DU可调度率：' + str(num_tries['WF_DU'][j])\
        #                   + '  WF_DP可调度率：' + str(num_tries['WF_DP'][j]) + '  BF_FF_DP可调度率：' + str(num_tries['BF_FF_DP'][j]))
        
        print('系统利用率：'+ str(system_uti) + '  FF_DU总时间：' + str(exe_time['FF_DU'][j]) + '  FF_DP总时间：' + str(exe_time['FF_DP'][j]) +\
                    '  BF_DU总时间：' + str(exe_time['BF_DU'][j]) +'  BF_DP总时间：' + str(exe_time['BF_DP'][j]) + '  WF_DU总时间：' + str(exe_time['WF_DU'][j])\
                          + '  WF_DP总时间：' + str(exe_time['WF_DP'][j]) + '  BF_FF_DP总时间：' + str(exe_time['BF_FF_DP'][j]) +  '  都可调度次数：' + str(all_schedulable[j]))

    plt.figure()
    xx = -1
    for i in mapping_Algorithm:
        xx += 1
        if i not in exe_time:continue
        schedulable = []
        for j in range(uti_number):
            if exe_time[i][j]!=None: schedulable.append(float(exe_time[i][j]) / all_schedulable[j])
        plt.plot(uti_list, schedulable, linewidth=1, linestyle='-.',color= color_ku[xx%len(color_ku)], marker=marker_ku[xx % len(marker_ku)], label= i)
    plt.ylabel('算法所用时间',size = FigWordSize)
    plt.xlabel('系统在低关键度模式下的利用率',size = FigWordSize)
    plt.xlim(system_uti_start-0.01, system_uti_start + system_uti_dis * (uti_number - 1) + 0.01)
    # plt.ylim(-12, 104)
    plt.xticks(fontproperties = 'Times New Roman', size = FigWordSize)
    plt.yticks(fontproperties='Times New Roman', size=FigWordSize)
    plt.legend(fontsize=FigWordSize)
    #plt.title("per-processor utilization")pdf
    plt.savefig('./result/mapping_LO_uti_time_%d_%d.png'%(cluster_col, task_number),bbox_inches = 'tight')
    plt.savefig('./result/mapping_LO_uti_time_%d_%d.pdf'%(cluster_col, task_number),bbox_inches = 'tight')
    plt.savefig('./result/mapping_LO_uti_time_%d_%d.svg'%(cluster_col, task_number),format='svg',bbox_inches = 'tight')
    plt.show()


def pri_uti_exper():
    mapping_Algorithm = ['DM','CRMS','Slack']
    uti_list = []
    num_tries = {}
    uti_number = 10
    for i in mapping_Algorithm:
        num_tries[i]=[0 for _ in range(uti_number)]
    cycle_index = 1000
    system_uti_start = 0.2
    system_uti_dis = 0.05
    for j in range(uti_number):
        system_uti = system_uti_start + system_uti_dis * j
        uti_list.append(system_uti)
        for i in tqdm(range(cycle_index), desc="Processing", unit="items", ncols=100):
            #任务集生成
            ts = Drs_gengerate(task_number, system_uti * node_number, 2, 0.5, node_number)
            task_set = ts.HI.union(ts.LO)

            #DM
            ts.priority_assignment_DM_HI(task_set,0)
            FF_DP_mapping_list = FF_DP(ts)
            num_tries['DM'][j] += cal_schedulable(FF_DP_mapping_list, ts)

            #CRMS
            ts.priority_assignment_CRMS(task_set)
            FF_DP_mapping_list = FF_DP(ts)
            num_tries['CRMS'][j] += cal_schedulable(FF_DP_mapping_list, ts)

            #Slack
            ts.priority_assignment_Slack(task_set,0)
            FF_DP_mapping_list = FF_DP(ts)
            num_tries['Slack'][j] += cal_schedulable(FF_DP_mapping_list, ts)


        print('系统利用率：'+ str(system_uti) + '  DM可调度率：' + str( num_tries['DM'][j]) + '  CRMS可调度率：' + str( num_tries['CRMS'][j]) + \
                '  Slack可调度率：' + str(num_tries['Slack'][j]))

    
    plt.figure()
    xx = -1
    for i in mapping_Algorithm:
        xx += 1
        if i not in num_tries:continue
        schedulable = []
        for x in num_tries[i]:
            if x!=None: schedulable.append(float(x) / cycle_index * 100)
        plt.plot(uti_list, schedulable, linewidth=1, linestyle='-.',color= color_ku[xx%len(color_ku)], marker=marker_ku[xx % len(marker_ku)], label= i)
    plt.ylabel('Task Schedulability Ratio',size = FigWordSize)
    plt.xlabel('System Low-Criticality Utilization Level',size = FigWordSize)
    plt.xlim(system_uti_start-0.01, system_uti_start + system_uti_dis * (uti_number - 1) + 0.01)
    # plt.ylim(-12, 104)
    plt.xticks(fontproperties = 'Times New Roman', size = FigWordSize)
    plt.yticks(fontproperties='Times New Roman', size=FigWordSize)
    plt.legend(fontsize=FigWordSize)
    #plt.title("per-processor utilization")
    plt.savefig('./result/pri_LO_uti_%d_%d.png'%(cluster_col, task_number),bbox_inches = 'tight')
    plt.savefig('./result/pri_LO_uti_%d_%d.pdf'%(cluster_col, task_number),bbox_inches = 'tight')
    plt.savefig('./result/pri_LO_uti_%d_%d.svg'%(cluster_col, task_number),format='svg',bbox_inches = 'tight')
    plt.show()



def wcrt_uti_exper_FF():
    #wcrt_algorithm = ['amc-rtb','new_wcrt_1','new_wcrt_2','new_wcrt_3','new_wcrt_4_original','new_wcrt_4','new_wcrt_5','amc_rtb_pr']
    #wcrt_algorithm = ['amc-rtb','amc-rtb-pr-unit','amc-rtb-pr']
    wcrt_algorithm = ['amc-rtb', 'amc-rtb-pr']
    uti_list = []
    num_tries = {}
    uti_number = 13
    for i in wcrt_algorithm:
        num_tries[i]=[0 for _ in range(uti_number)]
    cycle_index = 1000
    system_uti_start = 0.2
    system_uti_dis = 0.05
    for j in range(uti_number):
        system_uti = system_uti_start + system_uti_dis * j
        uti_list.append(system_uti)
        for i in tqdm(range(cycle_index), desc="Processing", unit="items", ncols=100):
            #任务集生成
            ts = Drs_gengerate(task_number, system_uti * node_number, 2, 0.5, node_number)
            task_set = ts.HI.union(ts.LO)

            #DM
            ts.priority_assignment_Slack(task_set,0)
            #amc-rtb
            FF_DP_mapping_list = FF_DP(ts, amc_rtb_wcrt)
            num_tries['amc-rtb'][j] += cal_schedulable(FF_DP_mapping_list, ts, amc_rtb_wcrt)

            #new_wcrt_1
            #FF_DP_mapping_list_1 = FF_DP(ts, amc_rtb_pr_unit)
            #num_tries['amc-rtb-pr-unit'][j] += cal_schedulable(FF_DP_mapping_list_1, ts, amc_rtb_pr_unit)

            #amc_rtb_pr
            FF_DP_mapping_list_6 = FF_DP(ts, amc_rtb_pr)
            num_tries['amc-rtb-pr'][j] += cal_schedulable(FF_DP_mapping_list_6, ts, amc_rtb_pr)
            
        '''
        print('系统利用率：'+ str(system_uti) + '  amc-rtb可调度率：' + str( num_tries['amc-rtb'][j]) + '  new_wcrt_1可调度率：' + str( num_tries['new_wcrt_1'][j]) + \
                '  new_wcrt_2可调度率：' + str(num_tries['new_wcrt_2'][j]) + '  new_wcrt_3可调度率：' + str( num_tries['new_wcrt_3'][j]) \
                    + '  new_wcrt_4_original可调度率：' + str( num_tries['new_wcrt_4_original'][j]) + '  new_wcrt_4可调度率：' + str( num_tries['new_wcrt_4'][j]) + \
                        '  new_wcrt_5可调度率：' + str( num_tries['new_wcrt_5'][j]) + '  amc_rtb_pr可调度率：' + str( num_tries['amc_rtb_pr'][j]))
        '''
        #print('系统利用率：'+ str(system_uti) + '  amc-rtb可调度率：' + str( num_tries['amc-rtb'][j]) + '  amc-rtb-pr-unit可调度率：' + str( num_tries['amc-rtb-pr-unit'][j]) + \
        #        '  amc-rtb-pr可调度率：' + str(num_tries['amc-rtb-pr'][j]))

        print('系统利用率：' + str(system_uti) + '  amc-rtb可调度率：' + str(
            num_tries['amc-rtb'][j]) + '  amc-rtb-pr可调度率：' + str(num_tries['amc-rtb-pr'][j]))

    plt.figure()
    xx = -1
    for i in wcrt_algorithm:
        xx += 1
        if i not in num_tries:continue
        schedulable = []
        for x in num_tries[i]:
            if x!=None: schedulable.append(float(x) / cycle_index * 100)
        plt.plot(uti_list, schedulable, linewidth=1, linestyle='-.',color= color_ku[xx%len(color_ku)], marker=marker_ku[xx % len(marker_ku)], label= i)
    plt.ylabel('Task Schedulability Ratio',size = FigWordSize)
    plt.xlabel('System Low-Criticality Utilization Level',size = FigWordSize)
    plt.xlim(system_uti_start-0.01, system_uti_start + system_uti_dis * (uti_number - 1) + 0.01)
    # plt.ylim(-12, 104)
    plt.xticks(fontproperties = 'Times New Roman', size = FigWordSize)
    plt.yticks(fontproperties='Times New Roman', size=FigWordSize)
    plt.legend(fontsize=FigWordSize)
    #plt.title("per-processor utilization")
    plt.savefig('./result/wcrt_LO_uti_FF_%d_%d.png'%(cluster_col, task_number),bbox_inches = 'tight')
    plt.savefig('./result/wcrt_LO_uti_FF_%d_%d.pdf'%(cluster_col, task_number),bbox_inches = 'tight')
    plt.savefig('./result/wcrt_LO_uti_FF_%d_%d.svg'%(cluster_col, task_number),format='svg',bbox_inches = 'tight')
    plt.show()

def wcrt_uti_exper_BF():
    #wcrt_algorithm = ['amc-rtb','new_wcrt_1','new_wcrt_2','new_wcrt_3','new_wcrt_4_original','new_wcrt_4','new_wcrt_5','amc_rtb_pr']
    wcrt_algorithm = ['amc-rtb','amc-rtb-pr-unit','amc-rtb-pr']
    uti_list = []
    num_tries = {}
    uti_number = 10
    for i in wcrt_algorithm:
        num_tries[i]=[0 for _ in range(uti_number)]
    cycle_index = 100
    system_uti_start = 0.2
    system_uti_dis = 0.05
    for j in range(uti_number):
        system_uti = system_uti_start + system_uti_dis * j
        uti_list.append(system_uti)
        for i in tqdm(range(cycle_index), desc="Processing", unit="items", ncols=100):
            #任务集生成
            ts = Drs_gengerate(task_number, system_uti * node_number, 2, 0.5, node_number)
            task_set = ts.HI.union(ts.LO)

            #DM
            ts.priority_assignment_Slack(task_set,0)
            #amc-rtb
            FF_DP_mapping_list = BF_DP(ts, amc_rtb_wcrt)
            num_tries['amc-rtb'][j] += cal_schedulable(FF_DP_mapping_list, ts, amc_rtb_wcrt)
            '''
            #new_wcrt_1
            FF_DP_mapping_list_1 = FF_DP(ts, new_wcrt_1)
            num_tries['new_wcrt_1'][j] += cal_schedulable(FF_DP_mapping_list_1, ts, new_wcrt_1)
            '''
            #new_wcrt_1
            FF_DP_mapping_list_1 = BF_DP(ts, amc_rtb_pr_unit)
            num_tries['amc-rtb-pr-unit'][j] += cal_schedulable(FF_DP_mapping_list_1, ts, amc_rtb_pr_unit)
            '''
            #new_wcrt_2
            FF_DP_mapping_list_2 = FF_DP(ts, new_wcrt_2)
            num_tries['new_wcrt_2'][j] += cal_schedulable(FF_DP_mapping_list_2, ts, new_wcrt_2)

            #new_wcrt_3
            FF_DP_mapping_list_3 = FF_DP(ts, new_wcrt_3)
            num_tries['new_wcrt_3'][j] += cal_schedulable(FF_DP_mapping_list_3, ts, new_wcrt_3)
            
            #new_wcrt_4_original
            FF_DP_mapping_list_4_original = BF_DP(ts, new_wcrt_4_original)
            num_tries['new_wcrt_4_original'][j] += cal_schedulable(FF_DP_mapping_list_4_original, ts, new_wcrt_4_original)
            
            #new_wcrt_4
            FF_DP_mapping_list_4 = FF_DP(ts, new_wcrt_4)
            num_tries['new_wcrt_4'][j] += cal_schedulable(FF_DP_mapping_list_4, ts, new_wcrt_4)
            
            #new_wcrt_5
            FF_DP_mapping_list_5 = FF_DP(ts, new_wcrt_5)
            num_tries['new_wcrt_5'][j] += cal_schedulable(FF_DP_mapping_list_5, ts, new_wcrt_5)
            '''
            #amc_rtb_pr
            FF_DP_mapping_list_6 = BF_DP(ts, amc_rtb_pr)
            num_tries['amc-rtb-pr'][j] += cal_schedulable(FF_DP_mapping_list_6, ts, amc_rtb_pr)
            
        '''
        print('系统利用率：'+ str(system_uti) + '  amc-rtb可调度率：' + str( num_tries['amc-rtb'][j]) + '  new_wcrt_1可调度率：' + str( num_tries['new_wcrt_1'][j]) + \
                '  new_wcrt_2可调度率：' + str(num_tries['new_wcrt_2'][j]) + '  new_wcrt_3可调度率：' + str( num_tries['new_wcrt_3'][j]) \
                    + '  new_wcrt_4_original可调度率：' + str( num_tries['new_wcrt_4_original'][j]) + '  new_wcrt_4可调度率：' + str( num_tries['new_wcrt_4'][j]) + \
                        '  new_wcrt_5可调度率：' + str( num_tries['new_wcrt_5'][j]) + '  amc_rtb_pr可调度率：' + str( num_tries['amc_rtb_pr'][j]))
        '''
        print('系统利用率：'+ str(system_uti) + '  amc-rtb可调度率：' + str( num_tries['amc-rtb'][j]) + '  amc-rtb-pr-unit可调度率：' + str( num_tries['amc-rtb-pr-unit'][j]) + \
                '  amc-rtb-pr可调度率：' + str(num_tries['amc-rtb-pr'][j]))

    plt.figure()
    xx = -1
    for i in wcrt_algorithm:
        xx += 1
        if i not in num_tries:continue
        schedulable = []
        for x in num_tries[i]:
            if x!=None: schedulable.append(float(x) / cycle_index * 100)
        plt.plot(uti_list, schedulable, linewidth=1, linestyle='-.',color= color_ku[xx%len(color_ku)], marker=marker_ku[xx % len(marker_ku)], label= i)
    plt.ylabel('% of schedulable',size = FigWordSize)
    plt.xlabel('utilization of taskset in LO mode',size = FigWordSize)
    plt.xlim(system_uti_start-0.01, system_uti_start + system_uti_dis * (uti_number - 1) + 0.01)
    # plt.ylim(-12, 104)
    plt.xticks(fontproperties = 'Times New Roman', size = FigWordSize)
    plt.yticks(fontproperties='Times New Roman', size=FigWordSize)
    plt.legend(fontsize=FigWordSize)
    #plt.title("per-processor utilization")
    plt.savefig('./result/wcrt_LO_uti_BF_%d_%d.png'%(cluster_col, task_number),bbox_inches = 'tight')
    plt.savefig('./result/wcrt_LO_uti_BF_%d_%d.pdf'%(cluster_col, task_number),bbox_inches = 'tight')
    plt.savefig('./result/wcrt_LO_uti_BF_%d_%d.svg'%(cluster_col, task_number),format='svg',bbox_inches = 'tight')
    plt.show()
