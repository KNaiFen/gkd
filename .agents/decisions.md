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

- [2026-08-19] GKD-M2-A F-005 已整改但可信宿主边界仍缺失。
  - Why: canonical payload 删除 `record_activation`、`ActivationEvidenceProvider` 与 `RuntimeStore.write_activation`；测试 host seam 移入 tests，安装态 CLI 与库级 v2 claim/recovery 在无 host attestation 时固定返回 `TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE`。56 项 M2、104 项 task-core、53 项 foundation、47 项 watcher core、15 项 live-negative 通过。
  - Impact: 当前唯一允许结论仍为 `blocked`。本机登录态握手只执行一次并在临时 role/Skill 准备阶段以 `HANDSHAKE_SETUP_FAILED` 结束，未建立 custom-role activation 或 child/parent terminal；plan delta 固定为 `candidate-inaccessible-host-attestation-required`。PR #6 保持 Draft，禁止验收、合并、M2-B、automatic route 与生产/AIO 修改。

- [2026-08-19] GKD-M2-A 完成最小安装面整改与本机握手复验。
  - Why: canonical/installable payload 进一步移除 M1 的 `FixtureEvidenceProvider` 与 `make_fixture_evidence`，所有 activation/fixture writer seam 只留在 tests；正常 CLI/library v2 claim/recovery 无 host attestation 时在任何 runtime/tracked 写前返回 `TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE`。唯一 live probe 已从校验过 digest 的项目级 `gkd_executor`/Skills 启动，但宿主只给出失败事件，未证明角色、effective config 或双 terminal。
  - Impact: F-005 最小整改闭环，F-004 分类为 `CUSTOM_ROLE_HANDSHAKE_INCOMPLETE`，总体仍为 `blocked`。不引入 daemon、IPC、签名协议或恶意 subclass 防御；PR #6 保持 Draft，auto route 与 M2-B 继续禁用。

- [2026-08-19] GKD-M2-A 新增授权本机握手在宿主模型准入阶段终止。
  - Why: 授权锚点、分支/远程/PR head、干净 worktree 和静态 parser preflight 均通过；preflight 证明临时项目 trust、`agents.enabled=true`、精确 `gkd_executor` discovery 与 role/config/bundle digest，且此时模型调用/已消耗尝试均为 0。本轮唯一 live 启动后，Codex 在 parent turn 前以 HTTP 400 `invalid_request_error` 明确拒绝 ChatGPT account 使用 `gpt-5.6-sol`。
  - Impact: 失败分类收窄为 `HOST_MODEL_UNSUPPORTED_FOR_CHATGPT_ACCOUNT`；未产生 custom-role activation、effective model/effort/sandbox、host digest binding 或 child/parent terminal，F-004 和总体 outcome 保持 `blocked`。未重试、降级、fallback 或替换角色；PR #6 必须保持 Draft，不得启动 M2-B 或 automatic route。

- [2026-08-19] GKD-M2-A F-004 改为正常生产使用环境握手合同。
  - Why: 隔离模式的 parent `--model gpt-5.6-sol` 与 `--ignore-user-config` 绕过了日常 provider/model routing，其 HTTP 400 不能判定正常环境中 project-scoped child role 的可用性。官方 Codex 合同规定 project role 位于 `.codex/agents`，agent TOML 中的 model/effort 优先；user config 承载 machine-local provider/auth，受信项目才加载 project `.codex` 层。
  - Impact: v3 live parent 使用正常用户 provider/auth/model routing，不传 `--ignore-user-config`、parent `--model` 或 effort override；临时 `gkd_executor.toml` 继续固定 child Sol/xhigh/workspace-write。确定性 preflight 负责 digest/trust/discovery/non-drift，host 只负责 parent turn、按名唯一 activation、无 fallback 和双 terminal。先推送静态 fixed head，再由用户单独授权一次 live。

