# GKD-GATE-REPAIR Acceptance

## Outcome

Rejected. PR #39 fixed head `1952745266a84e02ca86c8a2cb8d55e4a590afd4` 未合并。

## Evidence

- 独立 acceptor 在 trusted main `bbeee84cd8198442414577180091bbaa43ebc46b` 上运行 candidate exact head 的 verifier：436 项中 1 项失败，`result-manifest.schema.json` 已安装但 packaging expected set 未同步。
- fixed-head CI terminal 为 `failure / REQUIRED_CHECK_FAILED`，观察 head 精确为 `1952745266a84e02ca86c8a2cb8d55e4a590afd4`；CI terminal digest 为 `0ddf978c34a4b59d6444bce3b4edf9667406c48d2020393696d9fdfafde04482`。
- lifecycle delivery 在 coordination head `4579b4bf4db46d939c556344094f522e901c6ce9` 冻结，delivery implementation head 为 `4e8a76edfd33d9881d654ca2140a78f2165ee2f0`；其后又有 `1952745266a84e02ca86c8a2cb8d55e4a590afd4` 提交，违反 delivery 后冻结。
- delivery/result manifest 的 candidate digest 仍为 `4f0ce30a47df3f327fb1ca61be38826efce2e0a7ff3a90d736528f3c74e7b7bf`，而最终 bundle digest 为 `16c2b604c729db6707fb6bbbc604fc2ec8b61cb90fe24a3a3b7c0700925a8e8d`，绑定不一致。
- trusted main `gkd-task status/doctor` 对 candidate 返回 `INVALID_TASK_STATE`；candidate 自带版本可读，说明新旧 logicalOrder/schema 兼容没有进入 trusted acceptance bundle。canonical rework 同样因 `INVALID_TASK_STATE` 未写入 candidate。
- review digest：`34c64bb8d8c339261c6230d2db040f97693b8f429523c83b8436c3d5f5577d63`。

## Boundary

未调用 accept/merge；未修改 candidate、runtime、production、AIO 或 GitHub settings/Secrets。旧 attempt 仅作为拒绝事实保留，后续不得沿同一 claim/head 重试。

