# Contributing to ars-production-pipeline

This repo uses a three-branch soak flow so broken code doesn't reach real client runs.

```
feature/* ──► dev ──► main
  (work)    (soak)   (blessed)
```

## Branches

| Branch | Purpose | Who merges |
|---|---|---|
| `main` | Production. Runs real client reports. | Only via `promote.bat` after `dev` has been tested. |
| `dev` | Soak / staging. Test new code here against real clients before promoting. | Feature branches merge here first. |
| `feature/*`, `fix/*`, `claude/*` | One-task work branches. | Merge into `dev` via PR. |

## Day-to-day workflow

1. **Start a new piece of work** — branch off `dev`:

   ```
   git checkout dev
   git pull origin dev
   git checkout -b feature/my-change
   ```

2. **Make changes, commit, push:**

   ```
   git add <files>
   git commit -m "fix(section): short description"
   git push -u origin feature/my-change
   ```

3. **Open a PR into `dev`** on GitHub. CI runs automatically — green checkmark = syntax and lint are clean. Merge the PR.

4. **Test `dev` against a real client** locally:

   ```
   git checkout dev
   git pull origin dev
   # run pipeline via Start Here.bat or python run.py ...
   ```

5. **When `dev` looks good, promote to `main`:**

   ```
   promote.bat
   ```

   This merges `dev` into `main` and pushes. After this, `main` has the new code and future real runs will use it.

## Golden rules

- **Never push directly to `main`.** Always go through `dev`. Branch protection on GitHub will enforce this.
- **Never merge a feature branch into `main` directly.** Always `feature → dev → main`.
- **Don't merge until you've tested.** CI catches syntax, not correctness. A real client run is the only real test.
- **When in doubt, don't merge.** Feature branches cost nothing to leave open.

## What CI does (and doesn't)

CI runs on every push and PR. It does:
- `py_compile` on every `.py` file (catches syntax errors)
- `ruff` with strict rules (catches a handful of likely-broken patterns)

It does NOT:
- Run the full pipeline (no access to M: drive from GitHub servers)
- Validate that outputs look right
- Catch logic errors

That's what the `dev` soak is for.
