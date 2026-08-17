# Native multiagentv2 D2 capability matrix

- Probe: `GKD-M-1A`
- Codex version: `codex-cli 0.147.0`
- Result: `native_insufficient`
- Scope: native multiagentv2 only; no external watcher was implemented or tested
- Evidence policy: configuration declarations, protocol surfaces, and observed
  behavior are kept distinct. Protocol declarations alone never produce a
  runtime `pass`.

| Contract | Status | Evidence kind | Reproduction | Evidence | Explanation |
| --- | --- | --- | --- | --- | --- |
| `single_long_wait` | `fail` | observed config-parser behavior | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 probes/multiagentv2/native_probe.py --output evidence/m-1-native-d2/capability-probe.json` | `evidence/m-1-native-d2/capability-probe.json` | With multiagentv2 enabled, 3,600,000ms loads and 43,200,000ms is rejected as above the 3,600,000ms maximum. No over-limit wait was called. |
| `normal_final_wakeup` | `pass` | observed one-shot behavior | `agents.spawn_agent(model="gpt-5.6-sol", reasoning_effort="xhigh", fork_turns="none")`; use one `agents.wait_agent(timeout_ms=180000)` only if final-status is not already delivered | `probes/multiagentv2/fixtures/normal-final.json`, `evidence/m-1-native-d2/normal-final.json` | The child returned the fixed final marker and the parent received the native mailbox/final-status event without external steer or polling. |
| `hourly_internal_watchdog` | `fail` | observed limit plus protocol surface | Run the capability capture command above. | `evidence/m-1-native-d2/capability-probe.json` | The native wait ceiling ends at the one-hour watchdog boundary, so one native wait cannot perform an internal hourly check and remain asleep for the 12-hour contract. No independent native watchdog mechanism is exposed. No 65-minute experiment was run. |
| `healthy_zero_parent_context` | `unknown` | protocol surface only | Run the capability capture command above. | `evidence/m-1-native-d2/capability-probe.json` | `thread/read` can omit turns and thread notifications return empty turn lists, but no runtime parent-context trace proves that repeated healthy checks add zero parent items. |
| `long_tool_is_healthy` | `unknown` | protocol surface only | Run the capability capture command above. | `evidence/m-1-native-d2/capability-probe.json` | The schema identifies in-progress command, MCP, dynamic, and collab tool items, but it does not define a native stalled classifier or prove the required runtime distinction. |
| `abnormal_wakeup` | `unknown` | protocol surface only | Run the capability capture command above. | `evidence/m-1-native-d2/capability-probe.json` | Thread and collab status enums include `systemError`, `errored`, `interrupted`, and `notFound`; no bounded fixture proved parent wakeup for every required abnormal class. |
| `wrong_turn_rejected` | `unknown` | protocol declaration only | Run the capability capture command above. | `evidence/m-1-native-d2/capability-probe.json` | `turn/steer` requires `expectedTurnId` and declares mismatch rejection, but no second live thread was started to convert the declaration into runtime evidence. |
| `child_interrupt_parent_safe` | `unknown` | protocol declaration only | Run the capability capture command above. | `evidence/m-1-native-d2/capability-probe.json` | `turn/interrupt` is scoped to child `threadId` and `turnId`, but no behavior fixture proved parent non-interruption and absence of a concurrent parent turn. |
| `orchestrator_failure_wakeup` | `unknown` | protocol surface only | Run the capability capture command above. | `evidence/m-1-native-d2/capability-probe.json` | Error and terminal status surfaces exist, but no safe bounded fault injection proved that connection or orchestration failure wakes the parent instead of remaining silent. |
| `twelve_hour_deadline` | `fail` | observed config-parser behavior | Run the capability capture command above. | `evidence/m-1-native-d2/capability-probe.json` | The parser rejects 43,200,000ms and caps native wait at 3,600,000ms. A fake clock is tested only as harness logic and is not counted as platform support. |

The two deadline contracts fail on the current version, so the native route
cannot satisfy GKD D2 even though normal child final wakeup works. Unknowns are
left unresolved rather than upgraded from schema names. The only permitted
conclusion is `native_insufficient`; `external_watcher_supported` is outside
this task.
