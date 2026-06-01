Debug loop:
- Repro: minimal failing test.
- Isolate: narrow suspect modules; instrument logs.
- Fix: smallest patch; add guard tests.
- Document root cause + prevention → repo docs (`docs/**`) + ConPort decision/progress:/docs/postmortems/<short>.md

> Token thrift:
- **ConPort**: prefer summaries/search with small `limit` (3–5) before full context.
