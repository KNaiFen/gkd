# 验收与收尾：GKD-M2-B 一小时原生等待门

## 最终结果

- 结果：完成
- Outcome：`one_hour_wait_gate_ready`
- 证据等级：用户明确确认的运行时事实
- 绑定 bundle digest：`5b115a918d8a5241551b0be8dac657a448e1b912815493e1988007b1f4ed1880`
- 日期：2026-08-20

## 接受事实

- 目标运行时实际支持 `wait_agent(timeout_ms=3600000)`。
- child final 可以在一小时到期前提前唤醒 parent。
- M2-A 已有 fake-clock 合同继续负责最多 12 个一小时间隔、健康静默重等、绝对 deadline、一次 bound interrupt 和单一 timeout。
- 不使用更短 wait 拼接、外部 watcher、generic worker、角色替换或 fallback。

## 用户决定

用户明确表示已经验证 M2-B 可用，并要求直接按可用事实固化，不再定位 session
记录或重跑 live gate。因此本记录不声称重新生成了 session/rollout 机器证据，用户
确认本身是本次计划门禁的接受依据；该决定取代此前“必须另建 M2-B worktree
重新验证”的待办。

## 路由影响

- manual 继续作为默认路线。
- 里程碑 3、4、5 的 wait gate 现在允许显式请求 automatic route，并且只能选择
  `gkd_executor`；实际启动仍须由后续 M2-C 提供 project role staging 与
  trusted-main activation/claim bridge。
- automatic route 仍必须绑定 exact bundle、role/config、offer/claim、activation
  和本记录对应的 wait gate；任一事实缺失或漂移时 fail-closed 回到 manual-only。
- 本决定不授权生产 `~/.codex` 安装、AIO 接入、付费 runner、Secrets 或计划外
  GitHub 设置。

## 清理

本次只做 records-only 固化，没有建立 M2-B worktree、任务分支或 PR，因此没有
相关清理对象。
