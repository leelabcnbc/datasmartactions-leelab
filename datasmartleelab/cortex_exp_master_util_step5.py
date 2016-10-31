import pymongo.collection
from copy import deepcopy
from datasmart.core.util.datetime import rfc3339_to_datetime


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
        sha1_field_list = {'timing_file_sha1': '.tm',
                           'condition_file_sha1': '.cnd',
                           'item_file_sha1': '.itm',
                           'parameter_file_sha1': '.par'}
        for field, ext in sha1_field_list.items():
            ref_doc_to_use[field] = ref_info['ctx_sha1_dict'][ext]

        # remove git and id from original doc
        del saved_doc['code_repo']
        del saved_doc['_id']

        if saved_doc != ref_doc_to_use:
            print(saved_doc, ref_doc_to_use)
