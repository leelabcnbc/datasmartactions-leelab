"""master script for automatically creating actions to fill up cortex_exp"""
from datasmart.actions.leelab.cortex_exp import CortexExpAction

import os.path

from cortex_exp_master_util import (check_folder_structure,
                                    check_cortex_exp_repo_wrapper,
                                    check_blackrock_files_all)


def generate_all_records(clean_data_site_url, clean_data_root,
                         messy_data_root,
                         git_repo_path,
                         git_repo_hash, git_repo_url, this_script_dir,
                         record_filter_config=None):
    # first, check out that folder structure is correct, and get the names of all cortex files.
    # as well as (possibly missing) blackrock files
    # and collect notes
    info_for_each_recording = check_folder_structure(clean_data_root, record_filter_config=record_filter_config)

    # second, check that all cortex files are already stored in git. if not, add them,
    # and then abort the program letting user push first.
    check_cortex_exp_repo_wrapper(info_for_each_recording, clean_data_root, git_repo_path, git_repo_hash)

    # third, check that all blackrock files are there; if not, generate the master cp & rm script,
    # and abort the program letting user push first.
    check_blackrock_files_all(info_for_each_recording, clean_data_root, messy_data_root, this_script_dir)

    # fourth, generate all the cortex_records, with recording_id in it.
    # this should be trivial.
    # all_records = generate_all_records_helper(info_for_each_recording, clean_data_site_url, clean_data_root,
    #                                           git_repo_path, git_repo_hash, git_repo_url)

    print({x['recording_id'] for x in info_for_each_recording})
    print(len(info_for_each_recording))


def main(clean_data_root, messy_data_root):
    clean_data_root = os.path.normpath(clean_data_root)
    messy_data_root = os.path.normpath(messy_data_root)
    assert os.path.isabs(clean_data_root) and os.path.isabs(messy_data_root)
    sample_action = CortexExpAction()
    git_repo_path = sample_action.config['cortex_expt_repo_path']
    git_repo_hash = sample_action.config['cortex_expt_repo_hash']
    git_repo_url = sample_action.config['cortex_expt_repo_url']
    clean_data_site_url = 'sparrowhawk.cnbc.cmu.edu'
    this_script_location = os.path.normpath(os.path.abspath(__file__))
    this_script_dir = os.path.split(this_script_location)[0]
    cortex_exp_action_files = {
        sample_action.prepare_result_name,
        sample_action.query_template_name,
        'cortex-exp-batch.p',
        'cortex-exp-batch.py'
    }

    for x in cortex_exp_action_files:
        assert not os.path.exists(os.path.join(this_script_dir, x)), \
            'probably unfinished action file {} exist under {}; ' \
            'finish the action first and then remove them'.format(x, this_script_dir)

    # generate all records induced from the folder structure.
    # TODO: allow the user to pass in some config file to restrict what to search for, saving time.
    record_filter_config = None
    all_records = generate_all_records(clean_data_site_url, clean_data_root,
                                       messy_data_root,
                                       git_repo_path, git_repo_hash, git_repo_url,
                                       record_filter_config=record_filter_config,
                                       this_script_dir=this_script_dir)

    # if there are some not in the database, pick them out, and write a script to batch insert them,
    # and then quit.

    # otherwise, validate all inserted records are consistent with what we generate.


if __name__ == '__main__':
    messy_data_root_deploy = '/datasmart/leelab/raw_data_messy'
    clean_data_root_deploy = '/datasmart/leelab/raw_data'

    messy_data_root_debug = '/Users/yimengzh/Desktop/datasmart_raw_data'
    clean_data_root_debug = '/Users/yimengzh/Desktop/datasmart_raw_data_messy'

    main(messy_data_root_debug, clean_data_root_debug)
