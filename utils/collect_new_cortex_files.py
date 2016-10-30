"""collect new files for cortex-exp repo"""

from sys import argv
import os
import hashlib
import json
from datasmartleelabutil.cortex_exp import files_to_ignore, cortex_file_exts
from datasmartleelabutil.git import check_git_repo_clean


def collect_cortex_files_one_case(folder, existing_dict):
    files_in_folder = os.listdir(folder)
    for x in files_in_folder:
        x_normalized = x.lower()
        x_ext = os.path.splitext(x_normalized)[1]
        if x_ext in cortex_file_exts:
            # read this file, and compute its SHA1
            with open(os.path.join(folder, x), 'r', encoding='utf-8') as f:
                # so always use windows style, in case accidentally a unix style file is there.
                data = f.read().replace('\n', '\r\n').encode('utf-8')
            with open(os.path.join(folder, x), 'rb') as f:
                data_raw = f.read()

            if data_raw != data:
                data_raw_fixed = data_raw.replace(b'\n', b'\r\n')
                assert data_raw_fixed == data
                input('{} does not have CRLF ending; press enter to ignore this, or ctrl+c to stop and fix this'.format(
                    os.path.join(folder, x)))

            # here SHA1 is just to speed up.
            x_sha1 = hashlib.sha1(data).hexdigest()
            if x_normalized in existing_dict:
                x_sha1_old = existing_dict[x_normalized]['sha1']
                assert x_sha1_old == x_sha1, 'unequal sha1 for {}/{}, old one {}, new one {}'.format(
                    folder, x, x_sha1_old, x_sha1
                )
            else:
                existing_dict[x_normalized] = {
                    'sha1': x_sha1,
                    'data': data
                }


def copy_cortex_files_to_git(folder, existing_dict):
    old_files_in_folder = os.listdir(folder)
    for x in existing_dict:
        if x not in old_files_in_folder:
            # good, just write new files
            print('create {}'.format(x))
            with open(os.path.join(folder, x), 'wb') as f:
                f.write(existing_dict[x]['data'])
        else:
            # compare that if the old file is same as the new ones.
            with open(os.path.join(folder, x), 'rb') as f:
                sha1_old_file = hashlib.sha1(f.read()).hexdigest()
            assert sha1_old_file == existing_dict[x]['sha1'], \
                'old {} in git is different from the one here!'.format(x)


def main(repo_root, data_folder_for_exp, exp_name):
    cortex_file_dict = dict()
    assert exp_name == exp_name.lower(), 'experiment name must be lower case'
    # first, loop over all sub folder structures in data_folder_for_exp
    for x in os.walk(data_folder_for_exp):
        if set(x[2]) - files_to_ignore:
            collect_cortex_files_one_case(x[0], cortex_file_dict)
    # then, compare each file in collect_cortex_files_one_case to those in git repo.
    # first, you must create the folder exp_name in repo_root
    project_root_repo = os.path.join(repo_root, exp_name)
    # check git clean
    assert check_git_repo_clean(repo_root)
    assert os.path.exists(project_root_repo), 'create {} first!'.format(project_root_repo)

    # copy new files to git
    copy_cortex_files_to_git(project_root_repo, cortex_file_dict)


if __name__ == '__main__':
    # TODO: add a minimal date to start process; older things will be discarded.
    assert len(argv) == 4, "usage: {} REPO_ROOT DATA_FOLDER_FOR_EXP EXP_NAME".format(argv[0])
    main(*argv[1:])
