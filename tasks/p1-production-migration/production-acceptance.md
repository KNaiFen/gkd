# GKD-P1 Production Acceptance

- Result: trusted-main production migration accepted.
- Release: `v0.1.1`; bundle digest `68188dcaeb98d93902b435c98784e242090ed18828e9d96a8dee735244f7d1ef`.
- Plan digest: `4345db67f85e394ab9492ea93d4c48c7b074ebceea61bd81e9128d648251c5f4`.
- Apply/doctor inventory digest: `b316622f47ca774accb0156ede878e4eb7248f988a51cf100f181e753da0c2a4`.
- Apply/doctor managed-surface digest: `e3c212d28747381f35ee11b364a10ae574dbaabe02e782336ed15baea58f1c05`.
- Doctor result: `production_migration_healthy`; the transaction recovery surface was removed on verified success.
- P2 global policy postimage and private rollback record were rechecked unchanged. AIO, Secrets, paid runners and GitHub settings were not modified.
