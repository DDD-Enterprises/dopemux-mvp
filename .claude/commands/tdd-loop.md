#tdd
1) Generate failing tests under tests/** for behaviors: [list].
2) Ask for Edit permission (tests only). Run tests; show failures.
3) Propose a minimal src/** patch; request Edit permission.
4) Run `make lint`, `make type-check`, and pytest with coverage on the touched code (target ≥90%). Stop when green.
5) Emit ADR stub if design shifted.
