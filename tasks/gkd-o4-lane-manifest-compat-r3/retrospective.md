# GKD O4 Lane Manifest Compatibility R3 Retrospective

## 结果

compatibility 前置任务已将 lane/profile manifest 的消费能力安全合入旧默认验证产物。后续 O4 可以改变默认 scope 集合，而 trusted delivery、acceptance 与 rework 能按显式 profile 复核完整 scope。

## 经验

- bridge execution context 修复解决了 CLI、candidate、task 与 runtime 参数推断；spawn 前固定 acknowledgement、spawn 返回后立即 claim 也消除了已观察到的 pre-claim 竞态。
- fixed-head monitor 的 policy 参数是仓库相对路径，不是 trusted main 展开后的绝对路径。错误输入必须退役 attempt，不能在同一验收尝试重跑。
- 兼容升级必须先保持当前 producer 的旧产物，使旧 trusted consumer 能验收自身；producer 行为变化只能在新 consumer 合并后进行。
- manifest profile 不能成为放宽 scope 的入口。已知 profile 的 scope 集合、test IDs、base/head 与各类 digest 都必须共同绑定。

## 后续

从 merge `aeeeb2b57fc98289e341f4b04790b7cf34d78ee3` 生成并验证新的 execution bundle，再以全新 lifecycle 重启完整 O4 watcher/probe historical lane。
