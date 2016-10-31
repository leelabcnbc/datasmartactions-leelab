#!/usr/bin/env bash
. activate datasmart
# it would be a very bad idea if you have space in your names
# this one assumes where those folders are.
export PYTHONPATH=~/datasmart:~/datasmartactions-leelab:$PYTHONPATH
python cortex_exp_master_script.py
