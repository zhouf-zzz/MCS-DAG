# MCS-DAG

## 同构多核处理器架构简化说明

当前工程已将处理器架构入口统一到 `wcrt_cal.py` 的同构配置：

- `HOMOGENEOUS_GRID_ROWS`
- `HOMOGENEOUS_GRID_COLS`
- `set_homogeneous_architecture(rows, cols)`

### 如何修改为你需要的同构规模

1. 打开 `wcrt_cal.py`，调整默认网格：
   - `HOMOGENEOUS_GRID_ROWS`
   - `HOMOGENEOUS_GRID_COLS`
2. 或在实验脚本开始处显式调用：

```python
from wcrt_cal import set_homogeneous_architecture

# 例如：8 个同构核心（2x4）
set_homogeneous_architecture(rows=2, cols=4)
```

### 建议同时做的精简（取消多余内容）

如果你希望完全聚焦“同构多核”并去掉与异构比例相关的参数：

- 在 `task_set.py` 的 `Drs_gengerate.__init__(...)` 中：
  - 将 `CF`、`CP` 固定为常量（例如 `CF=1`、`CP=1`），或删除为内部常量。
- 在 `experiment.py` 中：
  - 删除 `system_CP`、`system_CF` 扫描实验，仅保留总利用率实验。
- 保留 `cluster_row/cluster_col` 仅作为“同构网格尺寸”参数，不再赋予异构语义。

这样可以在不改动核心映射/可调度性分析流程的情况下，完成架构简化。
