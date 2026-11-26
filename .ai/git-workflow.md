# Git Workflow

## Branches and scope

- Branch from the current default branch and use a short, descriptive branch
  name such as `feat/client-roles` or `fix/token-audience-validation`.
- Keep each branch focused on one change. Separate unrelated refactors,
  formatting, dependency upgrades, and generated files.
- Never commit `.env` files, credentials, local databases, virtual
  environments, logs, or build output.

## Commits

Use small, reviewable commits with imperative subjects. A subject should say
what the commit does, for example:

```text
Add refresh-token rotation checks
```

Keep the body useful when context, migration details, security impact, or
operational follow-up is not obvious. Do not mix a behavior change with a
large unrelated reformat. Before committing, inspect `git diff` and
`git diff --check`, and confirm no unrelated user changes are staged.

## Change review

Before opening a pull request:

1. Run focused tests and relevant full checks.
2. Review API, migration, security, deployment, and worker implications.
3. Confirm configuration and documentation are updated.
4. Describe behavior, validation performed, known limitations, and rollback
   considerations.

Never rewrite shared history or force-push without team agreement. Do not
  amend or reset another contributor's work. Resolve merge conflicts by
  preserving intended behavior and rerun affected tests after resolution.

## Database and releases

Schema changes require a reviewed Alembic migration and a deployment-safe
rollout plan. Prefer backward-compatible expand/migrate/contract changes for
live systems. Ensure image/build changes are reproducible and that API and
worker compatibility is considered when deploying them independently.
