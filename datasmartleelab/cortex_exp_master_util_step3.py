import os
from shlex import quote
from .cortex_exp_master_util import blackrock_file_exts_required


def collect_missing_blackrock_files_one_case(this_dir, files_that_should_exist, file_dict, blackrock_folder):
    # then let's construct what needs to be there.
    file_to_copy_list = []
    idx_to_remove_list = []
    for file_idx, file_to_find in enumerate(files_that_should_exist):
        if os.path.splitext(file_to_find)[1] in blackrock_file_exts_required:
            if not os.path.exists(os.path.join(this_dir, file_to_find)):
                file_to_copy_this = os.path.join(blackrock_folder, file_to_find)
                assert os.path.exists(file_to_copy_this), '{} cannot be found'.format(file_to_copy_this)
                file_to_copy_list.append(file_to_copy_this)
        else:
            idx_to_remove_list.append(file_idx)

    # then remove those items from files_that_should_exist
    # from <http://stackoverflow.com/questions/497426/deleting-multiple-elements-from-a-list>
    for i in sorted(idx_to_remove_list, reverse=True):
        print(files_that_should_exist[i])
        del files_that_should_exist[i]

    file_dict[this_dir] = file_to_copy_list


def collect_missing_blackrock_files_checkresult(cp_lines, rm_lines, file_all):
    assert len(set(file_all)) == len(file_all)
    assert (cp_lines and rm_lines) or (not cp_lines and not rm_lines)


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
            cp_lines.append('echo {}\n'.format(quote(file)))
            rm_lines.append('#rm {}\n'.format(quote(file)))
            rm_lines.append('#echo {}\n'.format(quote(file)))
    collect_missing_blackrock_files_checkresult(cp_lines, rm_lines, file_all)

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

        if (cp_lines and rm_lines):
            with open(os.path.join(this_script_dir, 'blackrock_missing.sh'), 'wt', encoding='utf-8') as f_output:
                f_output.write('#/usr/bin/env bash\n')
                f_output.writelines(cp_lines)
                f_output.write('\n\n\n\n\n\n')
                f_output.writelines(rm_lines)
            raise RuntimeError('some blackrock files missing for monkey {}, '
                               'check blackrock_missing.sh!'.format(monkey))
