import hashlib
import os

from .cortex_exp_master_util import cortex_file_exts, cortex_file_exts_text, cortex_file_exts_binary
from datasmart.core.util.git import check_git_repo_clean, check_commit_in_remote


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


def augment_info(info_for_each_recording, monkey_exp_pair, cortex_file_dict_this):
    # amend my info_for_each_recording with those computed sha1. this is useful later.
    for x in info_for_each_recording:
        if (x['monkey'], x['exp_name']) == monkey_exp_pair:
            assert 'ctx_sha1_dict' not in x
            x['ctx_sha1_dict'] = {
                ext: cortex_file_dict_this[x['ctx_files_dict'][ext]]['sha1'] for ext in x['ctx_files_dict']
                }


def augment_info_post_check(info_for_each_recording, git_repo_path, git_repo_hash):
    # check that git is up to date with origin/master
    assert check_commit_in_remote(git_repo_path, git_repo_hash), 'you must push the commit first'
    for x in info_for_each_recording:
        assert 'ctx_sha1_dict' in x


def check_cortex_exp_repo_wrapper(info_for_each_recording, clean_data_root, git_repo_path, git_repo_hash):
    for monkey_exp_pair in {(x['monkey'], x['exp_name']) for x in info_for_each_recording}:
        # construct a list of all folders involving this experiment and monkey
        folder_list_this = [
            os.path.join(clean_data_root, x['suffix_dir']) for x in info_for_each_recording if
            (x['monkey'], x['exp_name']) == monkey_exp_pair
            ]
        # find if there are any missing files
        cortex_file_dict_this = collect_cortex_files_one_case_wrapper(git_repo_path, folder_list_this,
                                                                      monkey_exp_pair[1])
        augment_info(info_for_each_recording, monkey_exp_pair, cortex_file_dict_this)
    augment_info_post_check(info_for_each_recording, git_repo_path, git_repo_hash)


def collect_cortex_files_one_case_wrapper(repo_root, data_folder_for_exp_list, exp_name):
    cortex_file_dict = dict()
    # first, loop over all sub folder structures in data_folder_for_exp
    for x in data_folder_for_exp_list:
        collect_cortex_files_one_case(x, cortex_file_dict)
    # then, compare each file in collect_cortex_files_one_case to those in git repo.
    # first, you must create the folder exp_name in repo_root
    project_root_repo = os.path.join(repo_root, exp_name)
    # check git clean
    assert check_git_repo_clean(repo_root)
    assert os.path.exists(project_root_repo), 'create {} first!'.format(project_root_repo)

    # copy new files to git
    copy_cortex_files_to_git(project_root_repo, cortex_file_dict)
    assert check_git_repo_clean(repo_root), 'new files are added to git. push it first!'
    return cortex_file_dict


def collect_cortex_files_one_case_inner_readfile(f_path):
    ext = os.path.splitext(f_path)[1].lower()
    if ext in cortex_file_exts_binary:
        openargs = {'mode': 'rb'}
        process_func = lambda x: x.read()
    elif ext in cortex_file_exts_text:
        openargs = {'mode': 'r', 'encoding': 'utf-8'}
        process_func = lambda x: x.read().replace('\n', '\r\n').encode('utf-8')
    else:
        raise ValueError('invalid extension {} for cortex'.format(ext))
    with open(f_path, **openargs) as f:
        # so always use windows style, in case accidentally a unix style file is there.
        data = process_func(f)
    with open(f_path, 'rb') as f:
        data_raw = f.read()

    if data_raw != data:
        data_raw_fixed = data_raw.replace(b'\n', b'\r\n')
        assert data_raw_fixed == data, "{} can't be converted between CRLF and LF perfectly".format(f_path)
        print('{} does not have CRLF ending; may not be an issue in practice'.format(f_path))

    return data


def collect_cortex_files_one_case_inner(folder, x, x_normalized, existing_dict):
    data = collect_cortex_files_one_case_inner_readfile(os.path.join(folder, x))

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


def collect_cortex_files_one_case(folder, existing_dict):
    files_in_folder = os.listdir(folder)
    for x in files_in_folder:
        x_normalized = x.lower()
        x_ext = os.path.splitext(x_normalized)[1]
        if x_ext in cortex_file_exts:
            # read this file, and compute its SHA1
            collect_cortex_files_one_case_inner(folder, x, x_normalized, existing_dict)