- [2026-08-19] GKD-M2-A v3 正常环境静态预检因用户配置严格解析失败。
  - Why: `command -v codex` 解析的 `codex-cli 0.147.0` 在 `app-server --strict-config --listen off` 启动时拒绝正常用户 `config.toml` 的未知字段 `disable_response_storage`；失败发生在 project trust/custom-role discovery 之前。冻结 live 参数向量通过 `--help` 解析，临时 repo/digest 正确且生产配置前后一致。
  - Impact: 当前机器分类为 `USER_CONFIG_PARSE_FAILED`，`modelInvocations=0`、`liveAttemptsConsumed=0`；不修改生产配置，不放宽 strict-config，不启动 live。M2 63 项双 evidence 与 219 项保留回归通过，总体保持 `blocked`，PR #6 保持 Draft。

- [2026-08-19] GKD-M2-A F-004 v4 将生成配置严格性与宿主兼容启动分离。
  - Why: `codex-cli 0.147.0 --strict-config` 会因正常用户字段 `disable_response_storage` 在项目发现前失败，不能验证日常生产使用环境；用户明确要求保留正常配置且不修改生产 `~/.codex`。项目生成物仍可由标准库 `tomllib` 和 canonical source 精确比较实现严格校验。
  - Impact: 生成 project config 与 `gkd_executor.toml` 继续 strict/fail-closed；宿主预检改为非 strict `codex app-server --listen off` 加显式 trust/`agents.enabled=true`，只接受 no-transport 边界并拒绝 trust disabled、malformed project/role 或其他 fatal startup。live command 删除 `--strict-config`，继续使用正常 provider/auth/model routing。no-transport 不作为 activation；v3 `USER_CONFIG_PARSE_FAILED` 作为零模型/零尝试历史兼容性事实保留。静态门通过后仍须对新 fixed head 单独授权一次 live probe，F-004 成功前总体保持 `blocked`。

- [2026-08-19] GKD-M2-A F-004 v4 正常环境 live probe 未产生 custom-role activation。
  - Why: 授权 head `26b8e9c185a0bdf365266efdb45f42260c8922b3` 的全部启动门通过后，唯一一次正常登录态 `codex exec` 成功进入并完成 parent turn，exit code 为 0；但结构化 host 事件只包含一个无 receiver thread/agent state 的 collaboration `wait`，没有 spawn、`gkd_executor` activation、child identity 或 child terminal。Agent message 正文不作为证据。
  - Impact: 规范化分类为 `CUSTOM_ROLE_ACTIVATION_MISSING`，`modelInvocations=1`、`liveAttemptsConsumed=1`；不得重试、降级或以 parent terminal 补足 child 事实。原始 JSONL/临时 repo 已删除，生产/AIO 保护面不变。F-004 与 M2-A 继续 `blocked`，PR #6 保持 Draft，M2-B 与 automatic route 不得启动。

- [2026-08-20] GKD-M2-A F-004 通过 session rollout 记录完成 trusted custom-role handshake。
  - Why: 用户在精确 fresh probe Git 根通过正常 Codex trust UI 选择继续后，授权本机 `codex exec --json` 的 parent rollout 记录包含唯一 `agents.spawn_agent`，参数绑定 `gkd_executor`/`gkd_executor_handshake`/`none`；宿主 activity 绑定 child thread，child rollout 与 parent rollout 分别有独立 `task_complete` terminal marker，Codex exit 0。stdout 的 wait-only 压缩不完整，不能覆盖 rollout 记录中的 spawn 事实。
  - Impact: 只保留 path-free hashed thread、event types、exact role、terminal 和 exit facts；session 原文不进入仓库 evidence。F-004/M2-A outcome 为 `role_routing_core_ready`，route 仍 `manual_only`；M2-B、automatic route、生产安装、AIO 和里程碑 3 继续禁止。

