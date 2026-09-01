# 进度

## 2026-09-02

- 已创建独立工作树，基于主分支 `080e611`。
- 已以本机 `codex-cli 0.152.0` 真实 app-server initialize capture 核对响应：仅有
  `codexHome`、`platformFamily`、`platformOs`、`userAgent`，没有服务端
  `capabilities` 字段；原始响应未写入仓库。
- `src/gkd_watchdog/runtime.py` 新增严格 initialize metadata parser，并将缺失、空值、
  类型漂移和未捕获 capability 名称归一为 `unsupported`，仅把安全字段事实附加到
  client，不保留原始 payload。
- 新增 current/legacy 脱敏夹具、`tasks/app-server-capability-init/evidence.json`，并在
  `compatibility-baselines.json` 登记 current `unsupported` 与历史 `compatibility-only`。
- 专项验证：runtime/app-server/contract catalog 26/26，watchdog 全量 59/59，live 负向
  17/17 通过。
- 仓库历史 lane 校验 59/59 通过；host capability probe 按既有边界记录
  `unsupported`，没有把 current baseline 当作 watcher 可用。
- `gkd_bundle generate` 保持 development bundle `0.0.0-dev.1` / content digest
  `9a683001…`，`validate-repo` 返回 valid（7 个 VISION sections）；compileall 与
  `git diff --check` 通过。
- 已知边界：manual-first 默认安装继续不含 legacy watcher；历史 `0.147.0` 仅
  compatibility-only，当前 `0.152.0` capability 缺失为 unsupported；未修改
  MCP、CLI parser、turn/steer、生产/AIO 或发布面。
- 主代理已用本机生成 schema 复核 InitializeResponse 字段，并接受该阶段，待主工作树提交。
