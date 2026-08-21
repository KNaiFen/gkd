# GKD-M3-A 交付

## 结果

- Outcome: `fixed_head_ci_policy_ready`
- Fixed base: `d669c11735f1468127ce4b7b4699a19ef0984753`
- Claim base head: `9b5940900eb1745ff45731dfa5d260b9fdcb2bde`
- Claim: `a771ec4e79ea3148923adf04430892de0337028e3f3820e5c2dcdd49c35e3909`
- Implementation/evidence commit: `f3bff9359846d1819804dd926cd040bfedbf8ac8`
- PR: [KNaiFen/gkd#8](https://github.com/KNaiFen/gkd/pull/8)
- Accepted execution bundle: `1983f05b64860510bfb1af661e5458a6c7b660632479a33af46c27d35ff188d4`
- Candidate output bundle: `4d12c9973ea9302162493a5a71e25a4948b1f23991d30873c4a11ad691647aed`

本交付只实现 M3-A：通用仓库 CI policy、GitHub origin/base 一致性、固定头只读
terminal monitor、标准 Actions workflow、版本化本地 verifier，以及 task acceptance
对合法空格 check name 的兼容。M3-B 资源与 scanner、M3-C review core 与新 Skills
均未实现。

## 实现

- 在 `gkd_task.canonical` 提供共享 check-name 语法；task acceptance snapshot parser
  不再使用仅允许 identifier 字符的默认 regex，`GKD Verify` 等含空格的合法检查名可被
  exact-head acceptance 正确解析。
- `gkd_ci.policy` 复用同一 check-name validator，保持 policy、terminal schema、GitHub
  adapter 和 acceptance 的跨模块契约一致；未硬编码仓库、owner、分支或检查名。
- 新增一个正向空格检查名回归和一个删除显式 validator 的变异测试；生成器更新
  canonical manifest/lock，candidate bundle digest 与 evidence 重新绑定。

## 验证

唯一版本化 verifier：

`scripts/gkd-verify --base-sha d669c11735f1468127ce4b7b4699a19ef0984753`

终态为 `364/364`：M3-A `29`、task-core `128`、role-routing `70`、runtime-bridge
`37`、foundation `53`、watcher-core/live-negative `47`。未安装依赖，未运行历史 live
probe、M2-B 一小时实验、大型构建或 cache。

M3-A evidence 在两个互不相交的系统临时根生成，均为 `29/29` 且逐字节一致：

- Evidence digest: `07ccce79abd4f5598a33300bf587b7df18d16bf238664869ca1d704c083f9912`
- Evidence file SHA-256: `804bbfc12cef17697a515394df427abaf5b14a3753730556861ddcf4c3f1a401`
- Production before/after: `7611274708640cfdaa84e5756a7af0ab376fedbb338b67dac844bf1523277345` (`2295` entries)
- AIO before/after: `27358a2dcde47816b6dd213005167645b0a86644693e446ca4da8c1c656d98c3` (`15675` entries)
- 两个 evidence temporary root 均在发布前为空。

本任务新增 fixed head 的 policy-backed monitor 结果：

- Outcome: `success`
- Reason: `ALL_REQUIRED_CHECKS_SUCCESSFUL`
- PR/head: `8` / `f3bff9359846d1819804dd926cd040bfedbf8ac8`
- Expected/observed head: 完全一致
- Required checks: `GKD Verify` = `success`
- Observations/elapsed: `2` / `35` 秒
- Policy digest: `d77e68152843dcc1f470d88c76fe8c249ef803854048f4a9d42ed5cc92cd54c2`
- Monitor 为只读；未 rerun、dispatch、cancel、修改 PR metadata、accept 或 merge。

首次 monitor 调用误将短 SHA 手工扩展为错误的 full head，因而返回一次
`head_drift`；未产生任何 GitHub 写入。随后以 `git rev-parse HEAD` 得到上述 exact
head，重新运行同一只读 monitor 并获得 success。远端分支、候选 worktree 和本地 head
均已核对为同一 SHA。

## 停止边界

本 session 停在 exact claim delivery 与 trusted-main 独立验收之前：不验收、不合并、
不归档、不清理 worktree/branch、不启动 M3-B，不修改生产 `~/.codex`、AIO、sandbox、
仓库设置、Secrets、runner、tag 或 Release。
