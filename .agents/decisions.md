# Decisions

- [2026-08-17] 建立独立 GKD 开发仓库。
  - Why: 将 GKD 的 Skills、roles、脚本、schema、安装与测试从消费项目中分离，并使用 Git 管理版本。
  - Impact: 后续经批准的 GKD 实现和专属测试进入本仓库；消费项目只保存固定版本、digest 和项目 adapter。

- [2026-08-17] 完整 GKD 测试不挂到消费项目的每个 PR。
  - Why: 这些测试验证的是 GKD 工作流发行包，而不是普通产品功能。
  - Impact: GKD 源码变更运行 hermetic 测试，release candidate 运行适用的 agent/live 验证；消费项目仅在升级 bundle 或修改 GKD adapter/integration 时运行兼容性 smoke。

- [2026-08-17] GKD 上下文治理只采用 Skill无损去重、AGENTS无损压缩和角色最小上下文。
  - Why: 用户不需要专用profile、全局能力裁剪或token基线工程，只要求消除已证实的重复并减少规则与角色材料冗余。
  - Impact: 禁用Codex对6组 `.agents` Skill副本的发现但不删除原件；压缩AGENTS时保留全部硬边界；由确定性CLI生成角色材料清单。context window、插件/MCP、输出预算和fresh canary不在范围内。

- [2026-08-17] GKD新增CI优化与逐项审查两个Skill，并共享确定性审查core。
  - Why: CI领域判断与审查状态控制需要独立触发，但批准、部分决定、游标和恢复不能重复手写；用户还要求Skill主动发现本机/GitHub条件，并在用户不知道方向时主动推荐。
  - Impact: bundle从5个Skill扩展到7个；CI Skill使用资源与速度/成本预设，资源受限预设明确禁止本地产生大型依赖/构建/cache产物，临时目录事后清理不能绕过峰值磁盘门；审查Skill提供targeted/guided/recon三种入口；两者默认停在方案阶段，全部机器状态由CLI生成。

- [2026-08-17] GKD根目录使用单一权威 `VISION.md` 保存指导思想。
  - Why: 未来开发需要理解GKD的使命、成功标准和冲突取舍，但愿景不能变成决定索引或第二套操作手册。
  - Impact: VISION只写使命、用户承诺、成功标准、可读原则、冲突顺序、非目标和演进规则；README/AGENTS只链接，具体决定留在decision/ADR/test，后续方案使用短Vision Alignment。

- [2026-08-17] GKD本体与AIO接入使用独立实施计划和授权。
  - Why: GKD是canonical产品，AIO只是首个消费项目；批准开发GKD不能隐含授权修改AIO或生产用户安装。
  - Impact: 先独立开发/验证GKD本体，再单独批准生产 `~/.codex` 安装，最后单独批准AIO pin、adapter和旧实现迁移。核心缺陷返回GKD任务，不在AIO永久fork。

- [2026-08-17] D2基于multiagentv2，必要时使用外部app-server watcher。
  - Why: GPT-5.6 Sol明确使用multiagentv2，app-server提供结构化thread状态与事件；用户允许原生能力不足时由外部脚本实现，并愿意把最大等待调长。
  - Impact: 临时配置先验证12小时单次等待；外部watcher只用版本化app-server协议，内部每小时检查且健康不返回main。正常final自然唤醒；异常可interrupt child，并用绑定expectedTurnId的 `turn/steer` 唤醒parent。生产等待配置和watcher安装另走生产安装授权；两条路线失败时manual-only，不退回D1。

- [2026-08-17] GKD本体实施计划v1获批。
  - Why: 16项决定、拆分授权边界和multiagentv2 D2路线已形成依赖有序的本体计划。
  - Impact: `implementation-plan-gkd.md` 是GKD本体实施的唯一依据；本次批准不等于开工，不授权AIO、生产安装、GitHub外部动作或自动executor。