- [2026-08-20] GKD-M2-A 采用 trusted-main 工作流 activation 边界并收紧 rollout 归一化。
  - Why: 用户明确将同一 OS 用户的 monkeypatch、私有 API 和直接 runtime 修改排除出威胁模型，并要求 trusted main 从已验证 host facts 生成最小 activation receipt。原 rollout 证据同时需要绑定唯一 exact spawn 参数、对应 activity child identity 与 exact child terminal，不能接受任意 child record 或硬编码 downgrade/fallback。
  - Impact: canonical payload 增加 `TrustedMainActivationAuthority` 和一次性 provider，candidate-facing CLI/default library 无 provider 时仍在写入前返回 `TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE`；不引入签名、daemon、IPC 或密钥。F-004 负向合同覆盖 wrong task/fork、unrelated terminal、multiple spawn、wrong identity 和 fallback。implementation/evidence commit 为 `f86a092a9ba42fd8965209dfe18f3a70debe0ef6` / `0108c1c50dc3c4437cadf0cbea1ebd480768e83c`；bundle/evidence digest 为 `5b115a918d8a5241551b0be8dac657a448e1b912815493e1988007b1f4ed1880` / `2f292830f2e9674a4ea95db1e4026ccf9abd3b6a3ef2241deec799329b590068`。M2-A 为 `role_routing_core_ready` 且 `manual_only`，等待独立验收。

- [2026-08-20] `GKD-M2-A` fixed head 已独立验收、合并并完成清理。
  - Why: main 以 `b579926aaff50d40b462e7f21cf91c9709eeb3a3` 为唯一验收 head，复核实时 PR #6、完整任务文档、M2-A 70 项和全部保留回归；候选树与 squash merge tree 完全一致，未发现阻塞 finding。
  - Impact: PR #6 以 `9351d628d198ec8638311901cf288abadc643a42` 进入 main；本地/远端任务分支和候选 worktree 已删除。M2-A 仍只证明 `role_routing_core_ready`/`manual_only`，下一步是独立人工 M2-B，不得由合并事实推导 automatic route、生产安装或 AIO 授权。

- [2026-08-20] M2-A 长会话复盘收敛子代理实施边界。
  - Why: 原始会话中嵌套 `codex exec` 的隔离参数、strict-config、parent model override 和 wait-only stdout 曾造成编排失败被误读为角色失败；首次 ready 还缺少 activation→claim 可消费正向链。独立验收和完整 rollout 事实随后纠正了这些判断。
  - Impact: 后续里程碑继续使用人工顶层 session 完成规划、实现和材料性判断；`gkd_executor` 只在固定角色/offer-claim/一小时等待门全部通过后用于后续自动路线，且 executor 不验收、不合并、不清理。执行 session 应在授权范围内自主完成静态验证、有限诊断、修复、证据和交付，只有真实平台硬阻塞才返回 main；新 session 以固定 head 和持久记录为准，不复制历史 blocked 叙述。

- [2026-08-20] 用户确认 M2-B 一小时原生等待门可用并免于重新取证。
  - Why: 用户明确说明已经验证 `wait_agent(timeout_ms=3600000)` 与 child early-final 可用，并要求直接按可用事实固化，不再定位 session 记录或重跑 live gate。M2-A 已由 fake-clock 合同覆盖最多12轮静默重等、绝对deadline、一次interrupt和单一timeout。
  - Impact: 用户确认作为本计划的 M2-B 接受依据，绑定 M2-A bundle digest `5b115a918d8a5241551b0be8dac657a448e1b912815493e1988007b1f4ed1880`；不伪装成重新生成的机器 session evidence。里程碑2完成，manual继续默认，M3/M4/M5可按已有hybrid B授权显式启动唯一`gkd_executor` automatic route；门禁漂移仍fail-closed。生产安装与AIO授权不变。

- [2026-08-20] 自动路线启动前补充 `GKD-M2-C` runtime bridge。
  - Why: M2-A 已实现角色生成、路由和 `TrustedMainActivationAuthority` library seam，但 project `.codex` staging 只存在于测试 fixture；仓库根没有可发现的 `gkd_executor`。公开 CLI 又故意禁止 candidate activation/claim，canonical payload 没有把 trusted main 的 exact spawn 返回值转换为 activation 并注入 claim 的可执行入口。当前 session 无法回溯加载后来生成的 custom role，直接启动 M3 会跳过 offer/claim 或退化为 generic worker。
  - Impact: 先由最后一次人工顶层 session 实现窄的 M2-C：确定性 project-role stager、main-only spawn事实→activation→claim bridge、执行 bundle digest与候选输出 bundle digest分离、对应L1/L2合同及README纠偏。不安装生产 `~/.codex`，不实现M3产品功能，不读取session/auth。M2-C通过后从staged project启动fresh main，后续M3/M4/M5才真正使用automatic route。

