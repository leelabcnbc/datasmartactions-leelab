"""check that the raw data folder structures are correct"""

from sys import argv
import os
from json import load
from datasmartleelabutil.cortex_exp import (files_to_ignore, cortex_file_exts,
                                            blackrock_file_exts, monkey_name_mapping,
                                            check_folder_format_date)


def check_one_case(x, data_root):
    dirpath, dirnames, filenames = x
    dirpath_old = dirpath
    # first, check dirpath
    assert dirpath[:-1] != os.pathsep
    dirpath, session_num_str = os.path.split(dirpath)
    dirpath, date = os.path.split(dirpath)
    dirpath, exp_name = os.path.split(dirpath)
    dirpath, monkey_name = os.path.split(dirpath)
    assert data_root == dirpath
    session_num = int(session_num_str)

    # check monkey_name
    assert monkey_name in monkey_name_mapping.keys(), '{} is not valid monkey name'.format(monkey_name)
    assert exp_name.lower() == exp_name, '{} must be lowercase'
    timestamp = check_folder_format_date(date, return_datetime=True)
    assert 1 <= session_num <= 999

    # check NEV etc files are there.
    nev_file_base = '_'.join(
        [monkey_name_mapping[monkey_name], timestamp.strftime('%Y_%m_%d'), '{:03d}'.format(session_num)])
    blackrock_files_list = [nev_file_base + ext for ext in blackrock_file_exts]
    for f in blackrock_files_list:
        assert os.path.exists(os.path.join(dirpath_old, f))

    # check all CORTEX files are there, each exactly one.
    ctx_files_dict = dict()
    for f in filenames:
        for ext in cortex_file_exts:
            if f.lower().endswith(ext):
                assert ext not in ctx_files_dict, 'mutiple {} files!'.format(ext)
                ctx_files_dict[ext] = f.lower()
    assert ctx_files_dict.keys() == cortex_file_exts

    # check that notes are good.
    json_file_path = os.path.join(dirpath_old, 'note.json')
    assert os.path.exists(json_file_path), 'note.json must exist under {}'.format(dirpath_old)
    with open(json_file_path, 'r', encoding='utf-8') as f:
        note = load(f)
    # fields to extract
    fields_to_extract = note.keys() - {'data'}
    note_new = {k: note[k] for k in fields_to_extract}

    assert {'notes', 'RF', 'blocks'} <= note_new.keys()
    # additional parameters are allowed.
    notes_dict = dict()
    notes_dict['notes'] = note_new['notes']
    notes_dict['additional_parameters'] = {k: note_new[k] for k in note_new.keys() - {'notes'}}

    # return everything
    return {
        'monkey': monkey_name,
        'exp_name': exp_name,
        'timestamp': timestamp,
        'blackrock_files_list': blackrock_files_list,
        'suffix_dir': os.path.join(monkey_name, exp_name, date, session_num_str),
        'ctx_files_dict': ctx_files_dict,
        'notes_dict': notes_dict,
    }


def main(data_root):
    data_root = os.path.normpath(data_root)
    result_list = []
    for x in os.walk(data_root):
        if set(x[2]) - files_to_ignore:
            result_list.append(check_one_case(x, data_root))
    print(result_list)

    # ok, based on this, I should be able to create record


if __name__ == '__main__':
    # TODO: able to set minimum date to start working on.
    assert len(argv) == 2, 'usage: {} DATA_ROOT_DIR'.format(argv[0])
    main(argv[1])