- [2026-08-17] GKD本体使用前期manual、后期条件auto的hybrid B路线。
  - Why: bootstrap阶段尚无可信executor/claim/D2，不能用未来能力自证；核心通过后可减少后续人工开session。
  - Impact: 里程碑-1/0/1/2由人工顶层session执行。只有role config、offer/claim和D2证据绑定固定bundle digest后，里程碑3/4/5才获准由main启动专用 `gkd_executor`；任何门失败继续manual，禁止worker回退。

- [2026-08-17] GKD使用源码仓库与L4演练仓库分离的双public GitHub仓库布局。
  - Why: 源码仓库需要承载正常PR CI和发布证据，L4 live canary会创建测试branch/PR/check并需要独立清理，隔离后不会污染源码或消费项目。
  - Impact: 计划使用 `KNaiFen/gkd` 作为canonical source remote，使用 `KNaiFen/gkd-sandbox` 作为专用L4 sandbox；只使用标准GitHub-hosted runner。此决定只批准布局，不代表仓库已经创建，也不授权创建仓库、修改GitHub设置、运行canary或发布。

- [2026-08-18] GKD本体采用 `implement_and_merge_on_acceptance` 外部动作模式。
  - Why: 用户要求完整流程在既定方案和授权范围内自动提交、运行CI、验收并合并，避免每个任务在相同边界上重复确认。
  - Impact: 未来明确授予实施授权后，任务级action authorization可允许推送、创建/更新PR、范围内CI修复，以及在固定head required checks全绿且独立acceptor无阻塞结论后自动合并。当前选择不执行任何外部动作，也不授权付费runner、Secrets、仓库可见性变更、生产安装、AIO接入、tag或Release。

- [2026-08-18] 中间任务采用 `closeout_only`，本计划最终GKD bundle发布已提前授权。
  - Why: 中间任务无需制造无意义版本发布；最终release candidate一旦通过完整测试和验收，再重复询问不会增加新的决策价值。
  - Impact: 每个中间任务合并后只归档。完成本次已批准GKD本体计划、固定version/digest、L0-L4全部适用门禁成功且最终acceptor无阻塞后，可直接创建首个GKD版本tag和GitHub Release，不再请求发布确认。材料性计划变化会使该预授权失效；生产 `~/.codex` 安装和AIO接入始终另行授权。

- [2026-08-18] 用户明确授予 `gkd_core_implementation`。
  - Why: 16项问题决定、本体计划、执行路线、GitHub布局、动作模式和最终发布边界均已逐项确认。
  - Impact: 允许在本仓库、临时测试环境、`KNaiFen/gkd` 与 `KNaiFen/gkd-sandbox` 内按冻结计划实施，包含必要的public仓库创建、标准Actions、任务PR、范围内CI修复、固定head验收后合并及最终条件发布。生产 `~/.codex`、AIO、付费runner、Secrets和计划外GitHub设置不在授权内。

- [2026-08-18] 已创建批准的双public GitHub仓库。
  - Why: GKD源码需要canonical remote，L4 live canary需要独立外部副作用边界。
  - Impact: `KNaiFen/gkd` 已接收本地 `main` 规划基线并成为 `origin`；`KNaiFen/gkd-sandbox` 已创建但保持空仓库，待L4确定性canary实现后初始化。当前未配置Secrets、付费runner或无workflow可绑定的required checks。

- [2026-08-18] 当前Codex原生单次等待不能满足12小时D2合同。
  - Why: 在 `codex-cli 0.147.0` 中把 `features.multi_agent_v2.max_wait_timeout_ms` 设为43,200,000会在启动时被配置解析器拒绝，并明确要求该值至多为3,600,000。
  - Impact: `GKD-M-1A` 只需用短时可复现证据记录 `native_insufficient` 及其余协议能力，不运行65分钟等待；里程碑-1必须进入已批准的外部app-server watcher路线。用户配置先恢复为3,600,000，禁止用连续短wait拼接12小时语义。

