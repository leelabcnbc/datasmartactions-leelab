files_to_ignore = {'.DS_Store'}

def check_folder_format_date(x):
    assert len(x) == 8, 'each folder name must be length 8, and {} is not'.format(x)
    for x_digit in x:
        assert x_digit in '0123456789', 'each folder name must contain only digits'
    return True