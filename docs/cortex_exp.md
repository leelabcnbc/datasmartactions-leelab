# `cortex_exp` DataSMART action

Oct. 31, 2016  
Yimeng Zhang

This document should help one upload captured data into datasmart.  

#This documents illustrates how to efficiently use `cortex_exp` action.

The files for each individual experiment should be in the folder /datasmart/leelab/cortex_exp/monkeyname/whateverthenameofexperiment/yyyymmdd/nn
where "monkeyname" is the name of your monkey and "whateverthenameofexperiment" is a name WITH NO SPACES of a name of your experiment.    

1. Check **Data file hierarchy** for how to put new data files on sparrowhawk.
2. Check **How to import new data** on how to use the master script.
3. In addition, check **How to import legacy data** if you are to import Summer's legacy data for leo, before running the master script.

## Setup

For Lee Lab users, simply log into `leelab@sparrowhawk.cnbc.cmu.edu`, and I have already setup all things. Basically I have done

0. Fetch three git repos, under home directory.
	1. <https://github.com/leelabcnbc/datasmart>
	2. <https://github.com/leelabcnbc/datasmartactions-leelab>
	3. <https://github.com/leelabcnbc/cortex-exp>
1. Install miniconda, with `tmux` and `git` in the default environment,
2. Installed an environment called `datasmart`, via <https://github.com/leelabcnbc/datasmart/blob/master/install_python_env.sh>.
3. After `source activate datasmart`, and change directory to `~/datasmart`, run
	1. `./install_config_core.py` to install all default configs. (I guess this can be skipped, since later I override all these; but whatever).
	2. `PYTHONPATH=~/datasmartactions-leelab ./install_action.py ~/datasmart-cortex-exp leelab/cortex_exp` This will install action `leelab/cortex_exp` under `~/datasmart-cortex-exp`.
4. modify some configuration files.
	1. for `~/datasmart-cortex-exp/config/core/db/config.json`, fill in the correct username and password. I also set its permission to `600` in case other people see it.
	2. for `~/datasmart-cortex-exp/config/core/filetransfer/config.json`, it's already tailored to `sparrowhawk.cnbc.cmu.edu`.
	3. for `~/datasmart-cortex-exp/config/core/util/config.json`, the timezone is set to `US/Eastern` already, which is appropriate for CMU.
	4. for `~/datasmart-cortex-exp/actions/leelab/cortex_exp/config.json`, change `cortex_expt_repo_path` to `/home/leelab/cortex-exp`. Previously it's set to a folder on my laptop, for debugging purpose.

## Data file hierarchy

On `sparrowhawk`, all raw datas are stored under `/datasmart/leelab/raw_data/cortex_exp`, which I denote as `$ROOT` later. For each recording of monkey `banana` for a particular project `myproject` at a particular day `YYYYMMDD`, at `X`th session. We put all its data files under `$ROOT/banana/myproject/YYYYMMDD/X`. Call this `$RECORDING_ROOT`.

The monkey name must be among keys of `monkey_name_mapping` in <https://github.com/leelabcnbc/datasmartactions-leelab/blob/master/datasmart/actions/leelab/cortex_exp.py>, and project name must be of lowercase. (TODO: in <https://github.com/leelabcnbc/datasmartactions-leelab/blob/master/datasmart/actions/leelab/cortex_exp.py>, actually `experiment_name` is not required to be lowercase, and this is only enforced by my master script; but I think such lowercase requirement is easier for me to write the master script; and we may also require it in the actual schema as well).

under each `$RECORDING_ROOT`, put the following files.

* CORTEX related files. it must be one of the following. Letter case in filenames is ignored.
	1. `.par`, `.cnd`, `.tm`, `.itm`, `.set` files (old one)
	2. `.par`, `.cnd`, `.tm`, `.itm`, `.set`, `.lut`, `.blk` files (new one, preferred)
	3. If you have difficuly achieving this, say you have 6 files, with `.blk` missing. The preferable way would be creating an empty file (using `touch` in Linux) called `dummy.blk`. `dummy` explicitly tells the purpose of this file.