- [2026-08-18] `codex-cli 0.147.0` 原生 multiagentv2 不满足 GKD D2。
  - Why: 启用 multiagentv2 后，3,600,000ms 配置可加载而43,200,000ms被解析器拒绝；正常child final可自然唤醒parent，但不能补足单次12小时等待与小时内部watchdog合同。
  - Impact: `GKD-M-1A` 结论固定为版本绑定的 `native_insufficient`；六项仅有协议表面或缺少安全短时行为fixture的合同保持 `unknown`，不得升级为支持。后续只能另立外部app-server watcher任务或保持manual-only。

- [2026-08-18] `GKD-M-1A` 已通过固定head验收并合并。
  - Why: 主会话逐行审查探测器、测试与证据；独立复现7项自测试、1小时配置成功、12小时配置拒绝及双次capture稳定性，未发现阻塞finding或真实敏感数据。PR无required checks被保留为bootstrap缺口，未伪装为CI成功。
  - Impact: PR #1 head `bd8332aba8c52c8a5bf276d17433dfbd37ed4a38` 以merge commit `0cc09e9c794f73876c84dd63effe87fde355add8` 进入main。里程碑-1继续建立独立 `GKD-M-1B` 外部watcher任务；不得复用native路线。

- [2026-08-18] `GKD-M-1B` 外部 watcher core 达到 live gate 前置条件。
  - Why: 版本/schema fail-closed、严格请求边界、单 writer JSON-RPC、静默小时健康检查、绑定 child interrupt 与 expected-parent-turn steer、MCP framing、并发隔离和敏感数据 containment 已由 37 项标准库 hermetic/subprocess 合同测试证明。
  - Impact: 当前唯一允许结论为 `core_ready_for_live_gate`。真实 Codex app-server 连接、12 小时 MCP 阻塞、正常 final 去重、异常 steer 和 parent context trace 必须留给独立 `GKD-M-1C`；在该门通过前禁止启用 auto route 或宣称 `external_watcher_supported`。

- [2026-08-18] `GKD-M-1B` 固定head验收的6项阻塞finding已修复并重新取证。
  - Why: 旧head允许任意64位digest、未绑定thread/session归属、interrupt后未确认终态、误分类steer错误、取消/EOF关闭不确定，并允许credential-shaped identity回显；这些均违反冻结安全合同。
  - Impact: 实现/证据提交 `b9fa7978298fea1fe1f14e8b992eb4f2ec2bf7b3` 增加精确runtime evidence绑定、控制前归属复核、有界终态确认、窄错误分类、确定性关闭和身份凭据样式拒绝。47项合同连续两次通过，结论仍仅为 `core_ready_for_live_gate`；PR #2必须在新固定head重新独立验收，本session不合并或启动M-1C。

- [2026-08-18] `GKD-M-1B` 新固定head已通过独立验收并合并。
  - Why: 主会话重新审查完整差异和6项修复，独立运行47项合同，并两次重生成与仓库完全一致的证据；PR live head、归属、可合并状态与无checks的bootstrap事实均已复核，未发现阻塞finding。
  - Impact: PR #2 head `98df6ba122d9fe8aed230094ed806010e7002aa7` 以squash commit `1d303456f2afcaa4e5fd0353232e30c5c6b63a33` 进入main。结论仍只允许 `core_ready_for_live_gate`；下一步必须由独立人工顶层session执行 `GKD-M-1C` live gate，未经该门不得启用auto route。

- [2026-08-18] `GKD-M-1C` 外部 watcher live gate 输出 `unsupported`。
  - Why: 四个真实 fresh Codex/app-server/MCP 场景均未稳定执行固定的先 spawn child、后调用 live gate 顺序，无法形成无猜测的 parent/child/session/turn 绑定；因此 Gate 1-8 缺少 required live facts。数据最小化、生产配置前后快照和最终运行清理通过，但不能替代 live 行为证明。
  - Impact: 禁止宣称 `external_watcher_supported`、启用 auto route、安装生产 watcher 或开始里程碑 0。PR #3 仅交付可复现 fail-closed probe、脱敏证据和失败边界；manual handoff 继续可用。

