# GKD-M2-C 交付

## 结果

- Outcome: `automatic_runtime_bridge_ready`
- Fixed base: `302f60d96c2f81e85052025f814593015a436bd7`
- Bootstrap planning head: `a7208f2d796ec62b3ddb300730d8e9b37be9a56e`
- Rework base: `b512a2aa644992c88ae2a2012d1322573a9ead0b`
- Acceptance rework base: `b97dce72a21a719b616f418b7e23638bce507f0c`
- Implementation commit: `d3d8ea7a6d594caac843be91f7f2e651906bfacd`
- Evidence commit: `bb1992998af62119fde4eef1b0e9972fe757b3d7`
- PR: [KNaiFen/gkd#7](https://github.com/KNaiFen/gkd/pull/7)，Ready
- Checks: 未配置，事实为 `required_checks_not_configured_bootstrap`

本交付使显式 automatic route 具备 project-scoped staging 与 trusted-main
spawn → activation → exact claim 支持路径。manual 仍是默认路线，candidate-facing
claim/activation 仍 fail-closed；生产安装、AIO 修改、fresh main、M3、独立验收与
合并均未执行。

## Bootstrap Exception

M2-C 本身保持 `planning`、`epoch=1`、`revision=5`，claim 为 `null`。旧 manual
offer `d25292982fcd667d81971050a56814434a6027d9c5721e41c51cd1e132b404ab`
已在 epoch 0 撤销且未消费。按一次性 bootstrap exception，本 session 没有调用
`gkd-task claim`、`gkd-task deliver`、`gkd-role activation-record` 或私有 API，
也没有生成 M2-C activation、receipt、runtime evidence 或修改 task JSON/runtime。

## 实现

- `gkd-role project-stage/project-verify/project-remove` 从固定 bundle 生成并验证
  parent `gkd-main` Skill、exact `gkd_executor` TOML 与三个 executor Skills；只接受
  显式非生产 Git 根，在项目写入前重新验证 bundle 全部真实文件与 manifest/lock，
  并逐组件拒绝 project/bundle root 的祖先 symlink；冲突、路径穿越、source/target
  overlap、摘要/mode 漂移与受管路径 symlink 均 fail-closed。
- main role 通过受支持的 `TrustedMainRuntimeBridge` library interface 把六门 route
  decision 绑定到 offer/envelope，验证唯一 direct `gkd_executor` spawn 的 task、
  role/config/execution-bundle、model/effort/sandbox/runtime、identity 与 offer window。
  公开 `gkd-role automatic-*`、candidate `gkd-task claim` 与默认 task library 路径
  均返回 `TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE`，不会消费伪造 spawn JSON。
- automatic activation postimage 与 task/offer postimage 进入同一 task lock、exact
  CAS 和 journal 事务。并发失败方不产生 activation/receipt/journal；pre-commit
  中断回滚 activation，post-commit 中断一次 recovery 即补齐 claim/activation receipts。
- automatic 只允许 v3 offer/envelope；旧 v1/v2 仍可读取，但不能以单个
  `route=automatic` 绕过 route decision。失败路径不创建 manual claim、generic
  worker fallback 或候选写入。
- fixed-head acceptance 对 v3 activation、双索引 activation receipt、claim receipt、
  active/consumed offer、envelope ID、role/config/execution bundle、route decision 与
  offer window 执行完整绑定；缺 receipt、receipt/claim 不匹配和 route digest 漂移均拒绝。
- 官方 bin 与 library 启动路径在普通 Python 环境禁用 payload bytecode 写入；52 个
  payload 文件仍全部由 source/manifest/lock 精确声明，未忽略任何 undeclared file。
  `source.toml` 在解析前用 `lstat` 拒绝 symlink。
- `project-remove` 允许已缺失的受管文件并可重试清理，其余仍存在文件的内容、mode
  或类型漂移继续拒绝；未引入 transaction、journal 或 freeze。
- claim 固定 `executionBundleDigest` 与 `routeDecisionDigest`；delivery 必须单独提供
  `candidateOutputBundleDigest`，状态模型强制执行摘要与 claim 一致。
- main 输出不含 capability、机器路径、prompt/transcript、凭据或原始 agent/thread
  identity。历史 M2-A handshake 只按已验收旧摘要校验，不随当前候选 bundle 重解释。

## Digests

- Historical M2-A/M2-B gate bundle: `5b115a918d8a5241551b0be8dac657a448e1b912815493e1988007b1f4ed1880`
- Candidate output bundle: `3a95bab5083bd2ff37e29ef4f367860bb3f80a63265ec8163334da310e3c556f`
- M2-C evidence digest/file SHA-256: `5e3a9b2efbafb75986c24f5f15f93c99f734bde1b716f23a58ca7c72ed11db13` / `b3b61f5fb86bec3034fd9df533af59f2fdd6897feebb18044c620f6878102ea5`
- Executor role/config: `08bfcea59c7be5ea03cd7958ac2195e6a0a5703823a739fd819aabd6c48427dd` / `10c0675808974609242280367f2e7aea07e61dd839a1ec2e244d53a9b6c74e3e`
- Project config/inventory: `9a9bc7db827ea68cf4ba6761902e91ce4982fbaec25b8d68b70c4c790cef35d0` / `ad581ad96a9a58226bae4330f650ea31c52d049b0c355ee081bc98a3d7a4b271`
- Skills: main `955471652de96a0de4e82e462b60700ff2d4b7a76afb6dcc32769fa41787ede6`; execute `a85105da54144a964e832affcd552daadbc09534e57c45d46f8cde2d1f4ce836`; local verify `3ec80b83782c7e1ff69d7fb72e6fb1665c6a5add66d97c19dd235908c33d6ad3`; CI monitor `45589e31a888437774b67c9c20be2ab4075c48bbb9de918f8ad7c068c82dc7a0`

M2-C evidence 中的 synthetic end-to-end flow 使用当前 candidate bundle 作为测试执行
bundle，并用 `d` × 64 作为独立 synthetic output digest；它不是本任务的 claim 或
delivery 事实。当前 candidate output 只有在独立验收后才能成为后续任务的 accepted
execution-bundle upgrade。

## 验证

| Contract | Result |
| --- | ---: |
| M2-C bridge/staging/recovery/mutation（两次，默认 Python） | 30/30 + 30/30 |
| `git archive` 纯净副本 M2-C（默认 Python） | 30/30 |
| M1 task-core | 104/104 |
| M2-A role-routing | 70/70 |
| Foundation | 53/53 |
| Watcher core | 47/47 |
| Watcher live-negative | 15/15 |
| Historical M2-A runner on current candidate | 70/70 |

两次 M2-C evidence 来自互不相交的干净系统临时根，文件逐字节一致，SHA-256
均为 `b3b61f5fb86bec3034fd9df533af59f2fdd6897feebb18044c620f6878102ea5`；
临时根结束为空。两个 staged project 的 inventory 与输出逐字节一致，candidate
Git 无污染。`git archive` 纯净副本在未设置 `PYTHONDONTWRITEBYTECODE` 时完整通过，
其 payload 未生成 `.pyc` 或 `__pycache__`。

生产保护快照 before/after 均为
`957e7ddbb7ed95e79f0774c131421514473bbd5e50939668803b038ced31434e`
（2295 entries）；AIO before/after 均为
`27358a2dcde47816b6dd213005167645b0a86644693e446ca4da8c1c656d98c3`
（15675 entries）。未安装依赖，未运行历史 live probe、真实一小时等待、大型构建
或真实 fresh-main staging。

仓库没有 AIO 专用 `scripts/check-local-verification.mjs`，因此未运行该外部固定
脚本；本仓库使用 dedicated M2-C 双 evidence、全部专属保留回归、canonical
manifest/lock 生成、diff/污染/敏感标记检查作为验证合同。

非阻塞 residual risk：若项目 inventory 本身在 remove 中断后被外部删除，重试无法
重新证明文件归属；本轮按明确放宽不为该场景增加 transaction/journal/freeze。

## 停止边界

PR #7 没有 configured status checks，不表述为 CI 成功。最终 push 后必须核对本地
HEAD、upstream、origin branch 和 PR head 完全一致并保持 worktree 干净。本 session
停在 fixed-head 独立验收前：不验收、不合并、不清理 worktree/branch、不启动 fresh
main 或 M3、不修改生产 `~/.codex` 或 AIO。
