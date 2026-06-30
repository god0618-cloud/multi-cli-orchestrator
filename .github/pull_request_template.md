## Summary

What changed and why?

## Verification

- [ ] `python -m unittest discover -s tests -p 'test_*.py' -v`
- [ ] `mco audit .`
- [ ] `mco release check .`

## Safety

- [ ] No private paths, credentials, screenshots, or business data.
- [ ] No arbitrary shell execution.
- [ ] New adapters remain disabled by default unless a dedicated safety review approved execution.
- [ ] Evidence artifacts or docs are updated where behavior changed.

## Notes

Known gaps or follow-up work:

