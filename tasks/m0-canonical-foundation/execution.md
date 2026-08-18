# GKD-M0-A：canonical 基础与章程

## 给执行 session 的唯一入口

在新的顶层 Codex session 中打开本 worktree，然后只发送：

> 读取 `tasks/m0-canonical-foundation/execution.md`，严格按文档执行 GKD-M0-A。你是人工开启的顶层 execution session，不是 main，也不是默认 subagent；完成后停在 PR ready 和固定 head 交付，不得合并或开始 GKD-M0-B/里程碑 1。

执行 session 必须使用 GPT-5.6 Sol、`xhigh`。无法确认模型或 reasoning effort 时停止，不得降级。

## 任务身份

- 状态：`awaiting_manual_execution`
- 执行路线：D2 已固定为 `unsupported`，使用人工顶层 execution session
- 仓库：`KNaiFen/gkd`
- 分支：`task/m0-canonical-foundation`
- Draft PR：`https://github.com/KNaiFen/gkd/pull/4`
- 固定 base SHA：`88325398c7bb0b6559927a707634e39016726695`
- 本机 worktree：`/Users/knaifen/Documents/Codex/gkd-worktrees/m0-canonical-foundation`
- 前置结论：M-1C / PR #3 / merge `afacf490aee948a0e70910304976da6c667375fa`，`unsupported`，manual-only
- 冻结计划：`GKD 本体实施计划 v1` 里程碑 0
- 覆盖：canonical bundle/manifest/version/digest/临时安装骨架；单一权威 VISION；decision/ADR/Alignment 文档分层；短时 L0/L1 合同

## 授权与硬边界

用户已授予 `gkd_core_implementation`。本任务允许：

1. 修改当前 task worktree 中的 canonical 基础、VISION、文档分层、确定性脚本、短时测试、任务记录和脱敏证据。
2. 使用 Python 标准库和临时目录验证两次安装、digest、drift 与负向合同。
3. 提交并推送任务分支、更新 PR、读取 PR 状态。

本任务禁止：

1. 写入或安装到生产 `~/.codex`，修改生产配置、Skills、roles、plugins、MCP 或用户凭据。
2. 修改 AIO Coding Hub、`KNaiFen/gkd-sandbox`、GitHub settings、Secrets、runner、Actions policy、tag 或 Release。
3. 实现里程碑 1 的 task state machine、offer/claim、worktree locator、accept/merge CLI，或里程碑 2 之后的角色、CI、Skills 与发布机制。
4. 声称7个 Skills、3个角色、完整 installer/doctor、L0-L4 或 production bundle 已完成；本任务只能建立可扩展的 bootstrap foundation。
5. 调用 live watcher probe、真实 subagent、付费 API、长时测试、大型构建、Rust/Tauri 或依赖安装。
6. 让子代理承担调查、设计、编码、测试或判断。

若实现需要材料性改变批准的 VISION 语义、bundle 边界或生产安装授权，停止并记录 blocker，不自行扩权。

## 目标结果

本任务只能输出：

- `canonical_foundation_ready`：下面全部合同通过，可进入后续 manual milestone task。
- `blocked`：基础合同无法在授权范围内安全成立。

不得输出 production-ready、release-ready、auto-ready 或 D2 supported。

## 启动前置门

1. 核对 worktree、branch、origin、固定 base 和 PR；不得在 main 工作。
2. fetch `origin/main`。main 只允许比固定 base 多 M0-A 登记类 `.agents` 提交；合入并记录实际 synced main SHA。出现产品代码或未知修改时停止。
3. worktree 必须干净；确认 GPT-5.6 Sol / xhigh，并确认 M-1C `unsupported` 与 manual-only 状态未被改写。
4. 先运行现有 M-1B 47项和 M-1C 15项短时 tests；不得重跑四场景 live probe。

## Canonical bundle foundation

### 源与结构

1. 建立一个明确的 canonical source 根、版本化 manifest schema、规范化文件清单/lock 和窄 CLI/脚本入口。目录命名应通用，不含AIO、用户名、本机绝对路径或当前 worktree。
2. manifest 只声明本任务实际存在的 bootstrap components。未来7个 Skills、3个角色和其他里程碑组件可扩展，但当前不得放入虚假占位文件或声称已安装。
3. 使用明确的非发布 development version；不得创建正式版本、tag、Release 或暗示兼容性承诺。版本与schema升级规则要有最小说明。
4. content digest 由固定脚本按规范路径、类型、mode 和文件内容生成；排除 Git、临时目录、mtime、绝对路径和输出目录。自引用字段必须通过明确的 canonical 规则解决，不能手算或手填。
5. 同一 Git tree 重复生成必须字节一致；文件增加、删除、内容或可执行 mode 改变必须改变 digest 或被拒绝。未知未声明文件不得悄悄进入安装。

### 临时安装与 drift

1. installer 只接受显式、已存在安全边界内的临时目标目录；本阶段不得提供生产安装开关或默认到用户 home。
2. 安装必须使用 source manifest/lock，拒绝路径穿越、symlink逃逸、缺失/多余声明、digest不匹配和目标内未知覆盖。
3. 两个独立临时 CODEX_HOME/目标安装得到相同 bundle version、content digest 和规范化已安装清单；重复安装幂等。
4. 提供最小只读 verify/version surface：报告版本与digest，检测安装后内容漂移、缺失和多余的 bundle-owned 文件。不要提前实现完整 production doctor。
5. 机器结果由脚本生成 JSON；Agent 不得手填 manifest、lock、安装结果或证据状态。

