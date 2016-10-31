"""master script for automatically creating actions to fill up cortex_exp"""
import os.path
from copy import deepcopy
import pickle
from .cortex_exp_master_util_step1 import check_folder_structure
from .cortex_exp_master_util_step2 import check_cortex_exp_repo_wrapper
from .cortex_exp_master_util_step3 import check_blackrock_files_all
from .cortex_exp_master_util_step4 import generate_all_records_helper
from .cortex_exp_master_util_step5 import validate_inserted_records

from datasmart.actions.leelab.cortex_exp import CortexExpAction


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
    all_records = generate_all_records_helper(info_for_each_recording, clean_data_site_url, clean_data_root,
                                              git_repo_hash, git_repo_url)
    assert len(all_records) == len(info_for_each_recording)

    return all_records, info_for_each_recording


def cortex_exp_master_wrapper(clean_data_root, messy_data_root, clean_data_site_url, this_script_dir):
    clean_data_root = os.path.normpath(clean_data_root)
    messy_data_root = os.path.normpath(messy_data_root)
    assert os.path.isabs(clean_data_root) and os.path.isabs(messy_data_root)
    sample_action = CortexExpAction()
    git_repo_path = sample_action.config['cortex_expt_repo_path']
    git_repo_hash = sample_action.config['cortex_expt_repo_hash']
    git_repo_url = sample_action.config['cortex_expt_repo_url']
    cortex_exp_action_files = {
        sample_action.prepare_result_name,
        sample_action.query_template_name,
        'cortex-exp-batch.p',
    }

    for x in cortex_exp_action_files:
        assert not os.path.exists(os.path.join(this_script_dir, x)), \
            'probably unfinished action file {} exist under {}; ' \
            'finish the action first and then remove them'.format(x, this_script_dir)

    # generate all records induced from the folder structure.
    # TODO: allow the user to pass in some config file to restrict what to search for, saving time.
    record_filter_config = None
    all_records, info_for_each_recording = generate_all_records(clean_data_site_url, clean_data_root,
                                                                messy_data_root,
                                                                git_repo_path, git_repo_hash, git_repo_url,
                                                                record_filter_config=record_filter_config,
                                                                this_script_dir=this_script_dir)

    # if there are some not in the database, pick them out, and write a script to batch insert them,
    # and then quit.
    recording_id_to_insert = []
    with sample_action.db_context as db_instance:
        collection_instance = db_instance.client_instance[sample_action.table_path[0]][sample_action.table_path[1]]
        for recording_id, record in all_records.items():
            if collection_instance.count({'recording_id': recording_id}) == 0:
                recording_id_to_insert.append(recording_id)

    if recording_id_to_insert:
        print('{} records to be inserted out of {}'.format(len(recording_id_to_insert), len(all_records)))
        # save all records in recording_id_to_insert to 'cortex-exp-batch.p'
        recordings_to_insert = [deepcopy(all_records[rec_id]) for rec_id in recording_id_to_insert]
        with open(os.path.join(this_script_dir, 'cortex-exp-batch.p'), 'wb') as f_batch_record:
            pickle.dump(recordings_to_insert, f_batch_record)
        print('execute the datasmart action, and in the end remove cortex-exp-batch.p and other action-related files')
    else:
        # otherwise, validate all inserted records are consistent with what we generate.
        with sample_action.db_context as db_instance:
            collection_instance = db_instance.client_instance[sample_action.table_path[0]][sample_action.table_path[1]]
            validate_inserted_records(all_records, info_for_each_recording, collection_instance)
