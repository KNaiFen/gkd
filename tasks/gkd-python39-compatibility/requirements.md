# GKD Python 3.9 Compatibility Requirements

## Goal

使 canonical GKD 在实际 executor 默认解释器 Python 3.9 下完整运行；移除 Python 3.10/3.11 API 依赖，而不把本机解释器路径、外部 pip 依赖或缩减验证范围固化为工作流条件。

## User Decisions

- 用户已选择完整 Python 3.9 兼容移植；这替代 R5 后“最低解释器或完整移植”的待决项。
- 本任务从 trusted main `f4ec2461f3314a9246b3d0f5ba25eb67b693e862` 建立。GKD-GATE-REPAIR attempt 0 至 R5 与 O4 是只读历史，禁止复用其 offer、claim、activation、delivery 或 PR。
- 一个精确 `gkd_executor` 交付、一个独立 `gkd_acceptor` 验收、trusted main 合并和收尾；不使用 nested agent、解释器路径 fallback 或外部依赖。
- 只修改 GKD canonical、合同测试、任务记录和相关文档。生产、AIO、GitHub settings/Secrets、付费 runner、tag/Release、已发布资产保持不变。

## Scope

- 系统审计并移除 canonical payload、默认/历史 verifier、watcher/probe 和测试运行器中实际可达的 Python 3.10/3.11-only API 依赖。已知入口包括 `zip(..., strict=True)`、`@dataclass(..., slots=True)` 与 `tomllib`；不能只修复首次报错位置。
- 以 Python 3.9 可执行且保留原有长度/顺序 fail-closed 语义的实现替代所有必要 strict zip 调用；不能静默截断不等长输入。
- 以 Python 3.9 可执行的 dataclass 声明替代所有 runtime/historical lane 的 `slots=True` 用法，保留现有不可变或其他既有语义。
- 引入 payload 内部 TOML compatibility facade：Python 3.11+ 优先使用标准 `tomllib`；Python 3.9 使用随 payload 分发、可解析完整 TOML 语义的兼容实现。兼容实现必须保持 `load`、`loads`、`TOMLDecodeError` 所需接口，携带上游许可和归属，不得手写仅覆盖当前 fixture 的 TOML 子集，也不得新增 pip/install-time dependency。
- 更新所有受影响的 payload、probe、测试和文档 import；文档声明的最低支持解释器改为 Python 3.9，不得硬编码任何本机绝对解释器路径。
- 收紧 CLI/服务边界的错误分类：内部 `TypeError`、`ValueError` 等程序错误不得再被输出为 `FILESYSTEM_ERROR`；保留既有领域错误和真实文件系统错误的稳定语义。
- 同步 source manifest、lock、package inventory、合同测试与文档，使 bundle 自验证覆盖新增兼容文件和许可材料。

## Non-Goals

- 不实施逻辑时钟、planning-refresh、delivery sidecar、state schema、O4-O8、route、CI policy、release 或生产迁移的行为改变。
- 不支持 Python 3.8 或更低版本，不降低现有 Python 3.11+ 行为，也不把 Python 3.9 测试缩成 import-only smoke。
- 不引入第三方安装依赖、运行时下载、解释器选择脚本、生产/AIO 写入或任何 GitHub settings/Secrets/runner 副作用。

## Acceptance Criteria

1. `/usr/bin/python3` 的 Python 3.9 环境可执行完整 current `scripts/gkd-verify`、bundle generate/verify、`gkd-task status`/`doctor`、`gkd-role project-verify` 和已适用的 historical watcher/probe lane；不出现版本 API 引发的 traceback 或误报 `FILESYSTEM_ERROR`。
2. 自动化扫描和正反合同覆盖所有 shipped/reachable Python 3.10/3.11-only API 使用；不等长 strict pairing、TOML 有效/无效输入、watcher/probe import 与 CLI 异常分类均保留或新增明确失败证据。
3. Python 3.11+ 的相同 verifier、bundle 和核心 CLI 合同仍通过；Python 3.9 与常用开发解释器对同一 source 生成一致的 canonical bundle/manifest 结果。
4. TOML fallback 不接受截断语义：包含嵌套、数组、日期时间、转义字符串和 malformed input 的合同与标准 `tomllib` 行为一致；新增兼容代码的来源许可在 payload 内可审计。
5. README、canonical README 和 task-facing运行时文档一致声明 Python 3.9 最低版本，且不包含机器专用解释器路径。
6. candidate 的 task state 保持旧 validator 可读，交付只包含本任务源码、测试、许可、manifest/lock、文档和证据；独立 acceptor 在相对 policy 的 fixed-head CI success 后完成 canonical acceptance。
7. 不引入绝对路径、凭据、新依赖或生产/AIO/GitHub settings/Secrets/runner/tag/Release 副作用。
