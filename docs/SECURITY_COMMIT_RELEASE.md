# Security, Commit, And Release

1. Read project security rules and scan exact staged scope.
2. Record full security evidence.
3. Commit source as C1.
4. Write .devad/docs/commits/C1.md.
5. Commit only attestation files as C2.
6. Validate C1/C2 and exact remote target.
7. Push source only after validation.
8. Keep deploy readiness, live deployment, and live proof as separate gates.

C2 does not require a recursive attestation. Historical PASS does not open a
current gate. Final destructive actions remain owner-run.