## 单一权威 VISION

在仓库根创建唯一 `VISION.md`，只包含以下七类长期内容：

1. 使命。
2. 服务对象与用户承诺。
3. 成功标准。
4. 核心原则。
5. 冲突时的决策顺序。
6. 明确非目标。
7. 演进规则。

必须表达已批准的上位思想：长时间 Agent 编码工作应用户可控、可恢复、可验证、可移植，并保护资源受限本机；GKD主动调查和推荐，但材料性方案、自动化与外部动作由用户决定；Agent负责开放式判断，确定性脚本负责脆弱状态；证据绑定固定事实；保持单事实源/单writer、静默编排、本机大型产物保护、基于实时事实的CI策略、最少必要流程成本、GitHub通用机制与项目policy分层、数据防泄漏而非Cyber平台、GKD发行自验证和长任务持久恢复。

冲突顺序固定为：用户已批准意图与数据保护 > 正确性和固定证据 > 可恢复与可移植 > 本机资源边界 > 目标项目速度/成本policy > 流程与上下文简洁。

VISION 禁止包含：

- `GKD-001..016` 映射、decision目录或当前产品承诺索引。
- 原则机器ID。
- 命令、模型名、reasoning effort、具体runtime/轮询时长、runner label、schema字段、版本号、SHA、路径或其他易变实现常量。
- 当前M-1C失败细节、任务进度、安装步骤或第二套操作手册。

README只用短段落介绍并链接VISION；AGENTS只增加“材料性规划前完整读取并遵守VISION”的硬规则，不复制正文。

## 文档分层与 Vision Alignment

1. 建立长期 decision/ADR 的明确位置与最小模板，说明VISION、decision/ADR、AGENTS、Skill/reference、repo policy各自职责，不把当前 `.agents` 运行记忆伪装成完整历史迁移。
2. 建立短 `Vision Alignment` 模板或确定性生成入口，只包含：可读原则名称、支持方式、张力/偏离、是否改变当前材料性承诺，以及仅在需要时引用方案自身的decision/ADR。
3. Alignment结构由脚本生成，Agent只填写可读分析；不得要求Agent手填机器JSON、digest、ID或状态。
4. 与VISION一致不等于获得授权；模板必须明确 executor/acceptor 不得借愿景扩大获批范围。

## 必测合同

至少覆盖以下短时、无依赖合同：

1. manifest/lock schema、canonical排序、重复生成字节一致。
2. 两个临时目标安装version/digest/清单一致，重复安装幂等，生产home未变化。
3. 内容、路径、mode、缺失、多余、symlink与目标drift的positive/negative tests。
4. 拒绝源码或安装清单中的AIO、用户名、本机绝对路径、临时根和未声明文件。
5. VISION恰有七类必需章节；缺章、重复章、决定索引、机器原则ID、模型/runtime/runner/schema等易变常量会失败。
6. README/AGENTS只链接、不复制VISION正文；文档分层和Alignment模板字段完整。
7. 修改普通措辞不应误改manifest机器状态；修改bundle-owned内容必须改变digest。
8. 现有M-1B 47项与M-1C 15项短时 tests继续通过；不运行M-1C live probe。

关键门需要negative/mutation test，确保删除digest校验、允许生产默认路径、允许手填lock或从VISION移除章节时测试会失败。

## 允许的主要文件

- 根 `VISION.md`、`README.md`、`AGENTS.md`
- canonical bundle/manifest/lock/installer/verify 的单一目录与窄脚本入口
- `docs/decisions/**`、`docs/adr/**`、Alignment模板
- 对应 `tests/**`、`evidence/m0-canonical-foundation/**`
- `tasks/m0-canonical-foundation/**`
- `.agents/**` 状态更新

不要修改已合并 M-1 watcher evidence，除非短时测试发现真实回归；发现回归时停止并报告，不顺手重写历史证据。

## 验证与交付

1. `git diff --check`。
2. 运行本任务全部L0/L1短时 tests、M-1B 47项和M-1C 15项negative tests；禁止依赖安装和live canary。
3. 两次从clean临时目录生成foundation evidence，规范化digest必须一致；允许临时路径不同，但不得进入证据。
4. 扫描安装产物、manifest、lock、证据和VISION，确认无用户名、本机绝对路径、凭据、AIO专用标识或未声明文件。
5. GitHub无required checks时记录 `required_checks_not_configured_bootstrap`，不得声称CI成功。
6. 填写 `delivery.md`：outcome、implementation/evidence commit、PR、文件、命令、合同矩阵、bundle development version、content digest、证据digest、生产home不变证明、残余风险和后续任务建议。
7. 使用简短中文提交说明提交、推送并将PR解除Draft；确认worktree clean与远端head一致。
8. 回报完整40位head、实现/证据commit、outcome、测试数、bundle version/digest、evidence digest、PR状态和未通过项。
9. 停止。不得合并、生产安装、创建tag/Release、启动后续session或开始里程碑1。
