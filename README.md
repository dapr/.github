# .github

Shared GitHub Actions workflows for the [dapr](https://github.com/dapr) organisation.

## Shared workflows

### Automerge and autoupdate ([`automerge.yaml`](.github/workflows/automerge.yaml))

Squash-merges PRs labelled `automerge` that have been approved by a maintainer. Also updates branches of PRs labelled `automerge` or `autoupdate` that have fallen behind their base branch.

With `merge-via-queue: true`, instead of merging directly the workflow enables GitHub auto-merge ("merge when ready") on the PR, so it is merged by GitHub as soon as all requirements pass — including going through the merge queue if the base branch uses one. Use this on repositories where the base branch requires a merge queue, since GitHub rejects direct API merges there. Requires **"Allow auto-merge"** to be enabled in the repository settings (Settings → General → Pull Requests), otherwise enabling auto-merge fails and the PR is not merged.

```yaml
# .github/workflows/dapr-bot-schedule.yml
on:
  schedule:
    - cron: '*/10 * * * *'
  workflow_dispatch:

permissions: {}

jobs:
  automerge:
    uses: dapr/.github/.github/workflows/automerge.yaml@main
    with:
      maintainer-teams: maintainers,co-maintainers
      # merge-via-queue: true   # default: false; enqueue via auto-merge instead of merging directly
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

permissions: {}

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
        #   commit: ''           # dapr/cli commit SHA or ref; builds from source, overrides version
```

### Setup Dapr Runtime ([`setup-dapr-runtime`](.github/actions/setup-dapr-runtime/action.yaml))

Initialises the Dapr runtime via `dapr init`. Requires the Dapr CLI to be installed first (use `setup-dapr-cli`). Defaults to the highest semver release.

`version` and `commit` are complementary: `dapr init` always runs (using `version` to set up the runtime environment — Redis, Zipkin, placement service, etc.), and if `commit` is also set, the `daprd` binary is replaced with one built from that ref afterwards.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: dapr/.github/.github/actions/setup-dapr-cli@main

      - uses: dapr/.github/.github/actions/setup-dapr-runtime@main
        # with:
        #   version: '1.14.0'   # version passed to "dapr init"; omit to use latest stable
        #   commit: ''           # dapr/dapr commit SHA or ref; builds daprd from source and
        #                        # replaces the binary after init (version still controls init)

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

permissions: {}

jobs:
  backport:
    uses: dapr/.github/.github/workflows/backport.yaml@main
    secrets:
      dapr_bot_token: ${{ secrets.DAPR_BOT_TOKEN }}
```