- [2026-08-20] 里程碑3拆分为三个依赖有序任务。
  - Why: fixed-head monitor/policy、资源与防泄漏基础、用户工作流Skills虽同属M3，但接口和验收风险不同；合并为单一PR会扩大审查面并让资源/审查语义阻塞CI最小核心。
  - Impact: `GKD-M3-A`只实现通用`.gkd` policy与GitHub fixed-head monitor；`GKD-M3-B`实现产物分类、资源预设、GitHub facts/推荐和固定scanner wrapper；`GKD-M3-C`实现共享review core、`gkd-optimize-ci`、`gkd-review-remediation`及七Skill收口。三者依次依赖并在M2-C后自动执行。

- [2026-08-20] `GKD-M2-C` 使用一次性 bootstrap execution exception。
  - Why: 已生成的 manual offer 无法被公开 `gkd-task claim` 消费：CLI 固定使用 unavailable evidence provider，而 schema-v1/manual claim 仍无条件读取 runtime evidence，形成“先使用待实现桥，再实现桥”的自举死锁。执行 Session 正确返回 `RUNTIME_EVIDENCE_UNAVAILABLE` 且未修改文件或状态。
  - Impact: main 撤销旧 offer/envelope；M2-C 由固定requirements/plan/implementation/execution、独立worktree/branch/PR、人工顶层Session与fixed-head独立验收授权，不调用或伪造claim、receipt、activation、task delivery。执行者仍不得验收/合并/清理。该例外在M2-C合并后终止，M3及以后必须使用正式automatic bridge。

- [2026-08-20] `GKD-M2-C` 候选达到 `automatic_runtime_bridge_ready`。
  - Why: canonical payload 现已提供确定性非生产 project staging、六门 automatic decision 的 offer/envelope 绑定、唯一 direct `gkd_executor` spawn 校验、trusted-main activation/exact claim 与中断恢复；claim 中的 execution bundle 和 delivery 中的 candidate output bundle 分离并有状态不变量。17 项 M2-C 合同在两个独立临时根逐字节生成相同 evidence，全部保留回归通过。
  - Impact: implementation/evidence commit 为 `958a313f48ea7fd5d190dfa5b200230d81d29fd4`；candidate output bundle/evidence digest 为 `2d8117b5ac8ecf9d30fa578424d208ff7795192a3396eb653ee641376955116a` / `5ffe2feef2646b39f5bf293e2365fcbf509fd5518d9a5885250716d1b9814e0e`。M2-C task state 按 bootstrap exception 保持 planning/revision 5/epoch 1 且无 claim/receipt；旧 offer 保持 revoked。PR #7 必须在新 fixed head 独立验收，验收前不视为 accepted runtime upgrade，不启动 fresh main、M3、生产安装或 AIO 修改。

- [2026-08-20] `GKD-M2-C` 首轮独立验收四项阻塞已修复并重新取证。
  - Why: fixed head `b512a2aa644992c88ae2a2012d1322573a9ead0b` 仍信任旧 bundle lock、接受 project/bundle 祖先 symlink、在 task lock/CAS 前写 activation 并向公开 `gkd-role automatic-claim` 暴露伪造 spawn 入口；原 17 项合同未覆盖这些反例。
  - Impact: implementation/evidence commit `e72803783b2abbf453a90ee1ebc89c911cd12c57` 在任何项目写入前重验 bundle 实体与 manifest/lock，逐组件 lstat 两类根路径，把 automatic activation postimage 纳入 claim transaction，并将公开 automatic CLI 固定为 `TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE`。24 项 M2-C 合同含真实并发、pre/post-commit 恢复和 5 项 mutation，两次 evidence 逐字节一致；candidate bundle/evidence digest 为 `c385b10ca631b94c8e26c4f1accfdd8a3c9208b0cacfc1e320b52bbe631c9650` / `5b8f824d7fb98b82c7db805e7cebea848c4185f8a4c078e969998a48f7d5ef13`。PR #7 仍须对新 fixed head 独立验收，本 session 不验收、不合并、不启动 fresh main/M3，也不修改生产或 AIO。

