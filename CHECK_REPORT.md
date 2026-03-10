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
