# 项目运行逻辑检查报告（任务模型 / 处理器模型 / AMC-RTB）

## 1) 任务模型（Task Model）
- 核心任务类为 `MCTask`，包含低/高关键度执行时间（`eLO/eHI`）、截止期（`dLO/dHI`）、周期（`pLO/pHI`）、利用率（`uLO/uHI`）以及关键度标志 `cri`（0=HI, 1=LO）。
- 每个任务固定为 `node_number=1`（单任务单核映射），并保留 `dag_id/predecessors/successors` 字段用于 DAG 约束。
- `MCTaskSet` 通过 `LO` 和 `HI` 两个集合维护任务集，其中 HI 任务会同时出现在 LO 与 HI 集中（便于模式切换分析）。
- `MCTaskSet.reset()` 已统一按 `HI ∪ LO` 重置任务状态。

## 2) 系统处理器模型（Processor/Core Model）
- 处理器被建模为线性 4 核（`node_number=4`），映射结构 `mapping_list` 是长度为 4 的列表。
- 映射算法包括 `FF/BF/WF + DU/DP` 变体，放置验证统一调用 `cal_wcrt(...)`。
- 若任务 `final_wcrt > dLO` 或 `wcrt_intertask == -1`，则该次放置失败并回退。

## 3) 舍去并行重叠后的 AMC-RTB 运行逻辑
- 主入口 `amc_rtb_wcrt(task_set, T, tasks)` 分为 LO 模式和 HI 模式两段固定点迭代。
- 每个仿真步中会先释放作业，再从“可运行作业集”中选取执行对象。
- 可运行条件由 DAG 与释放时刻共同决定：`release_time <= current_time` 且前驱任务均已完成。
- **单核映射约束下，`choose_job_new` 仅返回一个作业：当前可运行作业中优先级最高者**（不再进行并行任务拼接、重叠检测或 `preempt` 标志分支）。
- 若当前时刻无可运行干扰作业，则尝试执行目标任务 `current_job`；若目标任务也不满足 DAG 可运行条件，则该时隙空转。
- 任一模式超过截止期返回 `-1`；否则任务响应时间记为 `max(rLO, rHI)`。

## 4) 与映射流程的衔接
- 映射循环采用 DAG 截止期判定：每次试探放置后，按已映射 DAG 逐一校验；要求 DAG 内局部 WCRT 均可解，且 DAG 出口节点 `final_wcrt` 不超过其 `dLO`。
- `cal_wcrt` 会先依据当前映射构建与目标任务有竞争关系的任务集合，再筛选高优先级干扰任务，最后调用指定 WCRT 算法（默认 `amc_rtb_wcrt`）。
- 因此映射可行性本质上由“该映射下任务的 AMC-RTB 响应时间是否满足截止期”决定。


## 5) 当前多核 cal_wcrt 策略（忽略通信开销）
- 采用 Partitioned 固定优先级 + 两层分析：
  - 层1（核内 AMC-RTB）：对 DAG 内每个已映射节点，在其所在核心上计算局部 WCRT。
  - 层2（DAG 全局 RTA）：对已映射 DAG 做拓扑排序并递推 `finish(v)=local_wcrt(v)+max(finish(pred(v)))`。
- DAG 截止期判定口径（当前实现）：所有 sink 节点满足 `finish(sink) <= sink.dLO`；任一节点局部 WCRT 不可解（-1）则 DAG 不可调度。
- `cal_wcrt` 对外暴露：`wcrt_intertask` 为节点局部 WCRT，`final_wcrt` 为节点全局完成时间上界。

## 6) `mapping_validation.py` 运行校验结果（本次）
- 运行命令：`python mapping_validation.py`（先安装依赖 `numpy/scipy/matplotlib`）。
- 在总利用率 `U=0.20~0.60` 下，三种映射算法 **BF_DIP / BF_DP / WF_DU 的可调度率均为 1.000**，且 `inconsistent=0`。
- 在 `U=0.70` 下，可调度率略有下降：
  - `BF_DIP=0.990`
  - `BF_DP=0.980`
  - `WF_DU=0.990`
  同时 `inconsistent=0`，未发现“可调度性判定前后矛盾”的异常。
