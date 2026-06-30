# Security Policy

This project is in v0.2 extraction stage and is not ready for public security reporting yet.

Security principles for the eventual public release:

- Local-first by default.
- No default writes outside the configured workspace.
- No default writes to native CLI memory, stable knowledge bases, or user profile files.
- Explicit gates for destructive actions.
- No credentials in examples, tests, templates, or documentation.

Before v1.0, this file must include supported versions and a vulnerability reporting channel.

