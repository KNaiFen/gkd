# GKD-O1 交付

## 结果

- Outcome: `core_cleanup_ready`
- Fixed base: `4639a1bae97a56d293def0b5c2cf5d8406bfb217`
- Claim base head: `44ab961717791504466d4de492ff27ecb33dbf65`
- Claim: `1f3bac2bd32511a7592e84b1f5a745dac1ed3cb6defc569febce975f3990beb5`
- Implementation head: `4235ec653ec8b46b404312f9d5d1631679dddaef`

本交付只移除确认无调用的五个 payload helper，将 legacy v1 测试构造器移到
`tests/task_core/helpers.py`，并把 foundation executable/metadata mode drift 反例
合并为一个 `subTest` 表达。公开 CLI、task/role/release API、manifest 语义、watcher、
probe、optional pack、生产目录和 AIO 均未修改。

## 证据

- Execution bundle digest: `d749b753fb11aeab44d41b4e1d8bec44c7fa2d18a4b08148fbc0e0c127e27e6d`
- Candidate output bundle digest: `273873360cb7e3115a54dfef7e6840611457cc8c4d3af80384670b32630f1dc0`
- Foundation evidence digest: `8c61d40df9e8e64ceeeebdb2fd0b870bfaece5a6fd2325c8b5c7a25b1eee7c6e`
- Evidence file SHA-256 (two runs): `570ec8ba4c4bc3dbef11442afd8aba01b183a22412f3db98a3e04b9019dfa3fc`

两次 foundation evidence 均为 `canonical_foundation_ready`，输出逐字节一致，temporary
root 在终态为空。candidate bundle 在隔离 temporary root 中 install、verify、version
均通过，并返回上述 candidate digest。

## 验证

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=canonical/payload/lib:. python3 -B -m unittest discover tests/task_core -p 'test_*.py' -t .
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=canonical/payload/lib:. python3 -B -m unittest discover tests/foundation -p 'test_*.py' -t .
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=canonical/payload/lib:. python3 -B -m unittest discover tests/ci_policy -p 'test_*.py' -t .
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=canonical/payload/lib:. python3 -B -m unittest discover tests/review_core -p 'test_*.py' -t .
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=canonical/payload/lib:. python3 -B -m unittest discover tests/release_candidate -p 'test_*.py' -t .
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/gkd-verify --base-sha 4639a1bae97a56d293def0b5c2cf5d8406bfb217
```

Focused tests passed: task-core 135, foundation 52, CI 29, review 11, release 15.
The full verifier passed all 433 tests across its 11 scopes. No dependencies were installed,
and no production-home, AIO, GitHub settings, Secrets, runner, tag or Release action occurred.

## 停止边界

本文件单独提交后，executor 只调用 `gkd-task deliver` 绑定本文件、实现提交和
candidate output bundle digest，然后停止；不验收、不合并、不归档、不清理 worktree 或
分支，不启动其他任务。后续 acceptance 与 merge 只由 trusted main 按固定 head 处理。
