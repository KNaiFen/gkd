# 当前项目进度

## 当前状态

manual-first 默认入口、兼容基线、子代理事件解析、MCP 协商、CLI 探针、app-server 初始化能力和 turn/steer 退场修正均已完成并合并。当前没有挂起的根目录任务。

## 已确认事实

- 当前 development bundle：`0.0.0-dev.1`，content digest `3349077b50bca3d1b31919ef7004b8071229599abfbd0464baadab12b963bd16`。
- 默认安装面只包含 foundation 与 manual-first `gkd-main`；旧 role/自动化能力只读保留，不再安装或路由。
- 生产 GKD managed surface 已清理为单一 `gkd-main` Skill；不提供 production migration，也未创建 tag/Release 或接入 AIO。
- 当前 CLI 的 `steer` feature 为 `removed`，相关 legacy watcher 调用在运行时 fail-closed。

## 下一步

没有预先批准的下一项。新工作应由主代理在独立 worktree 建立任务计划后开始。