- [2026-08-20] `GKD-M2-C` 第二轮验收缺口已按最小自动工作流范围修复。
  - Why: fixed head `b97dce72a21a719b616f418b7e23638bce507f0c` 的 acceptance 只处理 schema v2，导致 v3 缺 receipt、receipt/claim 不匹配和 routeDecisionDigest 漂移仍可通过；普通 Python 又会在 source payload 生成未声明 `.pyc`，使官方 staging 自我拒绝，且 `source.toml` symlink 会被跟随读取。
  - Impact: implementation/evidence commits 为 `d3d8ea7a6d594caac843be91f7f2e651906bfacd` / `bb1992998af62119fde4eef1b0e9972fe757b3d7`。v3 acceptance 现完整绑定 activation、双 receipt、claim receipt、active/consumed offer、envelope ID、role/config/bundle、route decision 和窗口；官方 Python 启动边界禁止 payload bytecode，manifest 仍严格声明 52 文件；`source.toml` 使用 lstat。`project-remove` 仅增加已缺失受管文件的幂等重试，不新增事务。30 项 M2-C 合同默认环境双次一致，git archive 副本 30/30，全部保留回归通过；bundle/evidence digest 为 `3a95bab5083bd2ff37e29ef4f367860bb3f80a63265ec8163334da310e3c556f` / `5e3a9b2efbafb75986c24f5f15f93c99f734bde1b716f23a58ca7c72ed11db13`。PR #7 仍须新 fixed-head 独立验收，本 session 不验收、不合并、不启动 M3 或修改生产/AIO。

- [2026-08-20] `GKD-M2-C` AC7 in-flight execution bundle 复验缺口已修复。
  - Why: fixed head `d0d24fcea80d926fb4b9d29cfb93a3e58e1eb516` 的 bridge 只在构造时生成并缓存 role catalog；prepare 后删除或替换执行 bundle，claim/recover 仍可沿用旧 catalog，违反执行 bundle 不可静默替换合同。
  - Impact: implementation/evidence commits 为 `c5bf34c4f8623c1720cd4ddd990811cc29840295` / `0c2578ab4a6d98634dbc2ba13cf89ef1e6719bc3`。bridge 每次构造、prepare、claim、recover 都从当前 bundle 完整复验并重建 catalog；删除 bundle 的 claim 与 committed 中断后替换 bundle 的 recover 均在写前稳定拒绝，恢复原 bundle 后可确定性补齐 receipts。32 项 M2-C 双 evidence 与 archive 副本、全部保留回归通过；bundle/evidence digest 为 `05288d5b09bdd8b4703a45d8a300d9466ad59f6b414d8eb5684c4a214ecfaaad` / `ab6efbc3cded637edc1fd0acd155958a3949566d48282fa1c4bfa81b266bbb82`。Python 3.11+ 前提已写入 README；本轮使用 3.14.6。PR #7 必须在新 fixed head 独立验收，bootstrap 与停止边界不变。

- [2026-08-20] `GKD-M2-C` fixed head 已独立验收并合并，一次性 bootstrap exception 终止。
  - Why: main 对 `b25637d8f0989427f9bfe0cc46e603ffd3c79550` 复核三轮整改和完整 AC；M2-C 在两个隔离根及 fixed-head archive 各通过 32 项，104/70/53/47/15 项保留回归通过，候选与 squash merge tree 完全一致。无 configured checks 被记录为 bootstrap 事实，不伪装为 CI 成功。
  - Impact: PR #7 以 `b16349af24ae76055f86f3b02437168404b97ff8` 进入 main，bundle `05288d5b09bdd8b4703a45d8a300d9466ad59f6b414d8eb5684c4a214ecfaaad` 成为 accepted execution-bundle upgrade。M2-C 的 planning/epoch 1/revision 5 与无 claim/delivery/activation/receipt 保留为一次性历史，禁止补造；M3/M4/M5 必须使用正式 automatic bridge。当前 Session 未从 staged project 发现 exact `gkd_executor`，所以不启动 M3，后续 fresh main 的任一 gate 不匹配继续 fail-closed。

