# Security policy

## Reporting a vulnerability

Please report security problems in the kit privately, through GitHub's
**Report a vulnerability** button on this repository's Security tab (private
vulnerability reporting). Do not open a public issue.

Useful reports say which file or rendered output is affected, how it can be
abused, and which kit version (`_commit` in your `.copier-answers.yml`).

## What counts

The kit runs code and settings inside other people's repositories, so these are
in scope:

- a rendered workflow that leaks credentials, runs untrusted input, or grants
  more permissions than it needs;
- `tasks/apply.py` doing anything beyond what its header says;
- a gate that can be switched off without a reviewed change;
- pinned tools or images that are compromised or no longer verifiable.

## Supported versions

The latest release receives fixes. Upgrade with `uvx copier update --trust`.
