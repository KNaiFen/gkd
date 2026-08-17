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
