# switch between AAAABBBB and BBBBAAAA

from sys import argv
import os
import json

from datasmartleelabutil import check_folder_format_date


def convert_new_folder_name(dir_list):
    result_dict = dict()
    for x in dir_list:
        x_new = x[4:] + x[:4]
        result_dict[x] = x_new
        # check that x_new doesn't exist.
        assert x_new not in dir_list, 'name clash!'
    return result_dict


def main(root_folder):
    """switch the order of first 4 and last 4 letters for all 8 letter folders inside root_folder, no recursion.

    Parameters
    ----------
    root_folder

    Returns
    -------

    """
    dir_list = os.listdir(root_folder)
    for x in dir_list:
        assert check_folder_format_date(x)

    # ok, for each one, compute the switched version.
    result_dict = convert_new_folder_name(dir_list)

    print('below is the conversion result, do you want to continue')
    print(json.dumps(result_dict, indent=2))
    res = input('press y then enter to confirm, otherwise exit')
    if res != 'y':
        return
    else:
        # ok, I will change them one by one.
        input('make backup before doing this, in case it will fail in the middle,'
              'press enter to continue, ctrl+c to stop')
        for x, x_new in result_dict.items():
            os.rename(os.path.join(root_folder, x), os.path.join(root_folder, x_new))
        print('done!')


if __name__ == '__main__':
    assert len(argv) == 2, "usage: {} FOLDER".format(argv[0])
    folder = argv[1]
    main(folder)