- 运行时开销方面，`BF_DP` 平均耗时最高（约 `0.058~0.081s`），`BF_DIP/WF_DU` 较低（约 `0.018~0.031s`）。
- 结论：**当前映射算法未发现一致性问题；在高利用率（0.70）区间出现预期的可调度率下降，属于资源趋紧下的正常现象。**

## 7) 按要求扩展到 `U=0.80` 的再次实验结果
- 运行方式：`run_validation_with_plots(uti_points=7)`，即利用率点从 `0.20~0.80`（步长 `0.10`）。
- 新增 `U=0.80` 结果如下：
  - `BF_DIP`: `ratio=0.920`, `avg_runtime=0.029042s`, `inconsistent=0`
  - `BF_DP`: `ratio=0.900`, `avg_runtime=0.053358s`, `inconsistent=0`
  - `WF_DU`: `ratio=0.930`, `avg_runtime=0.026911s`, `inconsistent=0`
- 结论：当系统利用率提升到 `0.80` 时，可调度率继续下降（约 `0.90~0.93`），但一致性计数依然为 0，仍未发现映射有效性判定矛盾。

## 8) “同为按步仿真但耗时差很多”的可能原因（结合当前实现）
- 当前实现的时间步长是 `unit_time = 10`，并非 1 个最小时间单位推进；在同样时间跨度下，循环次数会显著减少，因此运行更快。
- 当前可运行作业选择被简化为**每个时刻只执行 1 个最高优先级作业**（`choose_job_new`），没有并行选择/重叠检测等组合逻辑，单步计算成本更低。
- `mapping_validation` 默认 `disable_internal_subtask=True`，会关闭任务内部 DAG 子任务生成，映射与分析对象更简单，速度明显快于“开启内部子任务”的版本。
- 映射验证时只校验“已映射 DAG”的截止期可行性（`_all_mapped_dags_deadline_ok`），且任务规模默认仅 `task_number=10`、`node_number=4`、`cycles=100`；若你的实验规模更大，耗时会呈倍数增长。
- 当前生成任务集使用随机生成（未固定随机种子），不同代码/不同轮次任务实例复杂度可能差异很大；若你恰好生成了更“紧张”的实例，仿真时间也会明显变长。

## 9) 内部子任务默认开启后的测试（已开启内部子任务）
- 已将 `mapping_validation.py` 的 `disable_internal_subtask` 默认值从 `True` 改为 `False`，现在默认会生成并参与分析任务内部子任务。
- 采用开启内部子任务配置进行快速验证：`validate_mapping_reliability(uti_start=0.8, uti_points=1, cycles=1, disable_internal_subtask=False)`。
- 本次结果（`U=0.80`）：
  - `BF_DIP`: `ratio=1.000`, `avg_runtime=4.542115s`, `inconsistent=0`
  - `BF_DP`: `ratio=1.000`, `avg_runtime=1.375754s`, `inconsistent=0`
  - `WF_DU`: `ratio=0.000`, `avg_runtime=0.798486s`, `inconsistent=0`
- 观察：开启内部子任务后单次映射耗时明显升高（秒级），与“关闭内部子任务”时的毫秒级耗时形成明显对比。


## 10) 按要求改为 `cycles=10` 的一次测试（内部子任务开启）
- 测试命令：`validate_mapping_reliability(uti_start=0.8, uti_points=1, cycles=10, disable_internal_subtask=False)`。
- 测试配置：`U=0.80`、`cycles=10`、内部子任务开启。
- 结果如下：
  - `BF_DIP`: `ratio=0.300`, `avg_runtime=1.173998s`, `inconsistent=0`
  - `BF_DP`: `ratio=0.700`, `avg_runtime=1.269726s`, `inconsistent=0`
  - `WF_DU`: `ratio=0.100`, `avg_runtime=0.785453s`, `inconsistent=0`
- 说明：在 `cycles=10` 下结果更稳定于统计意义，但由于任务集随机生成，不同轮次与不同随机样本下比例会出现波动。


