# GKD-O1 Execution Handoff

本文件由 trusted main 在 bootstrap 后补齐实际 task state、固定 base SHA、offer/claim、candidate head、evidence 和验收事实。executor 在任何文件修改前必须完整阅读本文件、`requirements.md`、`plan.md`、根 `AGENTS.md`、`VISION.md` 及 `.agents/` 持久记录。

## Hard Boundary

- 只修改 O1 scope；不得触碰生产 `~/.codex`、AIO、GitHub settings/Secrets、tag/Release 或已发布资产。
- 只交付，不接受、不合并、不归档、不清理其他任务、不委派子代理。
- helper 若存在未发现的外部调用，停止删除并以 findings 报告，不伪造“无调用”结论。
