from datasmart.actions.leelab.cortex_exp import CortexExpSchemaJSL
from datasmart.core.schemautil import validate
from copy import deepcopy
from collections import OrderedDict
from datasmart.core.util.datetime import datetime_local_to_rfc3339_local, datetime_to_datetime_local
import os.path


# class CortexExpSchemaJSL(jsl.Document):
#     """class defining json schema for a database record. See top of file"""
#     schema_revision = jsl.IntField(enum=[1], required=True)  # the version of schema, in case we have drastic change
#     timestamp = jsl.StringField(format="date-time", required=True)
#     monkey = jsl.StringField(enum=monkeylist, required=True)
#     session_number = jsl.IntField(minimum=1, maximum=999, required=True)
#     code_repo = jsl.DocumentField(schemautil.GitRepoRef, required=True)
#     experiment_name = jsl.StringField(required=True, pattern=schemautil.StringPatterns.relativePathPattern)
#     timing_file_name = jsl.StringField(pattern=schemautil.StringPatterns.strictFilenameLowerPattern('tm'),
#                                        required=True)
#     condition_file_name = jsl.StringField(pattern=schemautil.StringPatterns.strictFilenameLowerPattern('cnd'),
#                                           required=True)
#     item_file_name = jsl.StringField(pattern=schemautil.StringPatterns.strictFilenameLowerPattern('itm'),
#                                      required=True)
#     parameter_file_name = jsl.StringField(pattern=schemautil.StringPatterns.strictFilenameLowerPattern('par'),
#                                           required=True)
#     recorded_files = jsl.DocumentField(schemautil.filetransfer.FileTransferSiteAndFileListRemote, required=True)
#     additional_parameters = jsl.DictField(required=True)
#     notes = jsl.StringField(required=True)
def generate_all_records_helper_basic_info(entry_this, x, git_repo_url, git_repo_hash):
    entry_this['schema_revision'] = 1
    entry_this['timestamp'] = datetime_local_to_rfc3339_local(datetime_to_datetime_local(x['timestamp']))
    entry_this['monkey'] = x['monkey']
    entry_this['session_number'] = x['session_number']
    entry_this['experiment_name'] = x['exp_name']
    entry_this['code_repo'] = {
        "repo_url": git_repo_url,
        "repo_hash": git_repo_hash,
    }


def generate_all_records_helper_blackrock_files(entry_this, x, clean_data_site_url, clean_data_root):
    entry_this['recorded_files'] = {
        "site": {
            "path": clean_data_site_url,
            "local": False,
            "prefix": clean_data_root
        },
        "filelist": [
            os.path.join(x['suffix_dir'], f) for f in x['blackrock_files_list']
            ]
    }


def generate_all_records_helper_cortex_files(entry_this, x):
    entry_this['timing_file_name'] = x['ctx_files_dict']['.tm']
    entry_this['condition_file_name'] = x['ctx_files_dict']['.cnd']
    entry_this['item_file_name'] = x['ctx_files_dict']['.itm']
    entry_this['parameter_file_name'] = x['ctx_files_dict']['.par']


def generate_all_records_helper_notes(entry_this, x):
    entry_this['additional_parameters'] = deepcopy(x['notes_dict']['additional_parameters'])
    entry_this['notes'] = x['notes_dict']['notes']


def generate_all_records_helper(info_for_each_recording, clean_data_site_url, clean_data_root,
                                git_repo_hash, git_repo_url):
    all_records_dict = OrderedDict()

    for x in info_for_each_recording:
        entry_this = dict()
        # generate all basic info
        generate_all_records_helper_basic_info(entry_this, x, git_repo_url, git_repo_hash)
        # generate file entry
        generate_all_records_helper_blackrock_files(entry_this, x, clean_data_site_url, clean_data_root)
        # generate all cortex
        generate_all_records_helper_cortex_files(entry_this, x)
        # generate notes
        generate_all_records_helper_notes(entry_this, x)

        # check that entry_this is good.
        assert validate(CortexExpSchemaJSL.get_schema(), entry_this)
        all_records_dict[x['recording_id']] = entry_this

    return all_records_dict
