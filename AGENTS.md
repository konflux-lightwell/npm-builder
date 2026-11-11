# npm-builder (Python CLI)

Early scaffold for a Python CLI that will eventually replace the bash scripts
under `scripts/`. The design is not finalized — only enough is wired up to prove the pattern.

## Project structure

src/npm_builder/
  __main__.py, cli.py, logging.py   # Entry-point plumbing only
  commands/                         # CLI adapters, one module per subcommand
  build/                            # Pipeline stages, one package each (later: assess/, sbom/, collect/, publish/)
  runtime/                          # Shared runtime environment: workdir layout, git auth, CA trust
  tools/                            # Thin subprocess wrappers, one module per external program
tests/                              # Mirrors src/npm_builder/ (tests/build/, tests/runtime/, ...)

## Code structure

- **Root package**: entry-point plumbing only. Avoid adding new modules here.
- **commands/**: CLI wiring only: parsing arguments, printing output, and handling errors.
  All the business logic should be deferred to dedicated stages (see below).
- **Stages**: one per pipeline step. Stages never import each other;
  shared code goes to `runtime/` or `tools/`.
- **runtime/**: knows about the environment the CLI runs in, never about a specific workflow.
- **tools/**: take args + env, run the program, return or raise. No decisions.
- Imports flow one way: `commands -> stages -> runtime, tools`.
- stdout carries only a command's result (data a caller could consume); progress, status
  and errors are logged to stderr. Stages never print — only `commands/` writes to stdout.
- Configuration comes from CLI arguments. Env vars are only for fixed environment
  details and for the env passed to bash subprocesses.

## Checks

Before committing, run ruff and pytest via `uv run`, plus:

- `uv run pytest --cov` (enforces the coverage gate; plain `pytest` skips it)
- `uv run bandit -r src/npm_builder/ -ll`
- `uv audit` when dependencies change

## Git

- Only commit when asked. Never push unless asked.
- Use Conventional Commits (`feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `build`, `ci`), even though older history doesn't.
- One logical change per commit; tests and ruff must pass at every commit.
- Always commit with `git commit -s`.
- Jira: take the ticket from the branch name or the user's request; never invent one; omit if none.
- Fixing a bug introduced earlier on this (unmerged) branch: amend if it's HEAD, otherwise `git commit --fixup=<sha>` then `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash main`.
- Don't commit plans/design docs unless asked.

## Scripts migration plan

Scripts are ported one at a time. A script stays in `scripts/` until its
Tekton task and the Containerfile switch to the CLI; then it is removed.

Below is an initial proposal on how the migration can be done, but it can be adjusted as the
process evolves. Every port from `scripts/` must preserve the bash script's functional behavior.

| Script | Target |
|---|---|
| `build-npm-packages` | `build/` (in progress) |
| `build-npm-package` | `build/` (called as a subprocess via `tools/` until ported) |
| `assess-npm-compliance`, `lookup-npm-tl-compliance` | `assess/` |
| `generate-npm-sbom`, `verify-npm-sbom` | `sbom/` |
| `collect-npm-artifacts`, `collect-npm-package-outputs`, `record-npm-packages-built` | `collect/` |
| `npm-publish-pulp` | `publish/` |
| `select-builder-node` | `runtime/` |
| `npm-workdir-env.sh`, `npm-workdir-load.sh` | `runtime/workdir.py` |

This is a temporary section that should orient the migration and be removed once the migration is over.
