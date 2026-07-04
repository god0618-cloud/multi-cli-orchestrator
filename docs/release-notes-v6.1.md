# Release Notes v6.1.0a1

v6.1.0a1 adds runtime resilience to Multi-CLI Orchestrator.

The goal is narrow: if a worker claims a dispatch and disappears, the owner should not be stuck guessing. The task now records lease, heartbeat, reclaim, and retry exhaustion evidence in the dispatch JSON, `RUN_LEDGER.json`, and dashboard.

## Highlights

- Dispatch records now include:
  - `attempt`
  - `max_attempts`
  - `lease_expires_at`
  - `last_heartbeat_at`
  - `reclaim_count`
  - `last_reclaimed_at`
- `mco dispatch claim --lease-seconds 900` acquires a lease and increments the attempt count.
- `mco dispatch heartbeat` extends a claimed dispatch lease.
- `mco dispatch reclaim` returns stale claimed dispatches to the queue or blocks exhausted retries.
- `RUN_LEDGER.json` now records:
  - `dispatch_lease_acquired`
  - `dispatch_heartbeat`
  - `dispatch_reclaimed`
  - `dispatch_attempts_exhausted`
- The boss dashboard includes a Runtime Resilience panel with lease state, attempt count, reclaim count, lease expiry, and heartbeat timestamps.

## Safety Posture

v6.1 does not add an unbounded daemon.

Recovery remains explicit and bounded:

```bash
mco dispatch reclaim <task_id>
```

Long-running automation can call that command periodically, but the core product still avoids hidden background authority.

## Verification

Expected verification:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests
PYTHONPATH=src python3 -m mco.cli release check .
PYTHONPATH=src python3 -m mco.cli audit .
```

Regression coverage proves:

- claimed dispatches receive lease and attempt metadata,
- heartbeat extends the lease and writes ledger evidence,
- stale claimed dispatches are returned to the queue while attempts remain,
- exhausted stale dispatches become blocked,
- dashboard output surfaces Runtime Resilience state.

## Known Limits

- There is no always-on reclaim daemon yet.
- Reclaim is task-scoped, not workspace-global.
- Mimo Code and CodeWhale remain manual-only.
- Provider-account quota remains unknown unless task-local evidence supports a narrower claim.
