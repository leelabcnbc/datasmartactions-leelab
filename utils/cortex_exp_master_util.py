from datasmart.actions.leelab.cortex_exp import (monkey_name_mapping,
                                                 monkeylist, )

from datasmart.core.util.git import check_git_repo_clean, check_commit_in_remote

import os
import datetime
from json import load
import hashlib
from shlex import quote

files_to_ignore = {'.DS_Store'}  # this is hack for debugging on Mac. On Linux this is not needed
blackrock_file_exts = {'.nev', '.ccf', '.ns6', '.ns2'}
cortex_file_exts = {'.itm', '.cnd', '.par', '.tm'}


def check_folder_format_date(x):
    """this is for my master script"""
    assert len(x) == 8, 'each folder name must be length 8, and {} is not'.format(x)
    for x_digit in x:
        assert x_digit in '0123456789', 'each folder name must contain only digits'
    date_y = x[:4]
    date_m = x[4:6]
    date_d = x[6:]
    # <http://stackoverflow.com/questions/9987818/in-python-how-to-check-if-a-date-is-valid>
    # always return a naive datetime at noon.
    try:
        new_date = datetime.datetime(int(date_y), int(date_m), int(date_d), 12)
    except ValueError as e:
        print('wrong date format {}'.format(x))
        raise e
    return new_date


def check_folder_name_struture(dirpath, data_root):
    # first, check dirpath
    dirpath_old = dirpath
    assert dirpath[:-1] != os.pathsep
    dirpath, session_num_str = os.path.split(dirpath)
    dirpath, date_str = os.path.split(dirpath)
    dirpath, exp_name = os.path.split(dirpath)
    dirpath, monkey_name = os.path.split(dirpath)
    assert data_root == dirpath, '{} should be equal to {} for {}'.format(data_root, dirpath,
                                                                          dirpath_old)
    session_num = int(session_num_str)

    # check monkey_name
    assert monkey_name in monkeylist, '{} is not valid monkey name'.format(monkey_name)
    # check exp name
    assert exp_name.lower() == exp_name, '{} must be lowercase'
    timestamp = check_folder_format_date(date_str)
    assert 1 <= session_num <= 999

    return monkey_name, exp_name, timestamp, session_num, date_str, session_num_str


def check_cortex_files(filenames):
    # check all CORTEX files are there, each exactly one.
    ctx_files_dict = dict()
    ctx_files_actual_dict = dict()
    for f in filenames:
        for ext in cortex_file_exts:
            if f.lower().endswith(ext):
                assert ext not in ctx_files_dict, 'mutiple {} files!'.format(ext)
                assert ext not in ctx_files_actual_dict, 'mutiple {} files!'.format(ext)
                ctx_files_dict[ext] = f.lower()
                ctx_files_actual_dict[ext] = f
    assert ctx_files_dict.keys() == ctx_files_actual_dict.keys() == cortex_file_exts
    return ctx_files_dict, ctx_files_actual_dict


def check_one_case(x, data_root):
    dirpath, dirnames, filenames = x

    (monkey_name, exp_name, timestamp, session_num,
     date_str, session_num_str) = check_folder_name_struture(dirpath, data_root)
    nev_id = timestamp.strftime('%Y_%m_%d') + '_' + '{:03d}'.format(session_num)
    recording_id = timestamp.strftime('%Y%m%d') + '{:03d}'.format(session_num)
    # construct list of blackrock files.
    blackrock_file_base = '_'.join([monkey_name_mapping[monkey_name], nev_id])
    blackrock_files_list = [blackrock_file_base + ext for ext in blackrock_file_exts]

    # check that if anything ends with blackrock_file_exts, then it must be in blackrock_files_list
    for file in filenames:
        if os.path.splitext(file)[1] in blackrock_file_exts:
            assert file in blackrock_files_list, '{} should not exist under {}'.format(file, dirpath)


    # check cortex files are good
    ctx_files_dict, ctx_files_actual_dict = check_cortex_files(filenames)

    # check that notes are good.
    json_file_path = os.path.join(dirpath, 'note.json')
    with open(json_file_path, 'r', encoding='utf-8') as f:
        note = load(f)
    # fields to extract
    fields_to_extract = note.keys() - {'data'}
    note_new = {k: note[k] for k in fields_to_extract}

    assert {'notes', 'RF', 'blocks'} <= note_new.keys()
    # additional parameters are allowed.
    notes_dict = dict()
    notes_dict['notes'] = note_new['notes']
    assert type(notes_dict['notes']) == str
    notes_dict['additional_parameters'] = {k: note_new[k] for k in note_new.keys() - {'notes'}}

    # return everything
    return {
        'monkey': monkey_name,
        'exp_name': exp_name,
        'timestamp': timestamp,
        'blackrock_files_list': blackrock_files_list,
        'suffix_dir': os.path.join(monkey_name, exp_name, date_str, session_num_str),
        'ctx_files_dict': ctx_files_dict,
        'ctx_files_actual_dict': ctx_files_actual_dict,
        'notes_dict': notes_dict,
        'recording_id': recording_id
    }