- [2026-08-20] `GKD-M2-C` 收尾清理完成。
  - Why: 终态验收记录已进入 main；候选 worktree 删除前保持干净，head 为验收 fixed head，candidate tree 与 squash merge tree 一致。
  - Impact: `/Users/knaifen/Documents/Codex/gkd-worktrees/m2-automatic-runtime-bridge`、本地 `task/m2-automatic-runtime-bridge` 与远端同名分支均已删除。任务资料原位保留；当前 Session 继续因未发现 exact `gkd_executor` 而不启动 M3。

- [2026-08-20] accepted M2-C bundle 的项目级自动运行环境已暂存并独立复核。
  - Why: M3 自动路线必须从已验收 bundle 生成 project role/config/Skills，不能把 canonical source、生产安装或当前会话启动后的动态文件当作已加载运行时。暂存前后的生产 `~/.codex` 与 AIO 快照必须逐字节一致，Git 跟踪面必须保持干净。
  - Impact: accepted execution bundle `05288d5b09bdd8b4703a45d8a300d9466ad59f6b414d8eb5684c4a214ecfaaad` 已安装到隔离的非生产临时根；本仓库机器本地 staging 固定 `gkd_executor` 为 `gpt-5.6-sol` / `xhigh` / `workspace-write`，role/config/project-config/inventory digest 分别为 `08bfcea59c7be5ea03cd7958ac2195e6a0a5703823a739fd819aabd6c48427dd`、`10c0675808974609242280367f2e7aea07e61dd839a1ec2e244d53a9b6c74e3e`、`9a9bc7db827ea68cf4ba6761902e91ce4982fbaec25b8d68b70c4c790cef35d0`、`7566f1ed3fbc10b12585a2ecb3639772f7cbbc31c5485a24ba318bf34ea6544a`。这些项目表面由 `.git/info/exclude` 机器本地排除，不提交、不构成生产安装。当前 Session 不启动 M3；fresh main 必须先重验全部绑定并实际发现 exact `gkd_executor`，否则继续 fail-closed。

- [2026-08-20] `GKD-M3-A` 候选建立版本化仓库 CI policy 与 GitHub fixed-head terminal monitor。
  - Why: trusted acceptance 需要把仓库特有 required checks 留在 `.gkd/policy.json`，并由通用只读机制对显式 PR/full head 拥有 bounded polling 与单一终态，避免 Agent 手工轮询或把任意出现的 checks 当成 policy。
  - Impact: candidate output bundle `92e218e9809e6147f3b04ec7f8fed79231c6e8b3a94480729b52b6fcdbafafe8` 新增严格 policy/origin parser、read-only GitHub adapter、deadline-bound monitor 和 terminal schema；本仓库标准 check 为 `GKD Verify`，本地与 Actions 共用版本化 verifier。候选经 333 项本地合同与 27 项双 evidence 证明，仍须 PR #8 最终 fixed-head CI 与 trusted-main 独立验收；不授权 M3-B/M3-C、生产/AIO 或 GitHub 设置变化。

- [2026-08-21] `GKD-M3-A` 修复 PR #8 暴露的 shallow checkout 与 schema/parser 契约缺口。
  - Why: Actions 默认 `fetch-depth: 1` 无法证明显式 base SHA ancestry；标准 checkout 也不保证创建 `refs/remotes/origin/HEAD`；旧 schema 与 terminal parser 对 branch/check 约束及早期错误结果的可空身份形状不一致。
  - Impact: workflow 使用完整历史，policy 只校验 `origin/<baseBranch>`，schema/parser 共享严格约束并覆盖早期 error terminal；候选 bundle digest 更新为 `0484095704599750df655bc6c92cf0b5829bc2c1ebb877aa3f3cd132cc29998f`，335 项版本化本地验证与 29 项双 evidence 通过。仍只实现 M3-A，不授权 M3-B/M3-C、生产/AIO 或 GitHub 设置变化。

