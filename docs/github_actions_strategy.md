# GitHub Actions Strategy

## Purpose

This document explains the GitHub Actions structure used in this repository,
why each workflow exists, what each workflow validates, and how the branch
protection and automatic PR flow work together.

The current CI/CD setup was designed to support a solo development workflow
with professional controls:

- no direct push to `main`
- automatic validation on branches and pull requests
- automatic pull request creation after branch validation succeeds
- merge to `main` only after required checks pass

This setup intentionally validates repository artifacts only. It does not
validate local raw data files stored under `data/`, because those files are
development-only and future production raw data will live in S3 rather than in
Git.

## High-Level Flow

The repository currently follows this sequence:

```text
feature branch
  -> commit
  -> push
  -> branch workflows run
  -> auto-pr workflow validates branch
  -> auto-pr workflow creates or reuses PR to main
  -> pull_request workflows run against main
  -> required checks pass
  -> manual merge to main
```

This gives the project a production-style pull request gate without blocking
solo development.

## Why This Approach Was Chosen

The main design goals were:

- keep `main` protected
- prevent unvalidated code from being merged
- avoid requiring direct pushes to protected branches
- preserve a clean PR-based workflow
- make the repository self-checking on every commit

The process is especially useful for this project because it contains:

- Python ingestion code
- notebooks
- documentation
- secrets risk from API integrations

Those four categories are now explicitly covered by automation.

## What Is Intentionally Out of Scope

The following are intentionally not validated by GitHub Actions right now:

- raw files under `data/bronze`
- data payload correctness from local test runs
- S3 object validation
- runtime checks against external APIs

Reason:

- local raw files are not the Git contract of the repository
- production raw data will eventually live in S3
- CI should focus on code, notebooks, docs, and security

## Current Workflows

The repository currently uses four workflow files:

- `.github/workflows/ci.yml`
- `.github/workflows/notebooks.yml`
- `.github/workflows/docs.yml`
- `.github/workflows/auto-pr.yml`

Each workflow has a different responsibility.

## 1. `ci.yml`

Path:

- [ci.yml](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/.github/workflows/ci.yml)

### Main purpose

This is the primary code quality workflow.

It validates:

- Python source formatting
- Python lint quality
- Python import and syntax safety
- unit tests
- repository secret leakage

### When it runs

It runs on:

- every `push`
- every `pull_request` targeting `main`

### Jobs inside `ci.yml`

#### `lint-and-test`

This job validates the Python codebase.

Checks performed:

- `ruff check src`
  Detects Python style issues, unused imports, and common code smells.
- `ruff format --check src`
  Ensures the Python code follows a consistent formatter style.
- `python -m compileall src`
  Detects syntax and import parsing problems early.
- `PYTHONPATH=. pytest`
  Runs tests currently stored under `tests/`.

Why this matters:

- catches broken code before merge
- keeps style consistent
- guarantees at least a minimum confidence level for refactors

#### `secret-scan`

This job runs Gitleaks.

Checks performed:

- scans the Git history and PR diff for secret-like content
- uses `fetch-depth: 0` to avoid shallow clone problems in pull request scans
- uses `GITHUB_TOKEN` because recent Gitleaks action versions require it

Why this matters:

- prevents accidental credential leaks
- protects API keys and tokens from entering repository history

### Why `ci.yml` exists separately

This workflow is the main required quality gate for `main`.

It is intentionally separated from notebook and markdown checks because:

- code validation has different dependencies
- failures are easier to isolate
- required checks remain easier to understand in GitHub UI

## 2. `notebooks.yml`

Path:

- [notebooks.yml](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/.github/workflows/notebooks.yml)

### Main purpose

This workflow validates notebook hygiene.

It protects the repository against:

- notebooks committed with outputs
- notebooks containing suspicious hardcoded secrets
- malformed notebook JSON structure

### When it runs

It runs only when notebook files change:

- `notebooks/*.ipynb`
- workflow file updates to `notebooks.yml`

It also runs on pull requests to `main` when notebooks are involved.

### Checks performed

- verifies notebook JSON contains the `cells` structure
- fails if any code cell still has outputs
- scans only code cells for hardcoded secret-like patterns

This scan intentionally targets real risk patterns such as:

- `os.environ["..."] = "value"`
- `token = "value"`
- `api_key = "value"`
- `apikey=...`

It does not flag normal documentation text mentioning environment variable
names.

### Why this matters

Notebook repositories often degrade quickly when outputs are committed.

This workflow keeps notebooks:

- reviewable
- smaller
- safer
- cleaner for version control

## 3. `docs.yml`

Path:

- [docs.yml](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/.github/workflows/docs.yml)

### Main purpose

This workflow validates documentation quality.

### When it runs

It runs when:

- `README.md` changes
- files under `docs/` change
- the workflow itself changes

It also runs on pull requests to `main`.

### Checks performed

- runs `markdownlint-cli2`
- validates repository Markdown style using the local
  `.markdownlint-cli2.jsonc` configuration

### Current markdownlint configuration

The repository includes:

- [.markdownlint-cli2.jsonc](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/.markdownlint-cli2.jsonc)

Current configuration choices:

- `MD013` disabled
  Long technical documentation is allowed without forcing artificial line wraps
- `MD024.siblings_only = true`
  Repeated headings are allowed when they appear in different sections

### Why this matters

This project is documentation-heavy. The docs workflow ensures:

