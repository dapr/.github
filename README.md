# .github

Shared GitHub Actions workflows for the [dapr](https://github.com/dapr) organisation.

## Shared workflows

### Automerge and autoupdate ([`automerge.yaml`](.github/workflows/automerge.yaml))

Squash-merges PRs labelled `automerge` that have been approved by a maintainer. Also updates branches of PRs labelled `automerge` or `autoupdate` that have fallen behind their base branch.

```yaml
# .github/workflows/dapr-bot-schedule.yml
on:
  schedule:
    - cron: '*/10 * * * *'
  workflow_dispatch:

jobs:
  automerge:
    uses: dapr/.github/.github/workflows/automerge.yaml@main
    with:
      maintainer-teams: maintainers,co-maintainers
    secrets:
      dapr_bot_token: ${{ secrets.DAPR_BOT_TOKEN }}
```

### Prune stale ([`prune-stale.yaml`](.github/workflows/prune-stale.yaml))

Marks issues and PRs as stale after 90 days of inactivity and closes them after a further 7 days. The stale and close thresholds are configurable via inputs.

```yaml
# .github/workflows/dapr-bot-schedule.yml
on:
  schedule:
    - cron: '*/10 * * * *'
  workflow_dispatch:

jobs:
  prune_stale:
    uses: dapr/.github/.github/workflows/prune-stale.yaml@main
    with:
      days-before-pr-stale: 30      # default: 90
      days-before-issue-stale: 30   # default: 90
      days-before-pr-close: 7       # default: 7
      days-before-issue-close: 7    # default: 7
    secrets:
      dapr_bot_token: ${{ secrets.DAPR_BOT_TOKEN }}
```

### Setup Dapr CLI ([`setup-dapr-cli`](.github/actions/setup-dapr-cli/action.yaml))

Installs the Dapr CLI. Defaults to the highest semver release — stable releases are preferred over pre-releases of the same version.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: dapr/.github/.github/actions/setup-dapr-cli@main
        # with:
        #   version: '1.14.0'   # omit to use latest stable
```

### Setup Dapr Runtime ([`setup-dapr-runtime`](.github/actions/setup-dapr-runtime/action.yaml))

Initialises the Dapr runtime via `dapr init`. Requires the Dapr CLI to be installed first (use `setup-dapr-cli`). Defaults to the highest semver release.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: dapr/.github/.github/actions/setup-dapr-cli@main

      - uses: dapr/.github/.github/actions/setup-dapr-runtime@main
        # with:
        #   version: '1.14.0'   # omit to use latest stable

      - run: dapr --version
```

### Backport ([`backport.yaml`](.github/workflows/backport.yaml))

Backports merged PRs to release branches when a `backport/release-*` label is applied.

```yaml
# .github/workflows/backport.yaml
on:
  pull_request_target:
    types:
      - closed
      - labeled

jobs:
  backport:
    uses: dapr/.github/.github/workflows/backport.yaml@main
    secrets:
      dapr_bot_token: ${{ secrets.DAPR_BOT_TOKEN }}
```
