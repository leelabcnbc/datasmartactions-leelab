import datetime

files_to_ignore = {'.DS_Store'}
cortex_file_exts = {'.itm', '.cnd', '.par', '.tm'}
blackrock_file_exts = {'.nev', '.ccf', '.ns6', '.ns2'}
monkey_name_mapping = {
    'Leo': 'LE', 'Gabby': 'GA', 'Frugo': 'FR'
}


def check_folder_format_date(x, return_datetime=False):
    assert len(x) == 8, 'each folder name must be length 8, and {} is not'.format(x)
    for x_digit in x:
        assert x_digit in '0123456789', 'each folder name must contain only digits'
    date_y = x[:4]
    date_m = x[4:6]
    date_d = x[6:]
    try:
        # <http://stackoverflow.com/questions/9987818/in-python-how-to-check-if-a-date-is-valid>
        # always return a naive datetime at noon.
        new_date = datetime.datetime(int(date_y), int(date_m), int(date_d), 12)
        correct_date = True
    except ValueError:
        new_date = None
        correct_date = False

    if not return_datetime:
        return correct_date
    else:
        assert correct_date
        return new_date
