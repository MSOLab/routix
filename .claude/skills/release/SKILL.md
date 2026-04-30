---
name: release
description: Full release workflow for routix: clean dist, build with uv, publish to PyPI, and create a GitHub release. Use this skill whenever the user says "release" or "publish", or anything about shipping a new version of the routix package. Always invoke this skill — don't attempt the steps manually.
---

# Release Workflow

Runs the full routix release pipeline in this exact order:

1. Read the version from `pyproject.toml`
2. Clean `dist/`
3. `uv build`
4. `uv publish`
5. `gh release create`

Confirm the version with the user before starting. Stop on any failure and report what went wrong.

## Step-by-step

### 1. Get current version

```bash
uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"
```

Show the user: "Start releasing routix v{version}?" and wait for confirmation.

### 2. Clean dist/

```bash
rm -rf dist/
```

### 3. Build

```bash
uv build
```

### 4. Publish to PyPI

```bash
uv publish
```

`uv publish` reads credentials from the `UV_PUBLISH_TOKEN` environment variable or `~/.config/uv/credentials.toml`. If authentication fails, tell the user to set `UV_PUBLISH_TOKEN`.

### 5. Create GitHub release

```bash
gh release create v{version} dist/* \
  --repo MSOlab/routix \
  --title "v{version}" \
  --generate-notes
```

`--generate-notes` auto-generates release notes from git commits since the last tag. If the user wants to write custom notes, ask before running this step.

## Error handling

- If any step fails, stop immediately and print the error output.
- Do not proceed to the next step on failure.
- If `uv publish` fails with a version conflict (version already exists on PyPI), tell the user to bump the version in `pyproject.toml` first.
- If `gh release create` fails because the tag already exists, offer to delete the old release and recreate it, but ask first.