def check_folder_structure(data_root, record_filter_config=None):
    result_list = []
    for x in os.walk(data_root):
        if set(x[2]) - files_to_ignore:
            result_list.append(check_one_case(x, data_root))
    recording_id_all = {x['recording_id'] for x in result_list}
    assert len(recording_id_all) == len(result_list)
    return result_list


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
        assert check_git_repo_clean(git_repo_path), 'new files are added to git. push it first!'

        # amend my info_for_each_recording with those computed sha1. this is useful later.
        for x in info_for_each_recording:
            if (x['monkey'], x['exp_name']) == monkey_exp_pair:
                assert 'ctx_sha1_dict' not in x
                x['ctx_sha1_dict'] = {
                    ext: cortex_file_dict_this[x['ctx_files_dict'][ext]]['sha1'] for ext in cortex_file_exts
                    }

    # check that git is up to date with origin/master
    assert check_commit_in_remote(git_repo_path, git_repo_hash), 'you must push the commit first'
    for x in info_for_each_recording:
        assert 'ctx_sha1_dict' in x


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
    return cortex_file_dict


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


def collect_missing_blackrock_files_one_case(this_dir, files_that_should_exist, file_dict, blackrock_folder):
    # then let's construct what needs to be there.
    file_to_copy_list = []
    for file_to_find in files_that_should_exist:
        if not os.path.exists(os.path.join(this_dir, file_to_find)):
            file_to_copy_this = os.path.join(blackrock_folder, file_to_find)
            assert os.path.exists(file_to_copy_this), '{} cannot be found'.format(file_to_copy_this)
            file_to_copy_list.append(file_to_copy_this)

    file_dict[this_dir] = file_to_copy_list


def collect_missing_blackrock_files_wrapper(folder_list_dict, blackrock_folder):
    # walk through the tree. whenever there's a note.json in it, fill it.
    blackrock_file_dict = dict()
    for x, files in folder_list_dict.items():
        collect_missing_blackrock_files_one_case(x, files, blackrock_file_dict, blackrock_folder)

    # now, let's construct the list

    cp_lines = []
    rm_lines = []

    file_all = []

    for x, files_to_cp in blackrock_file_dict.items():
        for file in files_to_cp:
            file_all.append(file)
            cp_lines.append('cp {} {}\n'.format(quote(file), quote(x)))
            rm_lines.append('#rm {}\n'.format(quote(file)))
    assert len(set(file_all)) == len(file_all)

    return cp_lines, rm_lines


def check_blackrock_files_all(info_for_each_recording, clean_data_root, messy_data_root, this_script_dir):
    for monkey in {x['monkey'] for x in info_for_each_recording}:
        # collect all folders involving this monkey
        folder_list_dict = {
            os.path.join(clean_data_root, x['suffix_dir']): x['blackrock_files_list'] for x in info_for_each_recording
            if x['monkey'] == monkey
            }

        cp_lines, rm_lines = collect_missing_blackrock_files_wrapper(folder_list_dict,
                                                                     os.path.join(messy_data_root, monkey))
        assert (cp_lines and rm_lines) or (not cp_lines and not rm_lines)
        if (cp_lines and rm_lines):
            with open(os.path.join(this_script_dir, 'blackrock_missing.sh'), 'wt', encoding='utf-8') as f_output:
                f_output.write('#/usr/bin/env bash\n')
                f_output.writelines(cp_lines)
                f_output.write('\n\n\n\n\n\n')
                f_output.writelines(rm_lines)
            raise RuntimeError('some blackrock files missing for monkey {}, '
                               'check blackrock_missing.sh!'.format(monkey))
