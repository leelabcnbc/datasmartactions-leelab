from datasmartleelab.cortex_exp_master import cortex_exp_master_wrapper

if __name__ == '__main__':
    messy_data_root_deploy = '/datasmart/leelab/raw_data_messy'
    clean_data_root_deploy = '/datasmart/leelab/raw_data'

    messy_data_root_debug = '/Users/yimengzh/Desktop/datasmart_raw_data_messy'
    clean_data_root_debug = '/Users/yimengzh/Desktop/datasmart_raw_data'

    clean_data_site_url = 'sparrowhawk.cnbc.cmu.edu'

    cortex_exp_master_wrapper(clean_data_root_deploy, messy_data_root_deploy, clean_data_site_url)
