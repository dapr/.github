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
      maintainers: maintainer1,maintainer2,maintainer3
    secrets:
      dapr_bot_token: ${{ secrets.DAPR_BOT_TOKEN }}
```

### Prune stale ([`prune-stale.yaml`](.github/workflows/prune-stale.yaml))

Marks issues and PRs as stale after 90 days of inactivity and closes them after a further 7 days.

```yaml
# .github/workflows/dapr-bot-schedule.yml
jobs:
  prune_stale:
    uses: dapr/.github/.github/workflows/prune-stale.yaml@main
    secrets:
      dapr_bot_token: ${{ secrets.DAPR_BOT_TOKEN }}
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
