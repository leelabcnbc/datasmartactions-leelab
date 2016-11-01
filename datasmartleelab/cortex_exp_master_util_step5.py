import pymongo.collection
from copy import deepcopy
from datasmart.core.util.datetime import rfc3339_to_datetime

from .cortex_exp_master_util import ctx_sha1_mapping_dict

def validate_inserted_records(all_records, info_for_each_recording,
                              collection_instance: pymongo.collection.Collection):
    assert len(all_records) == len(info_for_each_recording)
    for idx, (rec_id, ref_doc) in enumerate(all_records.items()):
        print('checked {}/{}'.format(idx + 1, len(all_records)))
        # first, make sure only one
        assert collection_instance.count({'recording_id': rec_id}) == 1

        # then fetch it
        saved_doc = collection_instance.find_one({'recording_id': rec_id})

        # then compare them
        ref_info = info_for_each_recording[idx]
        ref_doc_to_use = deepcopy(ref_doc)
        ref_doc_to_use['recording_id'] = rec_id
        # swtich the timestamp
        ref_doc_to_use['timestamp'] = rfc3339_to_datetime(ref_doc_to_use['timestamp'])
        # remove git
        del ref_doc_to_use['code_repo']
        # add all sha1

        for ext, sha1_value in ref_info['ctx_sha1_dict'].items():
            ref_doc_to_use[ctx_sha1_mapping_dict[ext]] = sha1_value

        # remove git and id from original doc
        del saved_doc['code_repo']
        del saved_doc['_id']

        if saved_doc != ref_doc_to_use:
            print(saved_doc, ref_doc_to_use)
            raise RuntimeError('uncompatbile docs!')
