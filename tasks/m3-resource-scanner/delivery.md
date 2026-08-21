# GKD-M3-B 交付

## 结果

- Outcome: `resource_scanner_ready`
- Fixed base: `97c97cec3aa9cf51973bf4436be4d1750e0436fc`
- Claim base head: `46dd03c039ff203d3c99d1bff3b29b7bb9ae7b0a`
- Claim: `bb2fe214fada55efce73758e02adf2b74afe7c370fef7f49885d6e7c412608d2`
- Implementation/evidence commit: `1d57b2e139948fc7b315292bfa5d4c2c8f2588d2`
- Accepted execution bundle: `4d12c9973ea9302162493a5a71e25a4948b1f23991d30873c4a11ad691647aed`
- Candidate output bundle: `5f68703a42df613125814d78a491cb1991620afcb915d5a486c6ea6334604129`
- Evidence digest: `f32b33b8f53d10f018107452fdb5de2860587abc64d5ada1bb0b4453c77d674b`

本交付只实现 M3-B：确定性产物分类、资源 preset、visibility/runner/policy/billing
facts、speed-first/balanced/cost-aware recommendations，以及 diff/pull-request/artifact
固定范围脱敏 scanner。M3-A policy/monitor 与 M3-C review/Skills 未修改或实现。

## 实现

- `gkd_ci.resources` 提供 `zero`、`bounded`、`build-or-unknown` 分类和
  `resource-constrained`、`standard`、`high-capacity` preset。资源事实不完整时默认
  conservative preset；未知构建上界和峰值磁盘超限均返回 blocked，事后 cleanup 不改变结论。
- `gkd_ci.recommendations` 严格解析 visibility、runner、policy、billing、resource
  facts。只有带来源、币种、数值、检查时间且 `verified=true` 的价格进入推荐；未验证
  价格只输出 `unverified`，不生成成本声明。
- `gkd_ci.scanner` 只接受声明的 diff、pull-request、artifact surface，固定大小/路径
  边界，输出不保留匹配文本。credential、private key 或 credential assignment 会产生
  redacted terminal finding。
- 新 CLI、schema、hermetic fixtures、mutation contracts、deterministic evidence、
  文档和 manifest/lock 均已加入 candidate bundle；没有仓库、owner、机器路径、用户名、
  token 或 secret 常量。

## 验证

唯一版本化 verifier：

`PATH=/opt/homebrew/bin:$PATH scripts/gkd-verify --base-sha 97c97cec3aa9cf51973bf4436be4d1750e0436fc`

终态为 `378/378`：M3-A `29`、M3-B `14`、task-core `128`、role-routing `70`、
runtime-bridge `37`、foundation `53`、watcher-core/live-negative `47`。运行环境为
Python 3.14.6；未安装依赖，未运行历史 live probe、真实一小时等待、大型构建或 cache。

M3-B contract evidence 在两次独立运行中逐字节一致：

- Contract count: `14`
- Candidate output bundle: `5f68703a42df613125814d78a491cb1991620afcb915d5a486c6ea6334604129`
- Evidence digest: `f32b33b8f53d10f018107452fdb5de2860587abc64d5ada1bb0b4453c77d674b`
- `machinePathsRetained`: `false`

## 停止边界

本 session 停在 exact claim delivery 与 trusted-main 独立验收之前：不验收、不合并、
不归档、不清理 worktree/branch、不启动 M3-C，不修改生产 `~/.codex`、AIO、付费
runner、Secrets、GitHub settings、tag 或 Release。
