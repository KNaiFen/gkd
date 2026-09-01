# Review

## 结论

通过第一阶段 `legacy-compat-baseline`。

## 审查依据

- `70c383a` 将 runtime baseline 改为显式版本 registry，保留 `0.147.0` 历史别名并登记 `0.152.0` 当前 capture。
- 未知 CLI、已登记版本的 schema 漂移、请求 digest 与实际 baseline 不匹配分别返回窄错误；app-server transport 在校验失败时不会启动。
- 当前 capture 只进入兼容性记录；历史 watcher 仍要求旧 baseline，automatic watcher 没有重新启用。
- 变更没有处理子代理事件、MCP、CLI 文本 parser、initialize 能力或 `turn/steer`。

## 验证

- watchdog discover：53 项通过。
- runtime/app-server/native probe 专项：25 项通过。
- historical watchdog contract：47 项通过，输出 `compatibility_baseline_recorded`。
- `git diff --check`：通过。

## 下一步

进入第二阶段前，保留该 worktree 的 plan/progress/review 作为交接材料。第二阶段只处理子代理事件归一化，不得提前修改 `turn/steer`。
