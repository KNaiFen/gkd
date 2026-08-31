# P2 激活交接外观交付

## 固定输入

- 任务：`GKD-P2-ACTIVATION-HANDOFF-FACADE-R2-BOOTSTRAP`
- 固定基线：`2f02f199aafe0540349f518779124aa1debbbb2c`
- 规划头：`f10c23492143fd0bc3746ddfa4df02a957e65327`
- 实现固定头：`acb4fbe955a2a04b4ab2500e86cfc02bfe6cc8e5`
- bundle digest：`b7e7d9b34977774e16c690d0ebc85d8e450fc836a5aa6303d13e7294f0abda1f`

## 实现边界

新增 trusted-main-only `prepare_handoff` 与 `TrustedMainHandoff.acknowledge`。prepare 阶段封存 execution context、spawn request、offer/envelope/route/bundle/role/config 绑定和 claim CAS；一次 direct `gkd_executor` acknowledgement 会完成绑定 claim，成功或拒绝后均不可重放。旧 `prepare`、`claim`、`execution_context` 和公开、candidate fail-closed 面保持兼容。

本手工 bootstrap 只停在 planning/no-claim 状态；没有创建 offer、claim、activation、delivery 或 receipt，也没有修改 production、AIO、settings、Secrets、runner、tag 或 Release。

## 验证证据

- `scripts/gkd-verify --base-sha 2f02f199aafe0540349f518779124aa1debbbb2c`
- Python 3.9.6：424 项通过；runtime-bridge focused 50 项通过。
- Python 3.14.6：424 项通过；runtime-bridge focused 50 项通过。
- handoff focused contracts：sealed context、single consume、exact direct spawn、policy/CAS drift、bundle drift 均通过。
- 证据文件：`tasks/gkd-p2-activation-handoff-facade-r2-bootstrap/evidence.json`
- 证据摘要 digest：`91f8b7dee9fe1857087a3f9160c5e29f673ca26718c278891d7ccf2c7bb79db6`

## 交接终点

该分支在本 delivery 文档提交后固定；后续由独立验收流程绑定完整分支头与 fixed-head CI。执行会话不执行 acceptance、merge、archive 或 cleanup。
