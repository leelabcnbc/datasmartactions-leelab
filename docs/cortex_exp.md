# `cortex_exp` DataSMART action

Oct. 31, 2016  
Yimeng Zhang

This documents illustrates how to efficiently use `cortex_exp` action.

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

under each `$RECORDING_ROOT`, put the following files.

* set of `itm`, `cnd`, `par`, `tm`
	* To be super correct, I think LUT should be included as well. But that is for future experiments. I suggest we come up with more **required** fields, and put all of them in revision 2 of `cortex_exp`. Summer suggested adding `.set`, `.blk` as well.
* a JSON file called `note.json` that stores a dictionary (object in JSON terminolgy), including at least `notes`, `RF`, and `blocks`. Additional parmameters are accepted as well, except `data`, which has been taken by Summer to keep track of what files are used.
	* Another reserved field might be `revision`, which can be useful to distinguish between different versions of CORTEX schema (hopefully, there won't be many).
* set of `nev`, `ns2`, `ns6`, `ccf` files. Their names must be of form `MA_YYYY_MM_DD_00X`, where `MA` is the two letter abbreviation for the given monkey, and `00X` means `{:03d}.format(X)` (in Python syntax).

To be super exact, I allow exactly one file with of each extensions above in `$RECORDING_ROOT`.