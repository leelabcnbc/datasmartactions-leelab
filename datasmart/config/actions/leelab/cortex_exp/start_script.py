from datasmart.actions.leelab.cortex_exp import CortexExpAction
import pickle
import os.path
from copy import deepcopy

if __name__ == '__main__':
    if os.path.exists('cortex-exp-batch.p'):
        with open('cortex-exp-batch.p', 'rb') as f:
            batch_records = pickle.load(f)
        config = deepcopy(CortexExpAction().config)
        print('in batch mode, will insert {} records'.format(len(batch_records)))
        config['batch_records'] = batch_records
    else:
        config = None

    a = CortexExpAction(config)
    test = input('enter to run, and enter anything then enter to revoke.')
    if not test:
        a.run()
    else:
        a.revoke()