- [2026-08-20] `GKD-M2-D` delivered rejection/rework core 达到候选交付门。
  - Why: M3-A 暴露了 delivery 后 executor 已停止、但 CI/独立审查只能在 delivered PR head 上得出最终拒绝结论的生命周期缺口。task state v2 现由 trusted main/acceptor 在固定 candidate/PR/review/receipt/authorization 全部匹配时原子保存旧 attempt、撤销 offer、递增 epoch 并返回 planning；executor 与旧 capability/envelope/claim 均不可自行恢复执行。
  - Impact: implementation/evidence commits 为 `c0ee720cce21500faf5ef396c5e5a985498caeff` / `c41e35e420e3bc05b7fd23149a956403a0a5732c`，candidate output bundle/evidence digest 为 `71c4b2d3562c2e5a6a784bf3436a7d5920cd00b3ad387f320a2563d4b5b88766` / `da884bc1efe152ed983deda4c04d02bf95eafad17b2f61bd2f2067b729a2324d`。118 项 task-core 在两个独立临时根逐字节生成相同 evidence，完整 versioned verifier 的 118/32/70/53/47/15 项通过；生产/AIO 摘要不变，唯一任务 PR #9 已 Ready，PR #8/M3-A 未修改。候选仍须 fixed-head 独立验收，本 session 不验收、不合并、不清理或启动 M3-A 返工。

- [2026-08-20] `GKD-M2-D` fixed head 已独立验收、合并、安装并完成清理。
  - Why: main 对 `e8729934f567d74ee19e7583b8f8433dacb9ac60` 的完整 diff、requirements、rework 状态/事务/GitHub 合同和 fixed-head archive 独立复验均无阻塞 finding；candidate 与 squash merge tree 完全一致。无 configured checks 只记录为 bootstrap 事实，不伪装为 CI 成功。
  - Impact: PR #9 以 `0976b4900346e972bd8e03f6e8fa4ab761fe8952` 进入 main；bundle `71c4b2d3562c2e5a6a784bf3436a7d5920cd00b3ad387f320a2563d4b5b88766` 成为 accepted execution-bundle upgrade。隔离安装和 project staging 已验证，role digest 更新为 `880e1855cfdeb50ba890a3023c818cde377b9c6a71c230360154b79ecc16d680`；候选 worktree 与本地/远端分支已清理。M3-A 只能通过此 accepted transition 保存旧 delivered attempt 后重新 automatic offer/claim，禁止手改状态或复用旧 claim。

- [2026-08-20] M2-J delivery-document contract 已独立验收、合并并成为新的 accepted bundle。
  - Why: M2-I 首个候选在功能验证通过后暴露了 delivery document 在 final task state 之后提交的固定 head 缺口；M2-J 以通用、仓库中立的 sequencing/binding contract 修复该问题，并明确 legacy delivered state 必须显式迁移，不能静默接受。
  - Impact: PR #15 fixed head `10427606bd71985f5115b0d4ef3d9c5d8609f0a2` 以 squash merge `c2ae190f96ca321b1b5fe83035f8c67b4c20a42c` 进入 main；candidate bundle/evidence digest 为 `d17c5f5259591ab1dbd0b1148786fc5126dc858bdf577172c0df7c2a29f1c95b` / `c540592337c305f3b0fb738f45752528e55608581ddc4987d795824ff237f774`。旧 M2-I 候选不绕过该合同。

- [2026-08-20] M2-I trusted-host bridge 已按 M2-J 合同 redelivery、独立验收并合并。
  - Why: 为保留已验证的 M2-I bridge 功能，同时满足新的 implementation -> delivery-document -> final-state fixed sequence，注册窄范围 `GKD-M2-I-R`，仅移植原 implementation commit，不重用旧 task state/claim/delivery commits。
  - Impact: PR #16 fixed head `57c259ebfa39e0cf1da8197a28e9827df1328c15` 以 squash merge `faa49861e60ffd5b6b29732e4f769e7444b2dbf6` 进入 main；candidate bundle/evidence digest 为 `1983f05b64860510bfb1af661e5458a6c7b660632479a33af46c27d35ff188d4` / `be0a8b80229d832bf21d1d27e243a57a9832170940fbf28dfcb959b1816c29ea`，两次 focused evidence 逐字节一致，local verifier 全部通过。accepted bundle 已隔离安装并刷新 project staging；M3-A 现在只能从该 exact fresh main/role/bundle 开始。

