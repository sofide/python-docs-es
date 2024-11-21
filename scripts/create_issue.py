"""
Run this script with one variable:
 - PO filename to create an issue for that file
 - or '--all' to create the issues for all untranslated files that doesn't have an open issue already
 - or '--one' to create the next one issue
"""

import os
import sys
from glob import glob
from pathlib import Path

from github import Github
from potodo.potodo import PoFileStats


g = Github(os.environ.get('GITHUB_TOKEN'))
repo = g.get_repo('python/python-docs-es')

PYTHON_VERSION = "3.13"
ISSUE_LABELS = [PYTHON_VERSION, "good first issue"]
ISSUE_TITLE = 'Translate `{pofilename}`'
ISSUE_BODY = '''This needs to reach 100% translated.

The rendered version of this file will be available at https://docs.python.org/es/{python_version}/{urlfile} once translated.
Meanwhile, the English version is shown.

Current stats for `{pofilename}`:

- Fuzzy: {pofile_fuzzy}
- Percent translated: {pofile_percent_translated}%
- Entries: {pofile_entries}
- Untranslated: {pofile_untranslated}

Please, comment here if you want this file to be assigned to you and a member will assign it to you as soon as possible, so you can start working on it.

Remember to follow the steps in our [Contributing Guide](https://python-docs-es.readthedocs.io/page/CONTRIBUTING.html).'''


class IssueAlreadyExistingError(Exception):
    """Issue already existing in GitHub"""


class PoFileAlreadyTranslated(Exception):
    """Given PO file is already 100% translated"""



def check_issue_not_already_existing(pofilename):
    issues = repo.get_issues(state='open')
    for issue in issues:
        if pofilename in issue.title:

            print(f'Skipping {pofilename}. There is a similar issue already created at {issue.html_url}')
            raise IssueAlreadyExistingError()


def check_translation_is_pending(pofile):
    if pofile.fuzzy == 0 and any([
        pofile.translated == pofile.entries,
        pofile.untranslated == 0,
    ]):
        print(f'Skipping {pofile.filename}. The file is 100% translated already.')
        raise PoFileAlreadyTranslated()



def issue_generator(pofilename):
    pofile = PoFileStats(Path(pofilename))

    check_issue_not_already_existing(pofilename)
    check_translation_is_pending(pofile)

    urlfile = pofilename.replace('.po', '.html')
    title = ISSUE_TITLE.format(pofilename=pofilename)
    body = ISSUE_BODY.format(
        python_version=PYTHON_VERSION,
        urlfile=urlfile,
        pofilename=pofilename,
        pofile_fuzzy=pofile.fuzzy,
        pofile_percent_translated=pofile.percent_translated,
        pofile_entries=pofile.entries,
        pofile_untranslated=pofile.untranslated,
    )
    # https://pygithub.readthedocs.io/en/latest/github_objects/Repository.html#github.Repository.Repository.create_issue
    issue = repo.create_issue(title=title, body=body, labels=ISSUE_LABELS)

    return issue

def create_issues(only_one=False):
    po_files = glob("**/*.po")
    existing_issue_counter = 0
    already_translated_counter = 0
    created_issues_counter = 0

    print(f"TOTAL PO FILES: {len(po_files)}")

    for pofilename in po_files:
        try:
            issue = issue_generator(pofilename)
            created_issues_counter += 1
            print(f'Issue "{issue.title}" created at {issue.html_url}')
            if only_one:
                break
        except IssueAlreadyExistingError:
            existing_issue_counter += 1
        except PoFileAlreadyTranslated:
            already_translated_counter += 1

    print("Stats:")
    print(f"- Existing issues: {existing_issue_counter}")
    print(f"- Already translated files: {already_translated_counter}")
    print(f"- Created issues: {created_issues_counter}")




def main():
    error_msg = "Specify PO filename or '--all' to create all the issues, or '--one' to create the next one issue"
    if len(sys.argv) != 2:
        raise Exception(error_msg)

    arg = sys.argv[1]

    if arg == "--all":
        create_issues()

    elif arg == "--one":
        create_issues(only_one=True)

    else:
        try:
            issue_generator(arg)
        except FileNotFoundError:
            raise Exception(error_msg)

if __name__ == "__main__":
    main()