- Markdown files stay valid and readable
- long-form technical documents remain maintainable
- documentation changes are not ignored in CI

## 4. `auto-pr.yml`

Path:

- [auto-pr.yml](C:/Users/PedroRocha/Desktop/aws-global-financial-data-platform/.github/workflows/auto-pr.yml)

### Main purpose

This workflow automates pull request creation to `main`.

It is designed to:

- validate feature branches after push
- create a PR automatically only after all validations succeed
- reuse an existing PR if one is already open

### When it runs

It runs on:

- every push to any branch except `main`

### Jobs inside `auto-pr.yml`

#### `validate-code`

Equivalent purpose to the code checks in `ci.yml`, but executed as part of the
branch gate before PR creation.

Checks:

- lint
- format check
- compile check
- tests

#### `validate-notebooks`

Equivalent purpose to `notebooks.yml`, but used inside the branch gate for PR
automation.

Checks:

- notebook structure
- output-free notebooks
- suspicious hardcoded secret patterns

#### `validate-docs`

Equivalent purpose to `docs.yml`, but used inside the branch gate for PR
automation.

Checks:

- Markdown lint

#### `secret-scan`

Equivalent purpose to the `Secret Scan` job in `ci.yml`, but used inside the
branch gate for PR automation.

Checks:

- Gitleaks scan with full fetch depth

#### `create-or-update-pr`

This job only runs if every validation job succeeds.

Behavior:

- checks whether a PR from the current branch to `main` already exists
- if it exists, the workflow does nothing
- if it does not exist, the workflow creates a PR automatically

### Why this workflow exists

Without this workflow, the branch still has to pass validation, but PR creation
remains manual.

With this workflow:

- every validated branch becomes PR-ready automatically
- the developer does not need to manually open the PR
- `main` still remains protected

### Authentication model

The workflow supports:

- preferred: `PR_CREATOR_TOKEN`
- fallback: default `github.token`

Current behavior:

- tries to use `PR_CREATOR_TOKEN` if provided
- otherwise uses `github.token`

### Important repository setting

If the workflow uses the default token, the repository must enable:

`Settings -> Actions -> General -> Workflow permissions -> Allow GitHub Actions to create and approve pull requests`

If that is not enabled, auto PR creation fails with HTTP 403.

## Branch Protection Strategy

The current strategy for `main` is:

- pull request required
- required status checks required
- direct push blocked
- merge only after checks pass
- review requirement removed for solo workflow

### Why review requirement was removed

At one point, the branch rule required at least one approving review.

That caused a practical blocker in solo development:

- the author of the PR cannot satisfy the required approval for their own PR
- merge remained blocked even when all checks passed

For a solo repository, this caused friction without adding real review value.

So the current choice is:

- keep PRs mandatory
- keep checks mandatory
- remove mandatory review approval

This preserves governance while still allowing the repository owner to merge
their own validated PRs.

## Required Checks for `main`

The recommended required checks on `main` are:

- `CI / Lint, Tests, and Security (pull_request)`
- `CI / Secret Scan (pull_request)`
- `Notebook Validation / Validate Notebooks (pull_request)`
- `Documentation Checks / Markdown Lint (pull_request)`

Only the pull request variants should be required for `main`.

Why:

- push checks are useful for early feedback
- pull request checks are the actual gate before merge
- requiring both push and pull_request variants can create duplicate noise

## Why the Current Setup Works Well

This setup gives a good balance between control and developer speed.

It keeps:

- branch protection
- CI enforcement
- notebook cleanliness
- documentation quality
- secret scanning

It removes:

- unnecessary friction from mandatory external review in a solo project

So the current model is:

```text
strict on validation
flexible on review
safe on merge
```

## How to Use This Setup Day to Day

Recommended working flow:

1. Create a feature branch.
2. Commit locally.
3. Push the branch.
4. Branch workflows run automatically.
5. If all checks pass, a PR to `main` is created automatically.
6. Pull request workflows run.
7. If the required checks are green, merge the PR.

This gives a repeatable and low-friction development loop.

## Troubleshooting Notes

### If auto PR creation fails with 403

Check one of:

1. Enable GitHub Actions pull request creation in repository settings.
2. Create a secret named `PR_CREATOR_TOKEN`.

Recommended permissions for `PR_CREATOR_TOKEN`:

- contents: write
- pull requests: write

### If Gitleaks fails on pull requests

Ensure:

- `fetch-depth: 0` is enabled in the secret scan checkout step
- `GITHUB_TOKEN` is passed to the action

### If notebooks fail validation

Check:

- outputs were cleared before commit
- no hardcoded token or API key values were written in code cells

### If docs fail validation

Check:

- Markdown syntax
- headings structure
- `.markdownlint-cli2.jsonc` configuration

## Future Evolution

As the project grows, this GitHub Actions setup can expand to include:

- `mypy`
- test coverage thresholds
- Terraform validation
- Airflow DAG validation
- Spark job validation
- package publishing or release workflows

## Summary

The current GitHub Actions design gives this repository a professional,
PR-based, validation-first workflow.

Each workflow has a clear responsibility:

- `ci.yml` validates Python code and secrets
- `notebooks.yml` enforces notebook hygiene
- `docs.yml` protects documentation quality
- `auto-pr.yml` automates validated pull request creation

Together, they ensure that `main` stays protected and that every change passes
through automated quality gates before merge.
