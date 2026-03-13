# MCS-DAG

## 批量生成随机任务集

新增脚本 `generate_tasksets.py`，可直接调用当前仓库中的 `Drs_gengerate` 任务集生成方法，批量生成随机任务集并保存为 JSON。

示例：

```bash
python generate_tasksets.py --count 20 --task-number 12 --system-utilization 2.5 --output test_result/generated_tasksets.json
```

常用参数：

- `--count`：生成任务集数量。
- `--task-number`：每个任务集中的任务数。
- `--node-number`：处理器核数。
- `--system-utilization`：总利用率。
- `--cf`：高关键度任务 HI 模式利用率放大因子。
- `--cp`：高关键度任务占比。
- `--seed`：随机种子（保证可复现）。
- `--output`：输出 JSON 文件路径。