- [2026-08-21] `GKD-M3-A` 候选已同步 accepted M2-D/M2-J/M2-I-R main 基线并重新取证。
  - Why: PR #8 与 trusted main `d669c11735f1468127ce4b7b4699a19ef0984753` 的冲突必须由当前 exact executor 解决；main 新增的 delivery/rework/runtime payload 会改变 candidate bundle，旧 manifest lock 与旧 evidence 不再是当前候选事实。
  - Impact: 合并保留 M2 delivered rework、delivery document sequencing 和 trusted-host bridge 合同，同时保留 M3-A policy-backed monitor；canonical generator 将 60 文件 candidate bundle digest 更新为 `22b935b0ec7ad1fb1da9222c5b30c4586fa1c55a68ec23f782928a5635e01120`。362 项 versioned verifier 通过，29 项 M3-A 双 evidence 逐字节一致，evidence digest/file SHA-256 为 `2bee04f714db90808587986b13be38df42d041aa36efc3e3889c53c73fea5b58` / `9e548f09fa0ed6a294dc283c9bf392932f094af6b8e6b90f4fc8afe8a063caa8`；生产与 AIO 摘要均保持不变。accepted execution bundle 不变，仍须按 M2-J 单独提交 delivery 文档并执行 final task transition。

- [2026-08-21] `GKD-M3-A` 修复标准 GitHub-hosted Linux runner 的 fixed-head CI 失败。
  - Why: macOS 本地的 `/tmp -> /private/tmp` 与 `/Users` 事实掩盖了两个 portable contract 缺口；Linux runner 在 payload bundle scanner 中看到了硬编码 `/tmp`，并把测试中的不存在 `/Users` 误报为 invalid migration home。
  - Impact: `gkd_role.project` 使用构造式系统路径别名，retained migration test 使用当前平台存在的 `Path.home()`；M3-A evidence 重新绑定 candidate bundle `e49f6bf994a3dea405248535ffdd70473feacd13c27ae39a6ecfc1fabd9a7efd`，29 项双 evidence digest/file SHA-256 为 `a2ffc693a75780aa893538462bf6a1a2428f2d55d0c68d138b33f4a288cd1c5b` / `93b9e6b365f6fa832485183e0dcf83ab293e27804d5d087f1c438720474ba181`；本地 verifier 仍须绑定 repair head，GitHub monitor 的失败终态保留为历史证据，不重跑旧 head。

- [2026-08-21] `GKD-M3-A` fixed-head acceptance 合同补齐合法 required-check name。
  - Why: policy/workflow 正确声明 `GKD Verify`，但 task acceptance 的通用 identifier regex 拒绝空格，导致 live snapshot 在验收前失败；该缺口由 M3-A 范围内共享 check-name validator、回归和 mutation 测试修复。
  - Impact: PR #8 fixed head `b7804f7caacafbf2d08e1539cac21d571078ef3b` 通过 `GKD Verify`、364 项 verifier、29 项双 evidence 和独立 review，squash merge 为 `d7348ab286d7dc0a56fc0b8b85247c8521901828`。accepted bundle 更新为 `4d12c9973ea9302162493a5a71e25a4948b1f23991d30873c4a11ad691647aed`；M3-B 现在可从该 fresh main 自动启动。

- [2026-08-22] `GKD-M3-B` candidate resource/scanner layer follows fail-closed and source-boundary rules。
  - Why: resource-constrained must remain the conservative default; unknown build bounds and peak-disk violations cannot be repaired by later cleanup, and billing recommendations must not claim unverified runtime prices.
  - Impact: candidate payload adds deterministic artifact classes/presets, visibility/runner/policy/billing recommendations, and diff/PR/artifact scanner surfaces with redacted terminal findings. M3-A policy/monitor and M3-C review/Skills remain untouched; delivery and acceptance are still pending.
