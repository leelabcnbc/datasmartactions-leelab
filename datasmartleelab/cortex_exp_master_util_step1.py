import datetime
import os
from itertools import product
from json import load

from datasmart.actions.leelab.cortex_exp import (monkey_name_mapping,
                                                 monkeylist, )
from .cortex_exp_master_util import (cortex_file_exts,
                                     blackrock_file_exts_all, files_to_ignore,
                                     cortex_file_exts_r1, cortex_file_exts_r2,
                                     )


def check_folder_name_struture(dirpath, data_root):
    # first, check dirpath
    dirpath_old = dirpath
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
    for f, ext in product(filenames, cortex_file_exts):
        if f.lower().endswith(ext):
            assert ext not in ctx_files_dict, 'mutiple {} files!'.format(ext)
            ctx_files_dict[ext] = f.lower()
    if ctx_files_dict.keys() == cortex_file_exts_r1:
        return ctx_files_dict, 1
    elif ctx_files_dict.keys() == cortex_file_exts_r2:
        return ctx_files_dict, 2
    else:
        raise ValueError('set of cortex files {} does not matter revision 1 or 2'.format(filenames))


def check_blackrock_files(filenames, dirpath, monkey_name, timestamp, session_num):
    nev_id = timestamp.strftime('%Y_%m_%d') + '_' + '{:03d}'.format(session_num)
    blackrock_files_list = ['_'.join([monkey_name_mapping[monkey_name], nev_id]) + ext for ext in
                            blackrock_file_exts_all]

    # check that if anything ends with blackrock_file_exts, then it must be in blackrock_files_list
    for file in filenames:
        if os.path.splitext(file)[1] in blackrock_file_exts_all:
            assert file in blackrock_files_list, '{} should not exist under {}'.format(file, dirpath)
    return blackrock_files_list


def check_notes(dirpath):
    # check that notes are good.
    json_file_path = os.path.join(dirpath, 'note.json')
    with open(json_file_path, 'r', encoding='utf-8') as f:
        note = load(f)
    note_new = {k: note[k] for k in (note.keys() - {'data'})}

    assert {'notes', 'RF', 'blocks'} <= note_new.keys()
    # additional parameters are allowed.
    notes_dict = dict()
    notes_dict['notes'] = note_new['notes']
    assert type(notes_dict['notes']) == str
    notes_dict['additional_parameters'] = {k: note_new[k] for k in (note_new.keys() - {'notes'})}

    return notes_dict


def check_one_case(x, data_root):
    dirpath, dirnames, filenames = x

    (monkey_name, exp_name, timestamp, session_num,
     date_str, session_num_str) = check_folder_name_struture(dirpath, data_root)

    recording_id = timestamp.strftime('%Y%m%d') + '{:03d}'.format(session_num)
    # construct list of blackrock files.
    blackrock_files_list = check_blackrock_files(filenames, dirpath, monkey_name, timestamp, session_num)
    # check cortex files are good
    ctx_files_dict, schema_revision = check_cortex_files(filenames)

    notes_dict = check_notes(dirpath)

    # return everything
    return {
        'monkey': monkey_name,
        'exp_name': exp_name,
        'timestamp': timestamp,
        'blackrock_files_list': blackrock_files_list,
        'suffix_dir': os.path.join(monkey_name, exp_name, date_str, session_num_str),
        'ctx_files_dict': ctx_files_dict,
        'notes_dict': notes_dict,
        'recording_id': recording_id,
        'session_number': session_num,
        'schema_revision': schema_revision
    }


def check_folder_structure(data_root, record_filter_config=None):
    """main function."""
    result_list = []
    for x in os.walk(data_root):
        if set(x[2]) - files_to_ignore:
            result_list.append(check_one_case(x, data_root))
    # check all recording ids are unique.
    recording_id_all = {x['recording_id'] for x in result_list}
    assert len(recording_id_all) == len(result_list)
    return result_list


def check_folder_format_date(x):
    """check that the string for date can be decoded as a valid naive datetime object"""
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
