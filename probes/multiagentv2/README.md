# Native multiagentv2 D2 probe

This probe captures only the fields needed for GKD-M-1A. It does not read
conversation bodies, private rollout files, or session databases, and it does
not preserve generated app-server schemas. The committed JSON contains
selected fields and digests only.

Run the seconds-scale self-tests without bytecode artifacts:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  python3 -m unittest discover -s tests/probes -p 'test_*.py' -v
```

Capture the current CLI configuration-parser behavior, bundled model catalog,
and generated protocol surface:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  python3 probes/multiagentv2/native_probe.py \
  --output evidence/m-1-native-d2/capability-probe.json
```

The generated schema proves only that a protocol field or method is declared.
It is not runtime evidence. `normal-final.json` is a separately recorded,
one-shot behavioral fixture using `gpt-5.6-sol`, `xhigh`, and
`fork_turns="none"`.
