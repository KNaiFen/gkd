# 当前项目进度

## 当前状态

manual-first 默认入口、兼容基线、子代理事件解析、MCP 协商、CLI 探针、app-server 初始化能力和 turn/steer 退场修正均已完成并合并。当前没有挂起的根目录任务。

## 已确认事实

- 当前 development bundle：`0.0.0-dev.1`，content digest `33b0f0ae5c8e591b6cc0673c1f338dc83a3b36bdcedd087e0a7f801a4d1bfcda`。
- 默认安装面只包含 foundation 与 manual-first `gkd-main`；legacy/optional 能力保持显式分离。
- 该 development bundle 已按明确授权安装到生产 GKD managed surface，production-migration-doctor 返回 healthy；它尚未成为 tag/Release，也未接入 AIO。
- 当前 CLI 的 `steer` feature 为 `removed`，相关 legacy watcher 调用在运行时 fail-closed。

## 下一步

没有预先批准的下一项。新工作应由主代理在独立 worktree 建立任务计划后开始。
