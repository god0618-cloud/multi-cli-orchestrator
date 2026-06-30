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

`claude-code` is the first implemented supervised first-party adapter in v1.5. The disabled template is intentionally retained as a design-history marker for how first-party adapters start: no execution authority until doctor, sandbox, budget, non-interactive execution, and evidence reporting all exist.

Runtime check:

```bash
mco adapter capabilities claude-code
mco adapter doctor claude-code --sandbox templates/sandbox-contracts/claude-code-supervised.json
```
