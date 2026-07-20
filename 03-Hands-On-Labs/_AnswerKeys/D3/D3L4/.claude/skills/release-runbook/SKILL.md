---
name: release-runbook
description: Use when preparing, tagging, or documenting a software release; covers changelog, version bump, tag, deploy checklist
---

## Release Runbook

1. Update CHANGELOG.md with all changes since last release
2. Bump version in pyproject.toml / package.json
3. Run `git tag -a v{version} -m "Release v{version}"`
4. Push tag: `git push origin v{version}`
5. Deploy to production using the CI pipeline
6. Announce in #releases Slack channel