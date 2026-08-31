# P2 激活交接外观交付

## 固定输入

- 任务：`GKD-P2-ACTIVATION-HANDOFF-FACADE-R2-BOOTSTRAP`
- 固定基线：`2f02f199aafe0540349f518779124aa1debbbb2c`
- 规划头：`f10c23492143fd0bc3746ddfa4df02a957e65327`
- 实现提交：`b5838e575bf10fa63e36a27b428e81c4e2598d99`
- bundle digest：`f387dff79dd58acca465c1715e6676e38f618c71a47ae4fa07de56123efc686a`

## 实现边界

新增 trusted-main-only `prepare_handoff` 与 `TrustedMainHandoff.acknowledge`。prepare 阶段封存 execution context、spawn request、offer/envelope/route/bundle/role/config 绑定和 claim CAS；一次 direct `gkd_executor` acknowledgement 会完成绑定 claim，成功或拒绝后均不可重放。旧 `prepare`、`claim`、`execution_context` 和公开、candidate fail-closed 面保持兼容。

本手工 bootstrap 只停在 planning/no-claim 状态；没有创建 offer、claim、activation、delivery 或 receipt，也没有修改 production、AIO、settings、Secrets、runner、tag 或 Release。

## 验证证据

- `scripts/gkd-verify --base-sha 2f02f199aafe0540349f518779124aa1debbbb2c`
- Python 3.9.6：425 项通过；runtime-bridge focused 51 项通过。
- Python 3.14.6：425 项通过；runtime-bridge focused 51 项通过。
- handoff focused contracts：sealed context、single consume、exact direct spawn、policy/CAS drift、bundle drift 均通过。
- 证据文件：`tasks/gkd-p2-activation-handoff-facade-r2-bootstrap/evidence.json`
- 证据摘要 digest：`6083b154340f73b298e9914e23ca0c10512d769f1fd62e5a186b24140c449092`

## 交接终点

该分支在本 delivery 文档提交后固定；后续由独立验收流程绑定完整分支头与 fixed-head CI。执行会话不执行 acceptance、merge、archive 或 cleanup。
