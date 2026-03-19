#
# Copyright 2026 The Dapr Authors
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# This script backports merged PRs to release branches based on labels.
#
# Templates use Python str.format_map() syntax: {base}, {number}, {title}, etc.
# See each BACKPORT_*_TEMPLATE env var below for available variables.

import json
import os
import re
import subprocess
import sys

from github import Github, GithubException


def run(cmd, check=True):
    print(f"+ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


# Templates — configurable via environment variables.
# label_pattern must be a Python regex with a named group (?P<base>...).
label_pattern    = re.compile(os.environ.get('BACKPORT_LABEL_PATTERN',    r'^backport (?P<base>[^ ]+)$'))
head_template    = os.environ.get('BACKPORT_HEAD_TEMPLATE',    'backport-{number}-to-{base}')
title_template   = os.environ.get('BACKPORT_TITLE_TEMPLATE',   '[Backport {base}] {title}')
body_template    = os.environ.get('BACKPORT_BODY_TEMPLATE',    'Backport {merge_commit_sha} from #{number}.')
# labels_template renders to a JSON array of strings; available vars: base, labels (JSON array).
labels_template  = os.environ.get('BACKPORT_LABELS_TEMPLATE',  '[]')

with open(os.environ['GITHUB_EVENT_PATH']) as f:
    event = json.load(f)

pr_data = event['pull_request']

if not pr_data.get('merged'):
    print("PR is not merged, skipping.")
    sys.exit(0)

merge_commit_sha = pr_data['merge_commit_sha']
pr_number = pr_data['number']
pr_title = pr_data['title']
pr_body = pr_data.get('body') or ''
action = event.get('action')

# All label names on the original PR.
all_label_names = [label['name'] for label in pr_data.get('labels', [])]
# Labels that are NOT backport labels (passed to labels_template as {labels}).
non_backport_labels = [label for label in all_label_names if not label_pattern.match(label)]

# Determine which branches to backport to.
if action == 'labeled':
    # Only process the single newly-added label.
    label_name = event.get('label', {}).get('name', '')
    m = label_pattern.match(label_name)
    target_branches = [m.group('base')] if m else []
else:
    # On 'closed', process all existing backport labels.
    target_branches = [
        m.group('base')
        for label in pr_data.get('labels', [])
        if (m := label_pattern.match(label['name']))
    ]

if not target_branches:
    print("No backport labels found, skipping.")
    sys.exit(0)

g = Github(os.environ['GITHUB_TOKEN'])
gh_repo = g.get_repo(os.environ['GITHUB_REPOSITORY'])
gh_pr = gh_repo.get_pull(pr_number)

for base_branch in target_branches:
    template_vars = {
        'base': base_branch,
        'number': pr_number,
        'title': pr_title,
        'body': pr_body,
        'merge_commit_sha': merge_commit_sha,
        'labels': json.dumps(non_backport_labels),
    }

    backport_branch  = head_template.format_map(template_vars)
    backport_title   = title_template.format_map(template_vars)
    backport_body    = body_template.format_map(template_vars)
    backport_labels  = json.loads(labels_template.format_map(template_vars))

    print(f"\nBackporting #{pr_number} to {base_branch} ...")

    # Verify the target branch exists.
    fetch = run(['git', 'fetch', 'origin', base_branch], check=False)
    if fetch.returncode != 0:
        msg = (
            f"Backporting to `{base_branch}` failed because "
            f"the branch does not exist."
        )
        gh_pr.create_issue_comment(msg)
        print(f"Branch {base_branch} not found, skipped.")
        continue

    # Create the backport branch and cherry-pick.
    run(['git', 'checkout', '-b', backport_branch, f'origin/{base_branch}'])
    cherry = run(['git', 'cherry-pick', '-s', '-x', '-m', '1', merge_commit_sha], check=False)

    if cherry.returncode != 0:
        run(['git', 'cherry-pick', '--abort'], check=False)

        msg = f"""\
Backport of #{pr_number} to `{base_branch}`.

Backporting failed due to merge conflicts. \
Please resolve manually:

```bash
git fetch origin
git checkout {backport_branch}

# Reset to base, discarding the empty placeholder commit
git reset --hard origin/{base_branch}

# Cherry-pick the merged commit
git cherry-pick -x -m 1 {merge_commit_sha}

# Resolve the conflicts, then:
git add .
git cherry-pick --continue

# Force-push to replace the placeholder commit
git push --force-with-lease origin {backport_branch}
```\
"""
        # Create an empty commit so the branch differs from base and a PR can be opened.
        run(['git', 'commit', '--allow-empty', '-m',
             f'chore: placeholder for backport #{pr_number} to {base_branch} (manual resolution required)'])
        head_sha = run(['git', 'rev-parse', 'HEAD']).stdout.strip()
        run(['git', 'push', 'origin', backport_branch])
        run(['git', 'checkout', '-'], check=False)

        # Mark the commit as failing so the PR cannot be accidentally merged.
        gh_repo.get_commit(head_sha).create_status(
            state='failure',
            context='backport/conflict',
            description='Manual conflict resolution required — do not merge.',
        )

        try:
            backport_pr = gh_repo.create_pull(
                title=backport_title,
                body=msg,
                head=backport_branch,
                base=base_branch,
            )
            print(f"Cherry-pick conflict on {base_branch}, created placeholder PR: {backport_pr.html_url}")
        except GithubException as e:
            server  = os.environ.get('GITHUB_SERVER_URL', 'https://github.com')
            repo    = os.environ.get('GITHUB_REPOSITORY', '')
            run_id  = os.environ.get('GITHUB_RUN_ID', '')
            run_url = f"{server}/{repo}/actions/runs/{run_id}" if run_id else None
            run_ref = f" See the [action run]({run_url}) for details." if run_url else ""
            fallback_msg = (
                f"Backporting to `{base_branch}` failed due to merge conflicts,"
                f" and the placeholder PR could not be created automatically.{run_ref}"
            )
            gh_pr.create_issue_comment(fallback_msg)
            print(f"Cherry-pick conflict on {base_branch}, failed to create PR ({e}), posted comment instead.")
        continue

    run(['git', 'push', 'origin', backport_branch])

    try:
        backport_pr = gh_repo.create_pull(
            title=backport_title,
            body=backport_body,
            head=backport_branch,
            base=base_branch,
        )
        if backport_labels:
            gh_repo.get_issue(backport_pr.number).add_to_labels(*backport_labels)
        print(f"Created backport PR: {backport_pr.html_url}")
    except GithubException as e:
        print(f"Failed to create PR for {base_branch}: {e}")

    run(['git', 'checkout', '-'])

print("\nDone.")