- [2026-08-18] `GKD-M-1C` 的 `unsupported` 结论已通过独立验收并合并。
  - Why: 主会话审查live probe、adapter、15项negative tests和机器证据，独立复验M-1B 47项、M-1C 15项，并重放四个真实场景；重放仍为Gate 1-8 fail、Gate 9 pass，normalized digest保持 `bc3237802b839565b74665381a6df2cdbf920a13d9cbb48f8daddd9d29adf610`，配置前后匹配且无已知残留。
  - Impact: PR #3 head `4332cea7aecc7540640add626ddca6b9b3d8cbad` 以squash commit `afacf490aee948a0e70910304976da6c667375fa` 进入main。auto route在本次计划中保持禁用，但hybrid B允许后续里程碑继续人工交接；里程碑0不再被M-1C执行session的暂停边界阻塞。

- [2026-08-18] `GKD-M0-A` canonical基础达到人工交付门。
  - Why: 单一canonical source、生成式manifest/lock、临时边界installer、只读verify/version、唯一VISION与文档分层已由44项foundation合同、47项M-1B回归、15项M-1C负向回归和两次字节一致证据证明。
  - Impact: development version固定为 `0.0.0-dev.0`，content digest为 `9be34162a4e4125f2f56d4d8148140e022f24cba46abbc56512ea0e8afb2a30f`，结论仅为 `canonical_foundation_ready`。PR #4必须在新固定head独立验收；不得据此生产安装、发布、启用auto route或开始M0-B/里程碑1。

- [2026-08-18] `GKD-M0-A` 首个固定head验收发现3项阻塞合同缺口。
  - Why: 独立复验106项既有测试均通过，但新增反例证明源码schema mode改变不影响digest、已安装metadata mode改变仍被verify误报为0644；evidence output位于protected root时会在after快照后写入并仍声明unchanged；污染扫描把裸用户名和任意`aio`子串作为禁词，导致跨机器误杀。
  - Impact: PR #4 head `0f69a4ad34d095d70f6d5e5ed93569193ad75578` 不得合并，PR转回Draft。原execution session必须修复metadata mode绑定、protected/output/cleanup终态顺序和通用污染边界，并补旧实现失败的负向测试；新push后重新固定完整head验收。

- [2026-08-18] `GKD-M0-A` 首轮验收的3项阻塞finding已修复并重新取证。
  - Why: source与installed metadata实际mode已fail-closed；evidence output与source/temp/protected面经resolve后必须不相交，临时安装和staging清理完成后才允许最终protected快照与发布；通用污染扫描只识别完整机器路径，仓库专用标识移到最终evidence边界。新增9项foundation负向/变异合同使旧实现失败。
  - Impact: implementation/evidence commit `3bab17697735adcf85e1214d6580966a7e896f47` 通过53项foundation、47项M-1B、15项M-1C negative和两次字节一致证据，content digest更新为 `0b8b2487640ff2c78360a18e7f24304f72a8e8c8b5cbd1317ef833c323726228`。结论仍仅为 `canonical_foundation_ready`；PR #4必须在新固定head重新独立验收，本session不合并或开始后续任务。

- [2026-08-18] `GKD-M0-A` 新固定head已通过独立验收并合并。
  - Why: 主会话重新审查完整差异和3项修复，独立运行foundation 53项、M-1B 47项及M-1C negative 15项；两个隔离临时根生成的证据与仓库提交逐字节一致，内部evidence digest保持 `ac463b216718f4a49a7d2dd89198fc83403afd2ecd4f83a690622d2f517fd494`，临时根最终为空且生产保护面不变。PR live head、base、可合并状态与无configured checks的bootstrap事实均已复核，未发现阻塞finding。
  - Impact: PR #4 head `68c418aef398dd6c2a3576c330d744e5d351acfa` 以squash commit `2207645ab7a3bfc4b0ad4a15cf4bbe743612933c` 进入main。结论仍只允许 `canonical_foundation_ready`；下一任务必须继续由独立人工顶层session建立和执行，不得据此生产安装、接入AIO或提前开始里程碑1。

