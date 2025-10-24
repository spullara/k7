# Contributing to K7

Thanks for your interest in contributing!

We chose a lean and minimal approach to make development on this project as simple as possible:
- Infra is handled by a single Ansible playbook
- The CLI and API are implemented respectively with Typer and FastAPI in Python, for simplicity. They both wrap over the same `core` module. 

## Project Direction

Check out the [ROADMAP.md](ROADMAP.md) to see planned features, current priorities, and long-term goals. It's a great starting point if you're looking for areas to contribute!

## Repo Layout
- `src/k7/` CLI, core logic, API server
- `src/katakate/` Python SDK (published to PyPI as katakate)
- `src/k7/deploy/` Ansible playbook to install node
- `utils/` helper scripts

## Packaging
- The root Python packaging (`setup.py` and `MANIFEST.in`) builds the `katakate` SDK for PyPI only.
- Assets under `src/k7/` (including `src/k7/deploy/*`) are not included in the PyPI package; they are used by the Debian/CLI packaging flow.

## Code Style
- Python: PEP8, explicit types for public APIs, early returns, no inline comments
- Lint/format with Ruff:
  - Install: `pip install ruff`
  - Check: `ruff check src`
  - Format: `ruff format src`

## Building
- CLI deb helpers live in `src/k7/cli/` scripts
- Make targets may be available: `make` to list

## Releases
- Bump versions in `src/k7/__init__.py` and `src/katakate/__init__.py`
- Tag `vX.Y.Z` to build artifacts (CI may publish .deb and wheels)

## Reporting Issues
- Include steps, expected vs actual, logs, and environment (arch/OS/hardware)