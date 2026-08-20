# GKD-M2-C Acceptance Findings

## Round 1 - `d0d24fcea80d926fb4b9d29cfb93a3e58e1eb516`

### F-001 - execution bundle 在 prepare 后可消失或被替换（阻塞）

- 严重度：阻塞
- 对应要求：`requirements.md` AC7；`plan.md` Behavior And Defaults、Acceptance Criteria 与 Compatibility。
- 证据：`TrustedMainRuntimeBridge.__init__` 仅构造一次 `role_catalog` 并缓存；`claim` 与 `recover` 不再验证 `bundle_root` 的实体、manifest/lock、content digest 或 role/config digest。现有 `test_replay_stale_cas_and_execution_bundle_replacement_fail_closed` 只覆盖 stale CAS 和重复 claim，没有替换 bundle。
- 独立复现：在临时根复制 canonical bundle，构造 bridge 并成功 `prepare`；随后删除整个复制 bundle，再使用原 direct-spawn facts 调用 `claim`。固定 head 仍返回 `claimStatus=implementing`，此时 `bundleExistsAtClaim=false`。
- 影响：已持久化的 offer/envelope 与 host facts 可以在执行 bundle 消失或被替换后继续生成 trusted activation 与 claim；系统没有证明 activation/claim 使用的仍是已固定并验收的执行 bundle。
- 必须达到的结果：每个会继续消费 in-flight execution bundle 的 trusted-main bridge 入口，在任何 activation、claim、receipt 或 recovery 写入前重新验证实际 bundle；实体、manifest/lock、content digest、role/config/Skill digest 或预期 execution bundle identity 任一漂移均 fail-closed 且 tracked/runtime 字节不变。`recover` 必须在已有事务恢复语义允许的精确阶段验证，不能破坏已提交事务的确定性补全。
- 修改边界：只修改 M2-C bridge/bundle 校验所需的最小 canonical code、专项测试、生成清单与交付证据；不得扩展到签名、daemon、IPC、M3、生产安装或 AIO。
- 复验：新增至少两项旧实现失败的负向合同：`prepare` 后删除/替换 bundle 再 `claim`；中断后替换 bundle 再 `recover`。断言稳定错误码、无 activation/claim/receipt/journal orphan、task/runtime preimage 不变或按既有 committed recovery 合同完成。重跑 M2-C 双 evidence、默认 Python git-archive 合同和全部保留回归。

### F-002 - Python 最低版本未显式记录（非阻塞建议）

- 严重度：非阻塞
- 对应要求：`requirements.md` AC9 文档义务。
- 证据：canonical payload 使用标准库 `tomllib`；当前机器默认 `/opt/homebrew/bin/python3` 3.14 可运行，但 macOS `/usr/bin/python3` 3.9 会在官方入口导入时失败。README 与 canonical README 未声明 Python 3.11+ 前提。
- 影响：读者可能把“默认 Python”误解为任意系统自带 `python3`，降低 fresh-main 启动说明的可复核性。
- 建议结果：在最小用户文档中声明 Python 3.11+，并在交付记录中说明本轮 default-Python 合同使用的解释器版本；不要求增加兼容层或第三方依赖。

## Acceptance Decision

- Outcome: `changes_requested`
- Fixed head `d0d24fcea80d926fb4b9d29cfb93a3e58e1eb516` 不得合并。
- 返工责任：原独立人工顶层 execution Session。
- M2-C bootstrap exception、`planning / epoch 1 / revision 5`、无 claim/delivery/activation/receipt 的边界继续保持；不得启动 M3。

## Execution Remediation

- F-001：已由原 execution Session 修复，等待新 fixed head 独立复验。
- Implementation commit：`c5bf34c4f8623c1720cd4ddd990811cc29840295`。
- Evidence commit：`0c2578ab4a6d98634dbc2ba13cf89ef1e6719bc3`。
- `TrustedMainRuntimeBridge` 不再缓存 bundle catalog；构造、`prepare`、`claim` 与
  `recover` 均从当前 bundle 实体完成 manifest/lock/content 与 role/config/Skill
  复验，再建立当次 catalog。删除或替换 bundle 时稳定返回
  `BUNDLE_CONTENT_MISMATCH`，且 claim/recovery 写入前 task/runtime 字节不变。
- 新合同真实删除 prepare 后的 bundle 再 claim；另在 committed interruption 后替换
  Skill、保留旧 lock 再 recover。后者先零写入拒绝，恢复原 bundle 后同一事务成功
  补齐 claim/activation receipts，未破坏既有确定性恢复语义。
- F-002：已采纳非阻塞建议。根 README 与 canonical README 现在明确要求 Python
  3.11+；本轮 default-Python 合同使用 `/opt/homebrew/bin/python3` 3.14.6，未设置
  `PYTHONDONTWRITEBYTECODE`。