* a JSON file called `note.json` that stores a dictionary (object in JSON terminolgy), including at least `notes`, `RF`, and `blocks`. Additional parmameters are accepted as well, except `data`, which has been taken by Summer to keep track of what files are used.
	* Another reserved field might be `revision`, which can be useful to distinguish between different versions of CORTEX schema (hopefully, there won't be many).
* set of `nev`, `ns2`, `ns6`, `ccf` files. Their names must be of form `MA_YYYY_MM_DD_00X`, where `MA` is the two letter abbreviation for the given monkey, and `00X` means `{:03d}.format(X)` (in Python syntax). Other files, such as `.ns3` are allowed but ignored by the current master script.

To be super exact, I allow exactly one file with of each extensions above in `$RECORDING_ROOT`. So you cannot have multiple `.set` files

## How to import new data

After uploading new data files to `/datasmart/leelab/raw_data/cortex_exp` according to the data file hierarchy above, you should do the following to put it in the database.

1. First, open two terminal windows, both ssh to `leelab@sparrowhawk.cnbc.cmu.edu`. One change directory to `~/cortex-exp` (window 1), one to `~/datasmart-cortex-exp` (window 0).
2. In window 1, run `./start_cortex_exp_master_script.sh`.
3. There are several possibilities for running this script. Please contribute more detailed descriptions!
	1. You just uploaded some data for a brand new experiment `XXX`, and the script complains `please create XXX folder`. This is because the `cortex-exp` git repo for tracking CORTEX files don't have the corresponding folder `XXX` to hold CORTEX files for experiment `XXX`. Just create it and rerun.
	2. (Potentially after creating the folder) you may see that the script says your repo is not clean. This is because it automatically copies those new CORTEX files to the project folder in `cortex-exp`, and they are not committed. Switch to window 1 and commit & push them.
	3. You may forget to push those new `cortex-exp` files, and the script will ask you to push them first.
	4. For legacy data, it may complain that you need to run some file called `blackrock_missing.sh` under `~/datasmart-cortex-exp`. This file basically copies the missing blackrock files from `/datasmart/leelab/raw_data_messy/cortex_exp`, and optionally you can remove those copied files (commentted out in the file). Run it by `./blackrock_missing.sh` after `chmod +x` or `bash blackrock_missing.sh` should do as well.
	5. In the end, the `./start_cortex_exp_master_script.sh` can finally exit normally, reporting how many records are missing in the base, and telling you to run the action. In this case, it will create a file called `cortex-exp-batch.p` under `~/datasmart-cortex-exp`. This file contains all the new entries that should be entered into database.
	6. Run `./start_leelab_cortex_exp.sh`. Follow its instruction, and it will insert all those entries. I think it should run without any error. If there's any, rerun and revoke it (by pressing any key then pressing enter), and tell me immediately!
	7. Now the new data entries should be available in the database. Check <https://github.com/leelabcnbc/datasmartactions-leelab/blob/master/datasmart/config/actions/leelab/cortex_exp/config_db.json> and you should be able to figure out how to view the database using <http://3t.io/mongochef/>.
	8. In the end, you should remove `actions.leelab.cortex_exp.prepare_result.p`, `actions.leelab.cortex_exp.query_template.py`, and `cortex-exp-batch.p`. These files are used to prevent records from being inserted multiple times (without removing these files, running `./start_leelab_cortex_exp.sh` twice won't be harmful. Don't remove only one of them, or two of them, as that may lead to unpredictable results. Just remove all of them, or none of them.
4. If you run the master script again, it will verify that all previously inserted records can be generated by the current program as well. This is helpful when updating the datasmart actions.
5. During execution of master script, you may see warnings like "`leo/prediction/20160304/1/PRED.CND` does not have CRLF ending; may not be an issue in practice". This is because in theory those (text) CORTEX files should have CRLF line ending, but the particular file the warning is referring to is not. This may not be a problem in practice, as these files can run successfully. Or it's just some error in copying, or some automatic line ending detection and conversion of some FTP client.

## How to import legacy data

For Summer's old data to be imported into data base, you should

1. Download <https://github.com/leelabcnbc/datasmartactions-leelab/blob/master/datasmartleelab/switch_date_format.py> and use it to convert all `MMDDYYYY` to `YYYYMMDD` in each project folder (which contains all folders with name `MMDDYYYY`. The script should be executed with Python 3.5, and lower version is not tested. For example, `leo/aaa` folder contains many folders of format `MMDDYYYY`, then just run `python switch_date_format.py leo/aaa` should do. (I assume your current directory contains `switch_date_format.py`.
2. Upload the data with correct date format to `sparrowhawk.cnbc.cmu.edu:/datasmart/leelab/raw_data_no_file_original_from_summer_and_name_fixed/cortex_exp`, just for backup.
3. Upload the same set of data to `sparrowhawk.cnbc.cmu.edu:/datasmart/leelab/raw_data/cortex_exp`
4. Put all the blackrock files possibly missing under these folders to  `sparrowhawk.cnbc.cmu.edu:/datasmart/leelab/raw_data_messy/cortex_exp`. Each monkey should have one folder under it.
5. Follow instruction for importing new data.

## Error handling
error message like 'len(recording_id_list) == len(results)' can imply that date-session is not unique. For example, I have experiments named 'cg' and 'gra_12', on day 20161011, I have run both of these two experiments. If I run 'cg' first and then 'gra_12', so I have 2 sessions on that day. When I organize files generated on that day, if I miss label both experiments with session number '1', this error can be thrown because the date-session is the same for both of them which can't be real.
