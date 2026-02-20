# GitHub Configuration

This directory contains GitHub-specific configuration files for the EV Infrastructure Optimization project.

## Contents

### Workflows (`workflows/`)
- **python-ci.yml** - Automated CI/CD pipeline that:
  - Runs on Python 3.8, 3.9, 3.10, 3.11
  - Performs linting checks
  - Tests data pipeline and individual phases
  - Triggered on push to main/develop and PRs

### Issue Templates (`ISSUE_TEMPLATE/`)
- **bug_report.md** - For reporting bugs
- **feature_request.md** - For suggesting new features
- **documentation.md** - For documentation improvements
- **question.md** - For asking questions

### Pull Request Template (`pull_request_template.md`)
Standard template for all pull requests to ensure consistency and completeness.

## Automatic Features Enabled by This Configuration

1. **Issue Templates** - GitHub will automatically show these templates when users create new issues
2. **PR Template** - Appears when creating new pull requests
3. **CI/CD Pipeline** - Automatically runs tests on every push and PR
4. **Branch Protection** - Can be configured to require passing CI checks before merging

## Setup Instructions (Local Development)

See [GETTING_STARTED.md](../GETTING_STARTED.md) for development setup.

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.