- [2026-08-18] 里程碑0完成，撤销未定义的M0-B占位。
  - Why: 冻结计划中里程碑0只有canonical基础、单一权威VISION和文档分层三项正式范围，均已由M0-A实现并通过终验；计划没有批准任何M0-B具体范围，不能把执行文档中的停止边界误当成新任务定义。
  - Impact: M0-A终态记录保留在 `tasks/m0-canonical-foundation/acceptance.md`。完成worktree和分支清理后，下一步直接规划里程碑1的 `GKD-M1-A`；自动executor仍受D2 `unsupported` 阻断，继续采用人工顶层session。

- [2026-08-18] `GKD-M0-A` 收尾清理完成。
  - Why: 终态验收记录已进入main，候选worktree在删除前保持干净且tree与squash merge一致；用户明确允许忽略残留交互式shell的cwd后执行清理。
  - Impact: `/Users/knaifen/Documents/Codex/gkd-worktrees/m0-canonical-foundation`、本地 `task/m0-canonical-foundation` 和远端同名分支均已删除。bootstrap任务文档原位保留；因本仓库尚无 `.trellis/scripts/task.py`，未伪造task archive或validate结果。

- [2026-08-18] D2等待合同改为连续一小时原生等待。
  - Why: 用户放弃外部app-server、共享runtime、PTY和CLI唤醒方案，明确选择由main连续执行多轮一小时 `wait_agent`，并由Skill约束健康等待时不产生多余输出。
  - Impact: `GKD-M-1A` 的 `native_insufficient` 和 `GKD-M-1C` 的 `unsupported` 继续作为旧“单次12小时/外部watcher/健康零父上下文”合同的历史事实，不再阻止修订路线。新路线要求目标运行时实际接受 `wait_agent(timeout_ms=3600000)`；每次健康超时后main不得发commentary、分析、更新计划、读取仓库/worktree/PR/CI或调用状态旁路，只能立即对同一executor再次等待。child终态、错误、用户介入或claim后12小时deadline结束循环；deadline时只终止绑定executor一次并返回单一timeout，不重试或换agent。
  - Evidence boundary: 每次wait工具调用与timeout结果仍会进入父内部上下文，Skill只能消除自愿文本和额外工具噪声，不能声称零上下文。当前会话暴露的工具参数上限为360,000ms，因此auto route仍fail-closed；不得用十轮6分钟等待冒充一小时。里程碑1/2仍由人工顶层session完成，之后只有固定role、offer/claim及实际一小时等待门全部通过才可启用专用executor。

- [2026-08-18] `GKD-M1-A` v1 规划与人工交接已建立。
  - Why: 冻结计划已批准里程碑1的三状态门禁、clean-main/worktree、portable locator、offer/claim事务和窄accept/merge范围；现有bundle尚无可信task CLI，必须继续使用bootstrap人工交接，不能让main或候选代码自托管本任务。
  - Impact: 任务固定base为 `1335ac6a9a4dbb5c63570f5a02ba9e713705eebd`，branch为 `task/m1-deterministic-task-core`，planning head为 `b1e8b8d9f00ad53b68162c240134c3cd740d937a`，Draft PR为 `KNaiFen/gkd#5`。任务分支中的 `requirements.md`、`plan.md`、`execution.md` 是bootstrap审批锚；不手填 `task.json`，不使用候选 `gkd-task` claim/deliver/accept/merge自身PR。执行者必须是GPT-5.6 Sol / xhigh的独立人工顶层session，停在PR ready与固定head交付；main当前只登记和交接。

