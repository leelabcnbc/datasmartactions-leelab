files_to_ignore = {'.DS_Store'}  # this is hack for debugging on Mac. On Linux this is not needed

# don't use set, which has unpredicatable order, and will screw up validation
blackrock_file_exts = ('.nev', '.ns6', '.ns2', '.ccf')
cortex_file_exts_text = {'.itm', '.cnd', '.par', '.tm'}
cortex_file_exts_binary = {'.set', '.lut', '.blk'}
cortex_file_exts = cortex_file_exts_text | cortex_file_exts_binary
cortex_file_exts_r1 = {'.itm', '.cnd', '.par', '.tm', '.set'}
cortex_file_exts_r2 = {'.itm', '.cnd', '.par', '.tm', '.set', '.lut', '.blk'}
assert len(cortex_file_exts) == len(cortex_file_exts_text) + len(cortex_file_exts_binary)
assert cortex_file_exts_r1 <= cortex_file_exts
assert cortex_file_exts_r2 == cortex_file_exts

ctx_mapping_base = {'.tm': 'timing_file',
                    '.cnd': 'condition_file',
                    '.itm': 'item_file',
                    '.par': 'parameter_file',
                    '.set': 'set_file',
                    '.blk': 'blocking_file',
                    '.lut': 'lut_file'
                    }

ctx_name_mapping_dict = {
    x: ctx_mapping_base[x] + '_name' for x in ctx_mapping_base
    }

ctx_sha1_mapping_dict = {
    x: ctx_mapping_base[x] + '_sha1' for x in ctx_mapping_base
    }
