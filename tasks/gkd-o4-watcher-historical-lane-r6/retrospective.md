# GKD O4 Watcher Historical Lane R6 Retrospective

## 结果

O4 已将 watcher/probe 从默认验证成本分离到显式 historical lane，同时保留可复现的历史合同、M-1C host capability 结论和 fixed-tree acceptance 证据。默认路径现在只承担 core scope。

## 经验

- optional historical lane 必须输出明确 profile、完整 scope 与 artifact digest；只从默认 scope 列表删除项目会让 acceptance 失去固定 tree 解释能力。
- consumer compatibility 需要先于 producer 行为变化合并。R3 的 lane/profile consumer 前置任务使 R6 能在新 manifest 下独立验收。
- `unsupported` 是可追溯能力事实，不是失败或成功的替代品；在 host 不具备 probe 能力时应保留它，而不是跳过或伪造通过。
- automatic bridge 使用精确 execution context 以及 spawn 前 acknowledgement、spawn 后立即 claim 的顺序，可在真实 executor route 下避免 cwd/PATH 与 pre-claim 竞态。

## 后续

从 merge `c133de3e983f002259c68538aa644ca8fc7e0823` 的 fresh development bundle 建立 O5 runtime fixture 与测试输入拆分任务。
