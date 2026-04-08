# GitHub Actions Strategy

## Goal

This document describes the recommended GitHub Actions strategy for this repository.

The objective is to ensure that code only reaches `main` after passing automated validation in feature branches and pull requests.

This repository intentionally does **not** validate local raw data files in CI because:

- raw data is not part of the Git contract for the project
- local `data/` was used only for development and testing
- production raw data will eventually be stored in S3

Therefore, CI focuses on:

- source code quality
- notebook hygiene
- documentation quality
- secret detection

## Proposed Workflows

### 1. `ci.yml`

Purpose:

- validate Python code quality
- catch syntax errors
- run unit tests
- scan for secrets

Checks included:

- `ruff check src`
- `ruff format --check src`
- `python -m compileall src`
- `PYTHONPATH=. pytest`
- `gitleaks/gitleaks-action@v2`

### 2. `notebooks.yml`

Purpose:

- ensure notebooks are safe to merge
- avoid bloated notebook outputs in the repository
- detect suspicious strings that may indicate secrets or tokens

Checks included:

- notebook JSON structure validation
- reject notebooks with outputs
- reject notebooks with suspicious secret-like strings

### 3. `docs.yml`

Purpose:

- keep project documentation readable and consistent

Checks included:

- Markdown lint for `README.md` and `docs/**/*.md`

### 4. `auto-pr.yml`

Purpose:

- run a full validation gate on feature branches
- automatically create or reuse a pull request to `main`
- ensure a branch only auto-opens a PR after every configured validation succeeds

Checks included before PR creation:

- code validation
- notebook validation
- documentation validation
- secret scan

## Recommended Branch Protection for `main`

These settings must be configured in GitHub repository settings.

Recommended rules:

- disable direct push to `main`
- require pull request before merging
- require at least 1 approving review
- require status checks to pass before merging
- require branch to be up to date before merging
- optionally require conversation resolution before merging

## Recommended Required Status Checks

Mark these checks as required on `main`:

- `Lint, Tests, and Security`
- `Secret Scan`
- `Validate Notebooks`
- `Markdown Lint`

## Suggested Development Flow

```text
feature branch
  -> push commits
  -> GitHub Actions run
  -> auto-pr workflow validates branch
  -> auto-pr workflow creates or reuses PR to main
  -> open pull request to main
  -> checks pass
  -> review approved
  -> merge to main
```

## Why This Strategy Fits This Project

This setup is a strong fit for the current stage of the repository because it:

- protects the quality of Python ingestion code
- avoids accidental secret leakage
- keeps notebooks clean and reviewable
- keeps documentation in good shape
- avoids over-engineering CI around local data files that will not live in Git
- reduces manual PR creation for feature branches

## Future Evolution

As the project grows, the CI strategy can expand to include:

- `mypy`
- test coverage thresholds
- Terraform validation
- Airflow DAG validation
- Spark job validation
- packaging and release automation

For now, the current GitHub Actions setup is intentionally lean, practical, and aligned with the real repository contract.