- [2026-08-18] `GKD-M1-A` 确定性任务核心达到人工交付门。
  - Why: 独立execution session实现独立`gkd-task`、三状态规划与授权、clean-main/worktree、portable locator、runtime attachment、offer/claim fencing、锁/CAS/journal、doctor/migration及trusted fixed-tree acceptance；95项task-core合同含真实bare Git/worktree、双subprocess claim、fake GitHub和9项mutation均通过，保留的115项回归通过，两次clean临时根证据逐字节一致且生产保护面不变。
  - Impact: implementation/evidence commit固定为 `1798b0f2c32571c803c399179c27090f94d21c0a`，development content digest为 `f29a594cd138a1b4e039b1411b953a6795f9b21a27b6086fdd540479c408faeb`，evidence digest为 `164ab691af9fa1af9137386da2169aba3cd065793366815d53077557f69b3774`。结论仅为 `deterministic_task_core_ready`；PR #5仍须在最终delivery head独立验收。本结论不启用role/auto route/一小时wait/CI monitor，不授权生产安装、发布、AIO接入，也不允许本session验收或合并。

- [2026-08-18] `GKD-M1-A` 首轮独立验收阻塞已在原execution session修复。
  - Why: PR #5固定head `c35ac55fd299196a463bc31e8ff0f98ef37c3858` 的独立验收证明candidate-only claim历史可触发accept/merge、offer/migration runtime写失败会留下不可重试tracked状态、phase字段组合缺少完整不变量，以及显式symlink candidate会在resolve后失去身份；该head未合并。
  - Impact: implementation/evidence commit `fee072bf6849d87ffd6a6323ea75a81af3504831` 增加machine-local claim receipt并绑定精确claim commit、committed journal和task/offer postimage；runtime side effect前置并按实际commit结果恢复；task validator增加phase矩阵、跨记录ID/epoch与history关系；locator/service/acceptance在resolve前拒绝显式symlink。103项task-core与115项保留回归通过，两次clean临时根证据逐字节一致；content digest为 `17e51babe52b18695abf270d7359b8c9ff343e017caf379a3274cb3f1e470aff`，evidence digest为 `98079835befaefe7eae74b5becfcbeb0eb5b559abcde3223171072ba7dd7377b`。结论仍仅为 `deterministic_task_core_ready`，必须在PR #5新fixed head再次独立验收，本session不得验收或合并。

- [2026-08-19] `GKD-M1-A` 续交验收的migration CAS/runtime残留已修复。
  - Why: PR #5续交fixed head `f34152ddbe79c3b9ff12c6e2e97121c34fd8fffa` 的独立验收确认前三项原阻塞闭环，但证明active v1 migration在`TransactionManager`校验stale head前已写入原本不存在的attachment，随后因HEAD不等于expected而不回滚；该head未合并。
  - Impact: implementation/evidence commit `0548eb52ead7191733c32129241168c2e7035a9f` 将attachment previous-image读取与写入/删除移入manager已持锁且通过head/revision CAS后的builder；未提交异常按previous image恢复。新增合同同时证明stale full head与stale revision返回稳定CAS错误、tracked head和全部runtime文件字节不变，并可用正确CAS重试成功。104项task-core与115项保留回归通过，两次clean临时根证据逐字节一致；content digest为 `fc96a10cb82b628bd14280e4e878417a3fbc7a1d560fac5a61bb7abe7f3c3024`，evidence digest为 `3f119831c41a18536318b621f21f13d8d18d115fce77e3fb97870a0148395569`。结论仍仅为 `deterministic_task_core_ready`，必须在新fixed head再次独立验收。

