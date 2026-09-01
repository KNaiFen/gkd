# 审查

## 结论

主代理审查通过，已合并到 `refactor/manual-first-workflow`。

## 变更范围

- `AppServerFactory` 现在严格解析 app-server initialize 的四个当前必需元数据字段，
  并将安全归一化事实附加到 client；原始响应不进入 transcript 或 evidence。
- capability 缺失、null、类型漂移、名称漂移和未捕获字段均稳定归类为
  `unsupported`，不从 schema 字段或客户端请求反推支持。
- 当前 `0.152.0` 真实 capture 与历史 `0.147.0` evidence 分开登记：前者为
  `unsupported`，后者为 `compatibility-only`；不恢复 automatic watcher。
- 新增初始化夹具、专项 contract catalog、脱敏 evidence 与文档；未修改 MCP、CLI
  JSONL parser、watcher 控制、`turn/steer`、生产/AIO 或发布面。

## 验证

- runtime/app-server/contract catalog：26/26 通过。
- watchdog 全量：59/59 通过。
- live 负向：17/17 通过。
- 仓库验证、bundle generate/validate、compileall 和 `git diff --check` 待主代理
  交接前完成。

## 已知边界

- 当前 baseline 的 initialize 响应没有服务端 capability 广告，故 parser 不声称任何
  watcher capability 支持。
- 历史 `0.147.0` capability 仅来自已登记 protocol evidence，不能升级为 current
  live capability；M-1C 的 `unsupported` 和 manual-first 默认路线保持不变。

## 主代理复核

- 已用本机 `codex app-server generate-json-schema --experimental` 核对当前 `InitializeResponse`：四个必需字段与夹具一致，未发现 server capability 字段。
- 已核对 `AppServerFactory` 只把脱敏后的归一化事实附加到内存 client，不把原始 initialize response 写入 transcript/evidence。
- 已接受当前能力 unsupported 和历史 compatibility-only 的边界；automatic watcher、MCP、CLI parser 与 turn/steer 均未被恢复或改写。
- 仓库既有部分 legacy/manual-first verifier 失败不由本任务扩大或改写，交接时按现有
  记录报告。
