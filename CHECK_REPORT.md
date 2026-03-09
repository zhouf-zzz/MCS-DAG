# 项目运行逻辑检查报告（任务模型 / 处理器模型 / AMC-RTB）

## 1) 任务模型（Task Model）
- 核心任务类为 `MCTask`，包含低/高关键度执行时间（`eLO/eHI`）、截止期（`dLO/dHI`）、周期（`pLO/pHI`）、利用率（`uLO/uHI`）以及关键度标志 `cri`（0=HI, 1=LO）。
- 每个任务默认 `node_number=1`，即单任务映射到单核；同时保留 `dag_id/predecessors/successors` 字段用于 DAG 约束。
- `MCTaskSet` 通过 `LO` 和 `HI` 两个集合维护任务集，其中 HI 任务会同时出现在 LO 与 HI 集中（便于模式切换分析）。
- 提供 DM/Slack/CRMS/节点数等优先级分配策略，其中大量映射与可调度性流程依赖 `pri` 值。

## 2) 系统处理器模型（Processor/Core Model）
- 处理器被建模为**线性 16 核**（`node_number=16`），不再使用二维拓扑。
- 映射结构 `mapping_list` 是长度为 16 的列表，每个元素为该核上任务 ID 列表。
- 映射算法包括 `FF/BF/WF + DU/DP` 等：
  - `FF_DU`：按任务利用率压力降序，逐核 First-Fit 放置；
  - `BF_DU/BF_DP`：按压力排序后，优先尝试“最拥挤”核（Best-Fit 风格）；
  - `WF_DU/WF_DP`：优先尝试“最空闲”核（Worst-Fit 风格）。
- 放置验证统一调用 `cal_wcrt(...)`，若任务 `final_wcrt > dLO` 或 `wcrt_intertask == -1` 则当前放置失败并回退。

## 3) AMC-RTB 算法运行逻辑
- 主入口 `amc_rtb_wcrt(task_set, T, tasks)` 分两段固定点迭代：
  1. **LO 模式**：从 `rLO=T.eLO` 开始，仿真时钟推进，直到响应时间收敛或超 `dLO`；
  2. **HI 模式**：仅对 HI 任务继续，从 `rHI=T.eHI` 开始，考虑 LO/HI 干扰任务不同周期参数，收敛或超 `dHI`。
- 每个仿真步长是 `unit_time=10`。在步内：
  - 按周期释放干扰作业；
  - `choose_job_new` 先选最高优先级任务，若该任务可被抢占（`preempt==1`）则仅执行该任务；否则尝试选择与其不重叠核资源的可并行任务。
- DAG 约束通过三处机制生效：
  - `_mark_job_release` 记录作业释放时刻并复制前驱集合；
  - `_dag_job_runnable` 检查“已释放 + 前驱全部完成”；
  - `_get_runnable_jobs` 仅返回可运行作业集合。
- 结果输出：若任一模式超过截止期返回 `-1`；否则任务 `resp/final_wcrt` 记录 `max(rLO, rHI)`。

## 4) 与映射流程的衔接
- `cal_wcrt` 先通过 `mapping_list` 求与目标任务在核上冲突的任务集合，再筛选高优先级干扰任务，最后调用指定 WCRT 算法（默认 `amc_rtb_wcrt`）。
- 因此“映射是否成功”本质上由“当前映射下每个已映射任务的 AMC-RTB 可满足截止期”决定。

## 5) 注意事项
- `experiment.py` 中 `cal_schedulable` 当前仅判断 `mapping_list` 是否为 `False`，不再次遍历校验全部任务（因为映射阶段已做在线校验）。
- `MCTaskSet.reset()` 使用了 `self.HILO`，但该属性未在构造函数中定义；若外部调用该函数可能触发异常，建议后续修复。
