# Pianition, a neural network for recognising piano composers

# Data

`./download.sh` to download the (100 gb) .zip file of the dataset.

`python3 data_parse.py` to generate a `sample_<number>.npz` file for each data sample.

```python
import numpy as np

info = np.load('info.npz')['info']

for path in info['paths']:
  sample = np.load(path)['arr_0']
  id = sample[0]
  mfcc = sample[1]
```

info contains the following keys:

* `n_samples`: the number of data samples 
* `composed_to_id`: dictionary mapping a composer name to an id
* `id_to_composer`: dictionary mapping an id to a composer name
* `n_fft`: n_fft parameter used in computing the mffc
* `hop_length`: hop_lengths parameter used in computing the mfcc
* `paths`': an array with the relative path to all data samples.
