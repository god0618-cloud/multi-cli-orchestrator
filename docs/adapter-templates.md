# Adapter Templates

`templates/adapters/*.disabled.json` files document future first-party adapter shapes.

They are intentionally disabled:

- `supervised=false`
- `can_read_inbox=false`
- `can_write_artifacts=false`
- `can_run_shell=false`
- `quota_status=unknown`

The project must not turn these into executable adapters until each adapter has:

- adapter doctor implementation
- sandbox contract enforcement
- quota preflight
- non-interactive command contract
- evidence reporter

Current templates:

- `claude-code.disabled.json`
- `kimi-code.disabled.json`
- `mimo-code.disabled.json`
- `codewhale.disabled.json`

Use:

```bash
mco schema validate adapter-manifest templates/adapters/claude-code.disabled.json
```

