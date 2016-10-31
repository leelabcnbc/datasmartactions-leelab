files_to_ignore = {'.DS_Store'}  # this is hack for debugging on Mac. On Linux this is not needed

# don't use set, which has unpredicatable order, and will screw up validation
blackrock_file_exts = ('.nev', '.ns6', '.ns2', '.ccf')
cortex_file_exts = {'.itm', '.cnd', '.par', '.tm'}
