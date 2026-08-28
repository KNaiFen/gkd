# GKD-O4 Plan

## Goal

将 watcher/probe 从默认验证成本中隔离，同时保留可按需调用的历史验证能力和原有 fail-closed 结论。

## User Decisions

- 从 O3 accepted merge `9009b089fb811eceaf91ada8b60397b39a451f97` 之后的 trusted main 完整基线开始。
- 只使用一个精确 `gkd_executor` 和一个独立 `gkd_acceptor`；trusted main 才能合并和清理。
- 不修改生产 `~/.codex`、AIO、GitHub settings/Secrets、付费 runner、tag/Release 或已发布资产。

## Behavior And Defaults

- 默认 `gkd-verify` 仅运行核心 scope；输出中的 scope 集合和总数稳定，不再隐式启动 watcher、Codex app-server 或 live probe。
- historical lane 使用独立命令或明确 flag，输出独立 scope 名称和 canonical result/evidence；调用者必须显式选择是否执行 host-capability probe。
- historical lane 缺少 Codex、协议 digest、M-1B contract result 或临时资源时返回稳定错误/`unsupported`，不降级为普通 pass。
- O3 canonical result producer/consumer 是唯一结果格式来源；不得恢复各 scope 自己重复运行核心合同。

## Scope

- 调整 `scripts/gkd-verify` scope 列表和结果摘要。
- 新增 historical watcher runner/入口，并接入 `tests/watchdog/run_contracts.py` 与必要的 probe wrapper。
- 更新 watcher/probe README、测试入口、manifest/lock/source 声明和必要 schema。

## Non-Goals

- 不重写 watcher 协议、MCP adapter、app-server 控制逻辑、native probe 或其安全/清理语义。
- 不删除历史 fixtures/evidence，不把 M-1C `unsupported` 改写为 supported，不启用 automatic route。
- 不拆 O5 runtime fixtures、O6 optional pack、O7 contract index，也不改变生产/AIO。

## Acceptance Criteria

- 默认 `scripts/gkd-verify --base-sha <full-base-sha>` 不包含 watcher/probe scope，并成功生成 O3 canonical result manifest。
- 显式 historical lane 能独立执行 watcher core contracts，或在缺少真实宿主能力时返回稳定、可追溯的 fail-closed 诊断；不能伪造 live success。
- 默认与 historical lane 的 scope/test ID、base/head、verifier digest 和结果 manifest 均可验证；缺失、未知、篡改和 head/digest drift 继续拒绝。
- watcher core、native probe、M-1B/M-1C 历史相关测试覆盖不下降；两次 historical evidence 逐字节一致。
- candidate bundle、manifest/lock、README 和 task delivery 事实一致；固定头 `GKD Verify` 与独立 acceptor 通过。
- 变更不引入绝对本机路径、用户名、凭据、新依赖或生产/AIO/GitHub settings 副作用。

## Compatibility

- `gkd_watchdog` Python API、`gkd-watchdog-mcp` CLI、M-1B evidence schema 和 M-1C live probe 参数保持兼容。
- 默认验证器的退出码、base SHA ancestry 校验、canonical result schema 和 protected/output 边界保持 O3 语义。
- 历史 lane 的新入口使用仓库相对路径和可移植 Python 启动方式。

## Security And Data

- 不读取或写入用户凭据、生产 config 或原始 session 内容。
- historical evidence 只保留脱敏摘要、digest、枚举和清理状态；不保存路径、token、对话正文或原始 app-server/MCP payload。
- 临时进程和目录必须在成功、失败和取消路径清理；清理失败必须 fail-closed。

## Migration

- 已发布 bundle 不修改；合并后仅由 trusted main 重新生成未发布开发 bundle 和 project staging 事实。
- 现有 watcher 使用者继续调用原 CLI；需要完整历史验证的调用者改用显式 historical lane。

## Public Interfaces

- 保留现有 `gkd-watchdog-mcp` 和 probe 参数；新增入口必须有稳定帮助文本、错误码和结果 scope 名称。
- `gkd-task`、`gkd-role`、`gkd-ci-monitor` 和 O3 result schema 的既有接口不变。

## Execution Route

- `gkd-main` 完成 requirements-ready、plan-approve、authorization、offer、claim 和 trusted bridge。
- 精确角色为 `gkd_executor`，不允许 worker、fallback、nested agent 或同 attempt 重试。
- executor 只实现并交付；独立 `gkd_acceptor` 在真实 canonical checkout 用显式 full head 验收；trusted main 才能合并和清理。

## External Side Effects

- 允许一个 task worktree/branch/PR、仓库声明的默认/historical verifier、隔离 evidence root 和只读 CI 观察。
- 禁止生产 `~/.codex`、AIO、GitHub settings/Secrets、付费 runner、tag/Release 写入。

## Action Mode

- `implement_and_merge_on_acceptance`。

## Implementation Notes

- 修改前搜索所有 `SCOPES`、watcher/probe runner 调用点和 manifest 生成入口，建立默认/历史测试基线。
- 默认入口不得通过删除测试、跳过失败或硬编码 `pass` 缩短验证；历史 lane 失败必须保留可复现原因。
- 交付记录默认/历史 scope 集合、两次 evidence、candidate bundle digest、固定 head 和清理结果，不跨入 O5-O8。\n
