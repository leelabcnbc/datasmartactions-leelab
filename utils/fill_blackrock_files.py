"""copy all necessary blackrock files into folders, according to 'note.json' """

from sys import argv
from json import load
import os
from shlex import quote

from datasmartleelabutil.cortex_exp import files_to_ignore, cortex_file_exts, blackrock_file_exts


def collect_missing_files_one_case(this_dir, file_dict, blackrock_folder):
    json_file_path = os.path.join(this_dir, 'note.json')
    assert os.path.exists(json_file_path), 'note.json must exist under {}'.format(this_dir)
    with open(json_file_path, 'r', encoding='utf-8') as f:
        note = load(f)
    file_prefix_to_grab = os.path.splitext(note['data'])[0].upper()

    # then let's construct what needs to be there.
    files_that_should_exist = [file_prefix_to_grab + ext for ext in blackrock_file_exts]
    file_to_copy_list = []
    for file_to_find in files_that_should_exist:
        if not os.path.exists(os.path.join(this_dir, file_to_find)):
            file_to_copy_this = os.path.join(blackrock_folder, file_to_find)
            assert os.path.exists(file_to_copy_this), '{} cannot be found'.format(file_to_copy_this)
            file_to_copy_list.append(file_to_copy_this)

    file_dict[this_dir] = file_to_copy_list


def main(data_root, blackrock_folder, output):
    # walk through the tree. whenever there's a note.json in it, fill it.
    blackrock_file_dict = dict()
    for x in os.walk(data_root):
        if set(x[2]) - files_to_ignore:
            collect_missing_files_one_case(x[0], blackrock_file_dict, blackrock_folder)

    # now, let's construct the list

    cp_lines = []
    rm_lines = []
    for x, files_to_cp in blackrock_file_dict.items():
        for file in files_to_cp:
            cp_lines.append('cp {} {}\n'.format(quote(file), quote(x)))
            rm_lines.append('#rm {}\n'.format(quote(file)))

    assert not os.path.exists(output), 'must be a new file!'
    with open(output, 'wt', encoding='utf-8') as f_output:
        f_output.write('#/usr/bin/env bash\n')
        f_output.writelines(cp_lines)
        f_output.write('\n\n\n\n\n\n')
        f_output.writelines(rm_lines)


if __name__ == '__main__':
    assert len(argv) == 4, "usage: {} DATA_ROOT, BLACKROCK_FILE_FOLDER, OUTPUT"
    main(*argv[1:])
