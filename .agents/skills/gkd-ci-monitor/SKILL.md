---
name: gkd-ci-monitor
description: 只读等待一个明确的 GitHub CI、Actions 或发布目标，并返回一次终态报告。
---

# GKD CI Monitor

这是 CI、Actions 和等待中发布流程的专用只读能力。它只在 PLAN 已授权跟踪且父代理提供一个明确目标时使用，不替代 `gkd-main` 的规划、验收或交付判断。

## 输入与唯一目标

- 父代理必须提供一个目标项目 worktree、仓库（可由脚本从该 worktree 的 `origin` 解析）和且仅一个目标：`--pr <number>`、`--run <id>`、`--commit <sha>` 或 `--release <tag>`。
- PR、主线提交、workflow run 和正式 release 是不同目标；每次调用只跟踪其中一个固定标识，不在等待中切换目标。
- 每次调用都必须显式传入 `--interval 30 --timeout 3600`。改变 `interval` 或 `timeout` 任一参数都必须先得到 PLAN 明确授权，并让父代理的一次性等待时长与获准的 `timeout` 一致。

## 唯一入口与只读边界

`gkd-github-watch` 属于本 Skill，不属于目标项目。仓库源文件在 `.agents/skills/gkd-ci-monitor/scripts/gkd-github-watch`，安装后由 Codex 从 `~/.codex/skills/gkd-ci-monitor/scripts/gkd-github-watch` 提供。角色按已安装 Skill 的目录解析脚本，并把目标项目 worktree 作为命令 cwd，例如：

```text
~/.codex/skills/gkd-ci-monitor/scripts/gkd-github-watch --pr <number> --interval 30 --timeout 3600
```

按需传入 `--repo owner/name`；目标项目只用于提供 worktree、origin 和查询上下文，不需要放置同名脚本。脚本缺失时报告 Skill 安装不完整，不要求目标项目恢复入口。不要另行构造 API 请求或轮询脚本。禁止调用 GitHub CLI 的 watch 子命令，也禁止重跑、取消、编辑、派发或发布 GitHub 资源。不得修改本地文件、Git、目标项目代码或任何状态文件，不得启动其他代理，不得验收或合并。

## 等待与停止

1. 启动一次命名的 `gkd_ci_monitor` 角色并只等待这一目标。父代理使用一次 `wait_agent(timeout_ms=3600000)`（或 PLAN 明确批准且与 timeout 一致的时长）；等待期间不读取仓库/CI、不补充分析、不重复启动监控。
2. 脚本缺失、目标无法唯一解析、仓库与目标漂移、认证失败、目标不存在或返回未知结构时，立即报告阻塞并停止，不静默降级或临时轮询。
3. 脚本返回成功、失败、取消、超时或调用错误时，立即停止并原样保留该终态；不要继续等待或重试。失败后的修复由 main 重新规划并重新取得授权。

## 报告

报告目标类型和标识、仓库、链接、查询到的终态、失败检查摘要、超时/错误原因和后续建议。若未得到终态，明确写“阻塞”或“超时”，不要声称通过。报告只写入父代理交接，不落盘。