- [2026-08-19] `GKD-M1-A` 新固定 head 已通过独立验收并合并。
  - Why: main 对 `f0b339c0d52ae9325137e9f188b710645c2e2e80` 重新审查迁移事务增量并重放旧 stale-head 反例；attachment 变更只在同一 task lock 内通过 exact head/revision CAS 后发生，失败时 tracked head 与 runtime 全部文件字节不变且可正确重试。task-core 104 项在两个隔离临时根各通过一次，115 项保留回归通过，两份 evidence 与提交文件逐字节一致，未发现阻塞 finding。
  - Impact: PR #5 以 squash commit `5eb3bd34ef389361be2ba22df899ad088ef22da1` 进入 main，候选与 merge tree 均为 `938d02ed18a3ff256a63e707e01cbd3dc86d6649`。里程碑 1 完成，结论仅为 `deterministic_task_core_ready`；里程碑 2 仍由人工顶层 session 实施，auto route、生产安装、AIO 接入、tag 和 Release 均未因此启用。

- [2026-08-19] `GKD-M1-A` 收尾清理完成。
  - Why: 终态验收记录已进入 main；候选 worktree 删除前保持干净，head 为被验收的 fixed head，tree 与 squash merge tree 一致。
  - Impact: `/Users/knaifen/Documents/Codex/gkd-worktrees/m1-deterministic-task-core`、本地 `task/m1-deterministic-task-core` 和远端同名分支均已删除。任务文档原位保留；下一步可从同步 main 规划里程碑 2，但仍不得启用自动 executor。

- [2026-08-19] 里程碑 2 拆为角色路由核心与独立一小时 live gate。
  - Why: 固定角色、可信 activation/runtime evidence、manual/automatic 路由、确定性等待状态机、最小上下文和安装迁移属于可由 hermetic/L2 合同验收的实现面；真实 `wait_agent(timeout_ms=3600000)` 必须在固定 M2-A bundle digest 的 fresh runtime 独立证明，不能让同一实现 PR 自证平台 live 行为。
  - Impact: `GKD-M2-A` 由人工顶层 session 实现角色/路由核心，只允许短时隔离角色握手；通过并合并后再建立人工 `GKD-M2-B` 执行真实一小时 timeout 与 child early-final 门。两者全部通过前 auto route 始终禁用，禁止用更短等待、外部 watcher 或 generic worker 替代。

- [2026-08-19] `GKD-M2-A` v1 规划与人工交接已建立。
  - Why: 已验收 M1 CLI 的安装态 claim provider 故意 fail-closed，无法可信地让 M2-A 使用尚未实现的角色证据自管本任务；因此继续采用受审 Markdown、Git worktree 和独立人工顶层 session 的窄 bootstrap exception，不创建或伪造 task JSON/offer/claim/activation。
  - Impact: 固定 base 为 `839974fbcd9114e5a5ad3b8fa1d4c58e68cb90ea`，branch 为 `task/m2-role-routing-core`，planning head 为 `51fee63a8b600df4f94aa042ea42ef09e3b73986`，Draft PR 为 `KNaiFen/gkd#6`。execution session 只实现 M2-A，停在 fixed-head delivery；不得验收/合并、启动 M2-B、启用 auto route或修改生产/AIO。

- [2026-08-19] `GKD-M2-A` 固定角色与路由核心已实现，但交付结论固定为 `blocked`。
  - Why: 51 项 hermetic/L2 合同、M1 task-core 104、foundation 53、watcher core 47 和 live-negative 15 均通过，两次隔离安装/迁移 evidence 逐字节一致；但唯一一次获准的短时 fresh host handshake 只证明 custom role reference，未证明可信 custom role activation 或 parent/child terminal 归属。
  - Impact: bundle digest 固定为 `943301005912c05bb137d6c44a597e4569e05e9f0e738adaec4a8b675f654649`，M2 evidence digest 固定为 `efe08577c4eabfb91938d2d93473ed142ded4bbe4f651c591a8d830624fbec8c`；不得用 Agent 自述、fixture 或候选文件补足证据。PR #6 只交付 fixed head/Ready，不能验收、合并、启动 M2-B、执行真实一小时等待或启用 auto route。

