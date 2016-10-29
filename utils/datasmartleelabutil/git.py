import subprocess
import string


def get_cmd_output(cmds, cwd):
    result = subprocess.check_output(cmds, cwd=cwd).decode()
    for x in result:
        assert x in string.printable
    return result


def check_git_repo_clean(repopath=None):
    if repopath is None:
        # from <http://stackoverflow.com/questions/957928/is-there-a-way-to-get-the-git-root-directory-in-one-command>
        repopath = subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).decode().strip()
        print(repopath)
    git_status_output = get_cmd_output(['git', 'status', '--porcelain'], cwd=repopath)
    assert not git_status_output, "the repository must be clean!, check {}".format(git_status_output)
    return True
