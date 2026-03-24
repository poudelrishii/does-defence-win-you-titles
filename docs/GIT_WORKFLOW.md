# Git Workflow Guide
## Does Defence Win You Titles?

---

## Branch Strategy

We use GitHub Flow — lightweight and suitable for solo analysis projects.
```
main
  └── feature/project-config
  └── feature/data-collection
  └── feature/data-processing
  └── feature/visualizations
  └── feature/pipeline
  └── feature/notebooks
  └── feature/tests
  └── feature/documentation
```

**Rule:** Never commit directly to main after initial setup.
Always: branch → create files → stage → commit → push → PR → merge

---

## Commit Message Convention
```
<type>(<scope>): <short summary>
```

| Type | When to use |
|---|---|
| feat | New functionality |
| fix | Bug fix |
| docs | Documentation only |
| refactor | Code restructure |
| test | Adding tests |
| chore | Setup and config |

---

## Complete Commit Reference

| Branch | Files | Message |
|---|---|---|
| main | .gitignore, .env.example, requirements.txt | chore: add project config and dependency files |
| feature/project-config | config.py, __init__.py files | chore: add central config and package init files |
| feature/data-collection | api_client.py, data_fetcher.py | feat(collector): add API client with caching and standings fetcher |
| feature/data-processing | cleaner.py, feature_engineer.py | feat(processor): add data cleaning and feature engineering pipeline |
| feature/visualizations | eda_plots.py, league_plots.py, summary_plots.py | feat(viz): add all 10 chart functions |
| feature/pipeline | main.py | feat(pipeline): add main entry point with full CLI pipeline |
| feature/notebooks | notebooks 01-05 | feat(notebooks): add interactive analysis notebooks 01-05 |
| feature/tests | test files | test: add unit tests for API client and cleaner |
| feature/documentation | README, docs | docs: add README and project documentation |

---

## Key Commands
```bash
# Always create branch before creating files
git checkout -b feature/my-feature

# Check what is staged
git status

# Stage specific files
git add path/to/file.py

# Commit with message
git commit -m "type(scope): description"

# Push branch and set upstream
git push -u origin feature/my-feature

# Switch back to main
git checkout main

# Pull latest main
git pull origin main

# Merge a branch into main locally
git merge feature/my-feature

# Tag a release
git tag -a v1.0.0 -m "Release description"
git push origin --tags
```

---

## Pull Request Process

1. Push your feature branch
2. Go to GitHub → you will see a prompt to open a PR
3. Title: same as your commit message
4. Description: what changed and why
5. Merge into main
6. Delete the feature branch after merging

---

## Release Tag

After all features are merged into main:
```bash
git checkout main
git pull origin main
git tag -a v1.0.0 -m "v1.0.0: complete defence analysis — 5 leagues, 5 seasons, 10 charts"
git push origin --tags
```