- [2026-08-19] `GKD-M2-A` 首轮固定头验收拒绝并转人工返工。
  - Why: 对 PR #6 implementation head `cd8c89899039070c29b2c5209e7c5afaefba0616` 的独立复验发现三项实现级阻塞：迁移 rollback failure 会在 `MIGRATION_FROZEN` 后删除唯一 backup；activation provider/digest 由调用者自由选择且 activation 时间未绑定 offer 有效窗口；wait transition 忽略 `deadlineAt`，13 小时 observation 仍返回 `wait_again`。现有 M2 51、task-core 104、foundation 53、watcher core 47、live-negative 15 测试和 evidence 再生均通过/逐字节一致，但未覆盖这些反例。
  - Impact: main 在候选任务文档记录 F-001 至 F-004 的 `findings.md`，提交 `c4a737f` 并推送到 PR #6；任务保持未合并，execution session 只处理 findings 后重新交付。fresh trusted custom-role handshake 仍未建立（F-004），因此不得启动 M2-B、启用 auto route、安装生产 `~/.codex` 或接入 AIO。

- [2026-08-19] `GKD-M2-A` 实现级返工完成，但可信角色握手继续 fail-closed。
  - Why: migration rollback failure 现在保留 backup/stage/freeze；activation provider 固定由 locked bundle catalog 派生且绑定 offer window/activation/envelope；wait transition 在 absolute deadline 终止。全部短合同与两次隔离 evidence 通过，但唯一 fresh handshake 被宿主以 `gpt-5.6-sol` 不支持当前 ChatGPT-account runtime 拒绝，未产生 custom-role activation 或 child/parent terminal。
  - Impact: implementation/evidence commit 为 `b64cab4e76f5ddd372a682531fe5802067a3c1c0`，bundle digest 为 `6e9cc8a73fa9e80e3a3061114f53c3daf152439a2886e40000e07d19b9c37a6b`，evidence digest 为 `5092c31dd1aaab13623e1131da84e248eb4af0018ce0c37f1a63ba85161b00b6`。F-001 至 F-003 转待独立复验，F-004 与总体 outcome 保持 `blocked`；PR #6 保持 Draft，不得验收、合并、启动 M2-B 或自动路线。

- [2026-08-19] 用户授权 M2-A 使用本机登录态执行一次额外 custom-role 握手。
  - Why: 本机 `codex-cli 0.147.0` 只读 preflight 确认为 ChatGPT 登录；旧 temporary-home probe 的模型拒绝不能证明正常本机登录态不支持固定 Sol role。项目级 custom-agent 配置可以在不安装生产 bundle 的情况下让真实本机 Codex 加载候选角色。
  - Impact: M2-A requirements/plan/implementation 升为 v2。执行 session 可从干净临时 Git repo 使用项目级 `.codex/agents`/`.codex/skills` 和 `codex exec --ephemeral --ignore-user-config --json` 发起一次真实握手；只保留脱敏结构化事件。不得设置 alternate `CODEX_HOME`、直接读取/复制/编辑认证材料、修改生产配置、模型降级、重试或运行一小时门。宿主自行产生的 operational metadata 不作为配置或证据，也不得检查正文或清理既有状态。

- [2026-08-19] M2-A 续交验收新增 F-005 activation writer 阻塞。
  - Why: PR #6 head `0c200bc9cfbdf6da62e53ed6eb7ff579b964f3da` 的安装态 `gkd_role.activation.record_activation` 仍接受调用者构造的 observation 并写入同权限 runtime；独立临时复现可绕过 fail-closed CLI 后令 claim 进入 `implementing`。固定 provider 字段不能证明写入者是 host/main。
  - Impact: canonical/installable payload 必须移除候选可调用的可信 activation writer，test seam 只能存在于 tests；若宿主没有候选不可伪造的 receipt 边界，安装态 activation/claim 保持 fail-closed。F-005 与 F-004 均闭环前 PR #6 不得合并，auto route 保持禁用。
