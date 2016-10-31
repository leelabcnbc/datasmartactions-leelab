from datasmartleelab.cortex_exp_master import cortex_exp_master_wrapper
import os.path

if __name__ == '__main__':
    messy_data_root_deploy = '/datasmart/leelab/raw_data_messy'
    clean_data_root_deploy = '/datasmart/leelab/raw_data'

    messy_data_root_debug = '/Users/yimengzh/Desktop/datasmart_raw_data_messy'
    clean_data_root_debug = '/Users/yimengzh/Desktop/datasmart_raw_data'

    clean_data_site_url = 'sparrowhawk.cnbc.cmu.edu'

    this_script_location = os.path.normpath(os.path.abspath(__file__))
    this_script_dir = os.path.split(this_script_location)[0]

    cortex_exp_master_wrapper(clean_data_root_deploy, messy_data_root_deploy, clean_data_site_url,
                              this_script_dir)
