# Release Checklist

Use this checklist before publishing the repository.

## Required

- [ ] Initialize git and make a clean first commit.
- [ ] Run unit tests.
- [ ] Run package install smoke.
- [ ] Run hello demo smoke.
- [ ] Run safe execution smoke.
- [ ] Run unsafe command rejection smoke.
- [ ] Run `mco audit .`.
- [ ] Run `mco release check .`.
- [ ] Confirm no generated cache files are present. `mco release check .` reports these as WARN because editable installs may generate them.
- [ ] Confirm no private paths, credentials, screenshots, or business data are present.
- [ ] Confirm `README.md`, `CHANGELOG.md`, and `ROADMAP.md` match the package version.
- [ ] Confirm `docs/release-notes-v3.0.md` matches the release tag.
- [ ] Confirm source-tree templates and packaged templates contain the same JSON filenames.
- [ ] Confirm first-party adapter templates are disabled by default.
- [ ] Confirm no command grants arbitrary shell execution.

## Recommended

- [ ] Add screenshots or diagrams to the README.
- [ ] Add a short demo GIF after the dashboard UI matures.
- [ ] Add GitHub topics.
- [ ] Add a SECURITY contact.
- [ ] Add a public issue template for adapter requests.
- [ ] Add a pull request template with audit and release-check gates.

## Release Gate

Do not publish if any of these are true:

- `mco audit .` reports `FAIL > 0`
- `mco release check .` reports `FAIL > 0`
- first-party adapters can execute by default
- private machine paths appear in repository files
- command examples require private local infrastructure
- CI cannot run without secrets
