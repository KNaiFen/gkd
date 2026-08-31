# GKD I1 Trusted Context Symlink Boundary Delivery

Candidate output bundle: `ebbd7230edd5b3d7856c8424341b254cc23e75077ed77642cc2f2d82d303b3b3`.

The default core verifier passed 419 tests on Python 3.9.6 and Python 3.14.6.
Focused context and locator contracts cover candidate cwd, runtime attachment
candidateRoot, explicit candidate, and trusted-anchor ancestor symlinks.

All checks are fail-closed before physical path resolution; normal non-symlink
context, attachment, and planning behavior remains unchanged.
