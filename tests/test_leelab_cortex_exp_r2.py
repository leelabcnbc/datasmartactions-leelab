import getpass
import hashlib
import json
import os
import random
import unittest
from functools import partial
from subprocess import CalledProcessError

import pytz

from jsonschema.exceptions import ValidationError
from datetime import datetime
import datasmart.core.util.datetime
import datasmart.core.util.git
from datasmart.actions.leelab.cortex_exp import CortexExpAction, CortexExpSchemaJSL, monkeylist
from datasmart.core import schemautil
from datasmart.test_util import env_util
from datasmart.test_util import mock_util, file_util
import datasmart.test_util


class LeelabCortexExpAction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # reset seed
        datasmart.test_util.reseed(0)
        # check git is clean
        datasmart.core.util.git.check_git_repo_clean()
        env_util.setup_db(cls, [CortexExpAction.table_path])

    def setUp(self):
        # check git is clean
        datasmart.core.util.git.check_git_repo_clean()
        # I put setup here only to pass in reference to class for mock function.
        self.mock_function = partial(LeelabCortexExpAction.input_mock_function, instance=self)
        self.config_path = CortexExpAction.config_path

    def get_correct_result(self):
        # create the correct result.
        correct_result = dict()
        correct_result['schema_revision'] = 2
        correct_result['code_repo'] = dict()
        correct_result['code_repo']['repo_url'] = self.git_mock_info['git_url']
        correct_result['code_repo']['repo_hash'] = self.git_mock_info['git_hash']
        correct_result['monkey'] = random.choice(monkeylist)
        correct_result['experiment_name'] = self.temp_dict['experiment_name']
        correct_result['timing_file_name'] = self.temp_dict['timing_file_name']
        correct_result['condition_file_name'] = self.temp_dict['condition_file_name']
        correct_result['parameter_file_name'] = self.temp_dict['parameter_file_name']
        correct_result['item_file_name'] = self.temp_dict['item_file_name']

        correct_result['lut_file_name'] = self.temp_dict['lut_file_name']
        correct_result['set_file_name'] = self.temp_dict['set_file_name']
        correct_result['blocking_file_name'] = self.temp_dict['blocking_file_name']

        correct_result['recorded_files'] = dict()
        correct_result['recorded_files']['site'] = self.site
        correct_result['recorded_files']['filelist'] = self.filelist_true
        correct_result['additional_parameters'] = file_util.fake.pydict(5, True, 'int', 'float', 'str')
        correct_result['notes'] = " ".join(file_util.fake.sentences())

        correct_result['timing_file_sha1'] = self.temp_dict['timing_file_sha1']
        correct_result['condition_file_sha1'] = self.temp_dict['condition_file_sha1']
        correct_result['item_file_sha1'] = self.temp_dict['item_file_sha1']
        correct_result['parameter_file_sha1'] = self.temp_dict['parameter_file_sha1']

        correct_result['set_file_sha1'] = self.temp_dict['set_file_sha1']
        correct_result['lut_file_sha1'] = self.temp_dict['lut_file_sha1']
        correct_result['blocking_file_sha1'] = self.temp_dict['blocking_file_sha1']

        correct_result['session_number'] = self.temp_dict['session_number']

        # let's directly create timestamp
        local_datetime = file_util.fake.date_time_between_dates(datetime_start=datetime(2000, 1, 1),
                                                                datetime_end=datetime(2020, 1, 1))
        # some of these hours can give different days for UTC and local time, without trouble of DST.
        local_datetime = local_datetime.replace(hour=random.choice([10, 20, 22, 23]))
        correct_result['recording_id'] = local_datetime.strftime('%Y%m%d') + '{:03d}'.format(
            correct_result['session_number'])
        # convert to UTC
        local_datetime_withtz = datasmart.core.util.datetime.datetime_to_datetime_local(local_datetime)
        local_datetime_rfc = datasmart.core.util.datetime.datetime_local_to_rfc3339_local(local_datetime_withtz)
        local_datetime_utc_naive = local_datetime_withtz.astimezone(pytz.utc).replace(tzinfo=None)
        correct_result['timestamp'] = local_datetime_utc_naive
        correct_result['timestamp_rfc'] = local_datetime_rfc

        self.temp_dict['correct_result'] = correct_result

    def setup_cortex_exp_files(self):
        # creating item file, condition file, timing file, and their sha.
        self.temp_dict['experiment_name'] = "/".join(file_util.gen_filenames(random.randint(1, 2)))
        self.temp_dict['timing_file_name'] = file_util.gen_filename_strict_lower() + '.tm'
        self.temp_dict['condition_file_name'] = file_util.gen_filename_strict_lower() + '.cnd'
        self.temp_dict['item_file_name'] = file_util.gen_filename_strict_lower() + '.itm'
        self.temp_dict['parameter_file_name'] = file_util.gen_filename_strict_lower() + '.par'

        self.temp_dict['set_file_name'] = file_util.gen_filename_strict_lower() + '.set'
        self.temp_dict['lut_file_name'] = file_util.gen_filename_strict_lower() + '.lut'
        self.temp_dict['blocking_file_name'] = file_util.gen_filename_strict_lower() + '.blk'

        filelist_full = [os.path.join(self.git_mock_info['git_repo_path'], self.temp_dict['experiment_name'], x) for x
                         in [self.temp_dict['timing_file_name'],
                             self.temp_dict['condition_file_name'],
                             self.temp_dict['item_file_name'],
                             self.temp_dict['parameter_file_name'],
                             self.temp_dict['set_file_name'],
                             self.temp_dict['lut_file_name'],
                             self.temp_dict['blocking_file_name'],
                             ]
                         ]
        file_util.create_files_from_filelist(filelist_full, local_data_dir='.')
        with open(filelist_full[0], 'rb') as f:
            self.temp_dict['timing_file_sha1'] = hashlib.sha1(f.read()).hexdigest()
        with open(filelist_full[1], 'rb') as f:
            self.temp_dict['condition_file_sha1'] = hashlib.sha1(f.read()).hexdigest()
        with open(filelist_full[2], 'rb') as f:
            self.temp_dict['item_file_sha1'] = hashlib.sha1(f.read()).hexdigest()
        with open(filelist_full[3], 'rb') as f:
            self.temp_dict['parameter_file_sha1'] = hashlib.sha1(f.read()).hexdigest()

        with open(filelist_full[4], 'rb') as f:
            self.temp_dict['set_file_sha1'] = hashlib.sha1(f.read()).hexdigest()
        with open(filelist_full[5], 'rb') as f:
            self.temp_dict['lut_file_sha1'] = hashlib.sha1(f.read()).hexdigest()
        with open(filelist_full[6], 'rb') as f:
            self.temp_dict['blocking_file_sha1'] = hashlib.sha1(f.read()).hexdigest()

        file_util.create_files_from_filelist(self.filelist_true, local_data_dir=self.site['prefix'])

        # let's add some session number
        self.temp_dict['session_number'] = random.randint(1, 999)

    def get_new_instance(self):
        # check git is clean
        datasmart.core.util.git.check_git_repo_clean()

        filetransfer_config_text = """{{
            "local_data_dir": "_data",
            "site_mapping_push": [
            ],
            "site_mapping_fetch": [
            ],
            "remote_site_config": {{
              "localhost": {{
                "ssh_username": "{}",
                "ssh_port": 22
              }}
            }},
            "default_site": {{
              "path": "default_local_site",
              "local": true
            }},
            "quiet": false,
            "local_fetch_option": "copy"
          }}""".format(getpass.getuser())

        env_util.setup_local_config(('core', 'filetransfer'), filetransfer_config_text)

        self.dirs_to_cleanup = file_util.gen_unique_local_paths(1)  # for git
        file_util.create_dirs_from_dir_list(self.dirs_to_cleanup)
        self.git_mock_info = mock_util.setup_git_mock(git_repo_path=self.dirs_to_cleanup[0])
        self.savepath = file_util.gen_unique_local_paths(1)[0]
        self.temp_dict = {}
        self.site = env_util.setup_remote_site()
        filelist = file_util.gen_filelist(100, abs_path=False)
        self.filelist_true = filelist[:50]
        self.filelist_false = filelist[50:]
        self.action = mock_util.create_mocked_action(CortexExpAction,
                                                     {'cortex_expt_repo_path': self.git_mock_info['git_repo_path'],
                                                      'savepath': self.savepath},
                                                     {'git': self.git_mock_info})
        self.class_identifier = self.action.class_identifier
        self.files_to_cleanup = [self.savepath, self.action.prepare_result_name, self.action.query_template_name]

        for file in self.files_to_cleanup:
            self.assertFalse(os.path.exists(file))
        self.setup_cortex_exp_files()
        self.get_correct_result()

    def remove_instance(self):
        file_util.rm_files_from_file_list(self.files_to_cleanup)
        file_util.rm_dirs_from_dir_list(self.dirs_to_cleanup)
        env_util.teardown_remote_site(self.site)
        for file in self.files_to_cleanup:
            self.assertFalse(os.path.exists(file))

        env_util.teardown_local_config()
        # check git is clean
        datasmart.core.util.git.check_git_repo_clean()

    def tearDown(self):
        # drop and then reset
        env_util.reset_db(self.__class__, CortexExpAction.table_path)
        # check git is clean
        datasmart.core.util.git.check_git_repo_clean()

    @classmethod
    def tearDownClass(cls):
        env_util.teardown_db(cls)
        # check git is clean
        datasmart.core.util.git.check_git_repo_clean()

    def test_insert_wrong_stuff(self):
        wrong_types = ['missing field', 'wrong monkey',
                       'nonexistent tm', 'nonexistent itm', 'nonexistent cnd',
                       'nonexistent par', 'nonexistent set', 'nonexistent lut', 'nonexistent blk',
                       'nonexistent recording files']
        exception_types = [ValidationError, ValidationError,
                           AssertionError, AssertionError, AssertionError,
                           AssertionError, AssertionError, AssertionError,
                           AssertionError, CalledProcessError]
        exception_msgs = [None, None,
                          ".tm doesn't exist!", ".itm doesn't exist!", ".cnd doesn't exist!", ".par doesn't exist!",
                          ".set doesn't exist!", ".lut doesn't exist!", ".blk doesn't exist!",
                          None]

        for wrong_type, exception_type, exception_msg in zip(wrong_types, exception_types, exception_msgs):
            for _ in range(5):  # used to be 20. but somehow that will make program fail for travis
                self.get_new_instance()
                self.temp_dict['wrong_type'] = wrong_type
                with self.assertRaises(exception_type) as exp_instance:
                    mock_util.run_mocked_action(self.action, {'input': self.mock_function,
                                                              'git': self.git_mock_info})
                if exception_msg is not None:
                    self.assertNotEqual(exp_instance.exception.args[0].find(exception_msg), -1)
                self.remove_instance()

    def test_insert_correct_stuff(self):
        for _ in range(10):  # used to be 100. but somehow that will make program fail for travis
            self.get_new_instance()
            self.temp_dict['wrong_type'] = 'correct'
            mock_util.run_mocked_action(self.action, {'input': self.mock_function,
                                                      'git': self.git_mock_info})
            self.assertEqual(len(self.action.result_ids), 1)
            result_id = self.action.result_ids[0]
            result = env_util.assert_found_and_return(self.__class__, [result_id])[0]
            del result['_id']
            correct_result = self.temp_dict['correct_result']
            # for key in correct_result: # this for loop for of assert is easy to debug.
            #     self.assertEqual(correct_result[key], result[key])
            timestamp_rfc = correct_result['timestamp_rfc']
            del correct_result['timestamp_rfc']
            self.assertEqual(correct_result, result)
            result['timestamp'] = datasmart.core.util.datetime.datetime_to_datetime_utc(result['timestamp'])
            result['timestamp'] = datasmart.core.util.datetime.datetime_local_to_local(result['timestamp'])
            result['timestamp'] = datasmart.core.util.datetime.datetime_local_to_rfc3339_local(result['timestamp'])
            print(timestamp_rfc, result['timestamp'],
                  correct_result['timestamp'], correct_result['recording_id'])
            del result['timing_file_sha1']
            del result['item_file_sha1']
            del result['condition_file_sha1']
            del result['parameter_file_sha1']
            del result['recording_id']

            del result['set_file_sha1']
            del result['lut_file_sha1']
            del result['blocking_file_sha1']

            self.assertTrue(schemautil.validate(CortexExpSchemaJSL.get_schema(), result))
            self.action.revoke()
            env_util.assert_not_found(self.__class__, [result_id])
            self.remove_instance()

    @staticmethod
    def input_mock_function(prompt: str, instance) -> str:
        if prompt.startswith("{} Step 0a".format(instance.class_identifier)):
            pass
        elif prompt.startswith("{} Step 1".format(instance.class_identifier)):
            with open(instance.action.config['savepath'], 'rt') as f_old:
                record = json.load(f_old)

            # first, fill in the correct stuff.
            record['schema_revision'] = instance.temp_dict['correct_result']['schema_revision']

            record['experiment_name'] = instance.temp_dict['correct_result']['experiment_name']
            record['timing_file_name'] = instance.temp_dict['correct_result']['timing_file_name']
            record['condition_file_name'] = instance.temp_dict['correct_result']['condition_file_name']
            record['item_file_name'] = instance.temp_dict['correct_result']['item_file_name']
            record['parameter_file_name'] = instance.temp_dict['correct_result']['parameter_file_name']

            record['set_file_name'] = instance.temp_dict['correct_result']['set_file_name']
            record['lut_file_name'] = instance.temp_dict['correct_result']['lut_file_name']
            record['blocking_file_name'] = instance.temp_dict['correct_result']['blocking_file_name']

            record['recorded_files'] = instance.temp_dict['correct_result']['recorded_files']
            record['additional_parameters'] = instance.temp_dict['correct_result']['additional_parameters']
            record['notes'] = instance.temp_dict['correct_result']['notes']
            record['monkey'] = instance.temp_dict['correct_result']['monkey']
            record['timestamp'] = instance.temp_dict['correct_result']['timestamp_rfc']
            record['session_number'] = instance.temp_dict['correct_result']['session_number']

            wrong_type = instance.temp_dict['wrong_type']
            if wrong_type == 'correct':
                pass
            elif wrong_type == 'missing field':
                # randomly remove one key
                del record[random.choice(list(record.keys()))]
            elif wrong_type == 'wrong monkey':
                record['monkey'] = random.choice(
                    ['Koko', 'Frugo', 'Leo', 'demo', 'koKo', 'lEo', 'gaBBy', None, 123123, 2.4])
            elif wrong_type == 'nonexistent tm':
                record['timing_file_name'] = file_util.gen_filename_strict_lower(
                    os.path.splitext(record['timing_file_name'])[0]) + '.tm'
            elif wrong_type == 'nonexistent cnd':
                record['condition_file_name'] = file_util.gen_filename_strict_lower(
                    os.path.splitext(record['condition_file_name'])[0]) + '.cnd'
            elif wrong_type == 'nonexistent itm':
                record['item_file_name'] = file_util.gen_filename_strict_lower(
                    os.path.splitext(record['item_file_name'])[0]) + '.itm'
            elif wrong_type == 'nonexistent par':
                record['parameter_file_name'] = file_util.gen_filename_strict_lower(
                    os.path.splitext(record['parameter_file_name'])[0]) + '.par'
            elif wrong_type == 'nonexistent set':
                record['set_file_name'] = file_util.gen_filename_strict_lower(
                    os.path.splitext(record['set_file_name'])[0]) + '.set'
            elif wrong_type == 'nonexistent lut':
                record['lut_file_name'] = file_util.gen_filename_strict_lower(
                    os.path.splitext(record['lut_file_name'])[0]) + '.lut'
            elif wrong_type == 'nonexistent blk':
                record['blocking_file_name'] = file_util.gen_filename_strict_lower(
                    os.path.splitext(record['blocking_file_name'])[0]) + '.blk'
            elif wrong_type == 'nonexistent recording files':
                record['recorded_files']['filelist'] = instance.filelist_false
            else:
                raise ValueError("impossible error type!")

            with open(instance.action.config['savepath'], 'wt') as f_new:
                json.dump(record, f_new)
        else:
            raise ValueError("impossible!")


if __name__ == '__main__':
    unittest.main()
