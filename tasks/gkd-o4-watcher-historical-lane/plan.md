# GKD-O4 Plan

## Goal

将 watcher/probe 从默认验证成本中隔离，同时保留可按需调用的历史验证能力和原有 fail-closed 结论。

## Behavior And Defaults

- 默认 `gkd-verify` 仅运行核心 scope；输出中的 scope 集合和总数稳定，不再隐式启动 watcher、Codex app-server 或 live probe。
- historical lane 使用独立命令或明确 flag，输出独立 scope 名称和 canonical result/evidence；调用者必须显式选择是否执行 host-capability probe。
- historical lane 缺少 Codex、协议 digest、M-1B contract result 或临时资源时返回稳定错误/`unsupported`，不降级为普通 pass。
- O3 canonical result producer/consumer 是唯一结果格式来源；不得恢复各 scope 自己重复运行核心合同。

## Scope

- 调整 `scripts/gkd-verify` scope 列表和结果摘要。
- 新增 historical watcher runner/入口，并接入 `tests/watchdog/run_contracts.py` 与必要的 probe wrapper。
- 更新 watcher/probe README、manifest/lock/source 声明和 focused tests。

## Compatibility

- `gkd_watchdog` Python API、`gkd-watchdog-mcp` CLI、M-1B evidence schema 和 M-1C live probe 参数保持兼容。
- 默认验证器的退出码、base SHA ancestry 校验、canonical result schema 和 protected/output 边界保持 O3 语义。
- 历史 lane 的新入口必须使用仓库相对路径和可移植 Python 启动方式。

## Security And Data

- 不读取或写入用户凭据、生产 config 或原始 session 内容。
- historical evidence 继续只保留脱敏摘要、digest、枚举和清理状态；不保存路径、token、对话正文或原始 app-server/MCP payload。
- 临时进程和目录必须在成功、失败和取消路径清理；清理失败必须 fail-closed。

## Execution Route

- `gkd-main` 完成 requirements-ready、plan-approve、authorization、offer、claim 和 trusted bridge。
- 精确角色为 `gkd_executor`，不允许 worker、fallback、nested agent 或同 attempt 重试。
- executor 只实现并交付；独立 `gkd_acceptor` 在真实 canonical checkout 用显式 full head 验收；trusted main 才能合并和清理。

## External Side Effects

- 允许一个 task worktree/branch/PR、仓库声明的默认/historical verifier、隔离 evidence root 和只读 CI 观察。
- 禁止生产 `~/.codex`、AIO、GitHub settings/Secrets、付费 runner、tag/Release 写入。

## Acceptance Evidence

- 默认 verifier 一次完整运行及结果 manifest。
- historical lane 两次独立运行的结果/evidence、watcher core 与 native probe focused tests。
- 默认 lane 与 historical lane 的 scope 列表、test-ID digest、base/head 和 bundle manifest/lock 复核。
- fixed-head `GKD Verify`、独立 review 和 canonical acceptance 事实。