## 11) 按要求测试：`cycles=50`，利用率 `0.4~0.8`（一次）
- 测试命令：`validate_mapping_reliability(uti_start=0.4, uti_step=0.1, uti_points=5, cycles=50, disable_internal_subtask=False)`。
- 测试配置：内部子任务开启，`U=0.40, 0.50, 0.60, 0.70, 0.80`。
- 结果汇总：
  - `U=0.40`
    - `BF_DIP`: `ratio=0.900`, `avg_runtime=2.866724s`, `inconsistent=0`
    - `BF_DP`: `ratio=1.000`, `avg_runtime=2.130124s`, `inconsistent=0`
    - `WF_DU`: `ratio=0.740`, `avg_runtime=2.960178s`, `inconsistent=0`
  - `U=0.50`
    - `BF_DIP`: `ratio=0.740`, `avg_runtime=2.340767s`, `inconsistent=0`
    - `BF_DP`: `ratio=1.000`, `avg_runtime=1.738599s`, `inconsistent=0`
    - `WF_DU`: `ratio=0.660`, `avg_runtime=3.011448s`, `inconsistent=0`
  - `U=0.60`
    - `BF_DIP`: `ratio=0.620`, `avg_runtime=1.984530s`, `inconsistent=0`
    - `BF_DP`: `ratio=1.000`, `avg_runtime=1.729001s`, `inconsistent=0`
    - `WF_DU`: `ratio=0.460`, `avg_runtime=1.842257s`, `inconsistent=0`
  - `U=0.70`
    - `BF_DIP`: `ratio=0.520`, `avg_runtime=1.526557s`, `inconsistent=0`
    - `BF_DP`: `ratio=0.980`, `avg_runtime=1.341318s`, `inconsistent=0`
    - `WF_DU`: `ratio=0.500`, `avg_runtime=1.633628s`, `inconsistent=0`
  - `U=0.80`
    - `BF_DIP`: `ratio=0.440`, `avg_runtime=0.996484s`, `inconsistent=0`
    - `BF_DP`: `ratio=0.880`, `avg_runtime=1.276180s`, `inconsistent=0`
    - `WF_DU`: `ratio=0.320`, `avg_runtime=0.842266s`, `inconsistent=0`
- 结论：在该设置下三种算法均未出现一致性异常（`inconsistent=0`）；随着利用率上升，可调度率整体下降。


## 12) 本次针对“子任务分配 + 可调度性核实执行路径”的代码核查结论
- **子任务分配粒度**：映射入口 `_iter_mapping_units` 会优先把 `task.internal_dag.nodes` 展开成“子任务映射单元”（`unit_key=(task.id,node_id)`）；若任务没有内部 DAG，则退化为任务级单元（`unit_key=(task.id,None)`）。
- **分配策略本质**：`FF_DU/BF_DU/WF_DU/BF_DP/WF_DP/BF_DIP` 都是“按单元逐个试放置到核心”的启发式分配；区别在于单元排序规则（按利用率或优先级）与核心选择规则（first-fit / best-fit / worst-fit / 综合评分）。
- **核实阶段是否执行可调度性分析**：会执行。每次试放置后都会调用 `_all_mapped_dags_deadline_ok(...)`；该函数再逐 DAG 调用 `analyze_dag_partitioned_fp(...)`，其中局部 WCRT 由 `_calc_task_local_wcrt(..., wcrt_algor)` 计算（默认 `amc_rtb_wcrt`），最后检查 sink 节点 `finish<=dLO`。
- **验证脚本中的执行位置**：`mapping_validation._is_mapping_valid(...)` 在检查“是否全映射”后，也会再次调用 `_all_mapped_dags_deadline_ok(...)` 进行可调度性核实；因此验证流程不是只看映射成功与否，而是实际执行了当前可调度性分析链路。
- **结论**：当前实现中“子任务分配”已接入映射主流程；“可调度性分析”在**映射试探阶段**和**验证判定阶段**都会执行。

## 13) 已修复：映射与可调度性分析统一到 `(task_id, node_id)` 粒度
- 映射表 `mapping_list` 现以 `unit_key=(task_id,node_id)` 记录单元；无内部 DAG 时使用 `(task_id,None)` 兼容。
- 放置/回退逻辑已按 unit 处理，避免“子任务粒度分配但任务粒度记录”的信息丢失。
- DAG 可调度性分析（局部响应时间 + DAG 聚合）已按 unit 粒度进行，并以 unit 级 sink 判定截止期。
- `mapping_validation` 的映射完整性检查已改为比较“期望 unit 集合”与“已映射 unit 集合”。
