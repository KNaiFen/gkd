# GKD Consumer Bootstrap Policy Binding Implementation

## Internal Design

新增的 policy input 只位于 task planning package root，文件名固定为 `policy.json`。task bootstrap 在创建 candidate 前确定 policy source：已有 base policy 或该单一 package input；两种来源都经同一 canonical policy parser 验证，并形成不可变 binding。source package 不进入 candidate，只有 canonical policy bytes 进入 bootstrap commit。

project staging 对首个项目采用同一受限 input，生成 inventory policy binding。bridge 只比较结构化 project-verify 与 task binding；不会接收 policy 路径、原始内容或可调用的 activation/claim 权限。acceptance 在所有 fixed candidate heads 上重验 policy binding。

## Execution Details

1. 扩展 task model/schema、documents/bootstrap service/CLI 与 tests，加入 policy binding 和 legacy read boundary。
2. 扩展 role project staging/verify/CLI 和 tests，受管 policy 输出及 inventory v2 绑定必须事务化、可复验、不可被候选 workspace 冒用。
3. 扩展 bridge、acceptance 和 corresponding test fixtures，确保任何 project/task/claim/head policy drift 在写入或 merge 前拒绝。
4. 更新 manifest/version/release inputs、README 与 task evidence；运行 `scripts/gkd-verify --base-sha <full-base>`，生成双 evidence。
5. executor 将 implementation 与 evidence 提交，先提交 `delivery.md`，再完成 final delivery state、推送 PR 和等待 fixed-head CI；不合并、不发布、不安装或启动 AIO。
