################################################################################
# Utility methods for accessing and manipulating the (maestro) data (set).
#
# Author(s): Nik Vaessen
################################################################################

import os
import pathlib
import json

import numpy as np

from keras.utils import to_categorical

################################################################################
# Constants

json_data_train = "train"
json_data_val = "val"
json_data_test = "test"

json_data_set_path = 'path'
json_data_set_composer_label = 'composer-label'
json_data_set_song_label = 'song-label'

json_data_used_composer_id = "num_composers"
json_data_used_song_id = "split_fraction"

json_data_label_to_composer = 'label_to_composer'
json_data_label_to_song = 'label_to_song'


################################################################################

def get_abs_paths(root, paths):
    corrected_paths = []

    for path in paths:
        corrected_paths.append(
            os.path.join(root, *pathlib.Path(path).parts[1:])
        )

    return corrected_paths


def load_dataset(path: str):
    print("loaded dataset from {}".format(path))

    info_object = os.path.join(path, "info.json")

    if not os.path.isfile(info_object):
        raise ValueError("could not find 'info.json' in {}".format(
            path
        ))

    with open(info_object, 'r') as f:
        info = json.load(f)

    train = info[json_data_train]
    train_paths = get_abs_paths(path, train[json_data_set_path])
    train_labels = train[json_data_set_composer_label]

    val = info[json_data_val]
    val_paths = get_abs_paths(path, val[json_data_set_path])
    val_labels = val[json_data_set_composer_label]

    test = info[json_data_test]
    test_paths = get_abs_paths(path, test[json_data_set_path])
    test_labels = test[json_data_set_composer_label]

    num_classes = len(info[json_data_label_to_composer].keys())

    return Dataset(
        train_paths,
        train_labels,
        val_paths,
        val_labels,
        test_paths,
        test_labels,
        num_classes
    )


class MfccDataset:

    used_composers = [
        "Johann Sebastian Bach",
        "Alexander Scriabin",
        "Claude Debussy",
        "Joseph Haydn",
        "Domenico Scarlatti",
        "Ludwig van Beethoven",
        "Franz Liszt",
        "Franz Schubert",
        "Fr\u00e9d\u00e9ric Chopin",
        "Robert Schumann",
         "Sergei Rachmaninoff",
         "Wolfgang Amadeus Mozart"
    ]

    def __init__(self, path):
        self.root_path = path[0:-5]

        with open(os.path.join(path, 'mfcc.json'), 'r') as f:
            info = json.load(f)

        self.composer_to_id = info['composer_to_id']

        self.mfcc_paths = info['paths']
        self.composer_labels = info['paths_composer_id']
        self.song_labels = info['paths_song_id']

    def get_composer_list(self):
        return MfccDataset.used_composers, \
               [self.composer_to_id[name] for name in MfccDataset.used_composers]

    def get_song_ids_from_composer(self, composer_id):
        song_ids = set()

        for composer_label, song_label in zip(self.composer_labels, self.song_labels):
            if composer_label == composer_id:
                song_ids.add(song_label)

        return list(song_ids)

    def get_mfcc(self, song_id, flatten):
        for song_label, path in zip(self.song_labels, self.mfcc_paths):
            if song_id == song_label:
                path = os.path.join(self.root_path, path)
                return load_mfcc([path], flatten)[0, ]


def load_mfcc(paths, flatten):
    x = np.array([np.load(path, allow_pickle=True)['arr_0'] for path in paths])

    if flatten:
        n = x.shape[0]
        m = x.shape[1] * x.shape[2]
        x = x.reshape(n, m)

    return x


class Dataset:

    def __init__(self,
                 train_paths,
                 train_labels,
                 val_paths,
                 val_labels,
                 test_paths,
                 test_labels,
                 num_classes
                 ):
        self.train_paths = train_paths
        self.train_labels = train_labels
        self.val_paths = val_paths
        self.val_labels = val_labels
        self.test_paths = test_paths
        self.test_labels = test_labels

        print('train_paths:', len(train_paths))
        print('train_labels', len(train_labels))

        print('val_paths:', len(val_paths))
        print('val_labels', len(val_labels))

        print('test_paths:', len(test_paths))
        print('test_labels', len(test_labels))

        self.num_classes = num_classes

    def load_mfcc(self, path, flatten):
        return load_mfcc(path, flatten)

    def load_labels(self, paths, output_encoded):
        if output_encoded:
            return np.array([to_categorical(label, num_classes=self.num_classes)
                             for label in paths])
        else:
            return np.array([label for label in paths])

    def get_train_full(self, flatten=False, output_encoded=True):
        x = self.load_mfcc(self.train_paths, flatten=flatten)
        y = self.load_labels(self.train_labels, output_encoded)

        return x, y

    def get_val_full(self, flatten=False, output_encoded=True):
        x = self.load_mfcc(self.val_paths, flatten=flatten)
        y = self.load_labels(self.val_labels, output_encoded)

        return x, y

    def get_test_full(self, flatten=False, output_encoded=True):
        x = self.load_mfcc(self.test_paths, flatten=flatten)
        y = self.load_labels(self.test_labels, output_encoded)

        return x, y


################################################################################


def quick_test():
    dir = "/home/nik/kth/y1p1/speech/project/data/debug/"
    train_dir = os.path.join(dir, "train")
    val_dir = os.path.join(dir, "val")
    test_dir = os.path.join(dir, "test")

    for file in os.listdir(train_dir):
        obj = np.load(os.path.join(train_dir, file), allow_pickle=True)['arr_0']

        mfcc = obj
        print(mfcc)
        print(mfcc.shape)
        print()
        break


def main():
    dir = "/home/nik/kth/y1p1/speech/project/data/debug/"

    ds = load_dataset(dir)

    x, y = ds.get_train_full()

    print(len(x))
    print(len(y))

    print(x[0], x[0].shape)
    print(y[0], y[0].shape)


if __name__ == '__main__':
    main()
