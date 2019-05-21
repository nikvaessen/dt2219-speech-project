################################################################################
#
# Create a reproducible train/val/test split of the maestro data
#
# Author(s): Nik Vaessen
################################################################################

import sys
import os
import math
import json

import numpy as np
from typing import Tuple, List

import data_wav2mfcc as mfcc

################################################################################
# Constants

split_fraction = (70, 20, 10)
minimum_num_samples_by_composer = 30

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

info_file_path = os.path.join("mfcc", "mfcc.json")

each_column_is_mfcc = True
time_axis = 1 if each_column_is_mfcc else 0
mffc_axis = 1 if time_axis == 0 else 0


################################################################################
# Helper methods


def get_info() -> dict:
    with open(info_file_path) as f:
        return json.load(f)


def load_sample(path: str) -> Tuple[int, np.ndarray]:
    sample = np.load(path, allow_pickle=True)['arr_0']

    if each_column_is_mfcc:
        sample[1] = sample[1].transpose()

    return sample


def split_sample(sample: np.ndarray, window_size=256) -> List[np.ndarray]:
    num_splits = sample.shape[time_axis] // window_size

    if each_column_is_mfcc:
        sample = sample[:, 0:num_splits * window_size]
    else:
        sample = sample[0:num_splits * window_size, :]

    samples = np.split(sample, num_splits, axis=time_axis)

    return samples


def extract_first_window(sample, window_size=256):
    if each_column_is_mfcc:
        return sample[:, 0:window_size]
    else:
        return sample[0:window_size, :]


def get_data(paths,
             split_data=True,
             only_first_window=False,
             window_size=256,
             progress_bar=False):
    if split_data and only_first_window:
        raise ValueError("cannot split data AND only use first sample!")
    if not split_data and not only_first_window:
        raise ValueError("specify one of 'split_data' or 'use_first_window'")
    if window_size < 1 or not isinstance(window_size, int):
        raise ValueError("window size {} is invalid, "
                         "should be > 1 and integer".format(window_size))

    gave_warning = False
    data_tuples = []

    for idx, path in enumerate(paths):
        if progress_bar:
            print("\r{}/{}".format(idx, len(paths)), flush=True, end="")

        if os.path.exists(path):
            id, sample = load_sample(path)

            if split_data:
                samples = [(id, sample) for sample in
                           split_sample(sample, window_size=window_size)]
            else:
                samples = [(id, extract_first_window(sample,
                                                     window_size=window_size))
                           ]

            data_tuples += samples

        elif not gave_warning:
            gave_warning = True
            print("Warning: one (or more) data paths are missing! (could "
                  "not find {})".format(path))

    if progress_bar:
        print()

    return data_tuples


def get_id_count():
    info = get_info()

    count = {}
    path_id = info[mfcc.json_mffc_paths_composer_id]

    for id in path_id:
        if id in count:
            count[id] += 1
        else:
            count[id] = 1

    return count


def get_allowed_paths(use_only_count_bigger_than=30):
    info = get_info()

    allowed_composers = [id for id, count in get_id_count().items()
                         if count > use_only_count_bigger_than]

    allowed_paths = []

    paths = info[mfcc.json_mffc_paths]
    paths_composer_id = info[mfcc.json_mffc_paths_composer_id]
    paths_song_id = info[mfcc.json_mffc_paths_song_id]

    for path, comp_id, song_id in zip(paths, paths_composer_id, paths_song_id):
        if comp_id in allowed_composers:
            allowed_paths.append((path, comp_id, song_id))

    return allowed_paths


def tracks_by_composer_id():
    allowed_tracks = get_allowed_paths(use_only_count_bigger_than=minimum_num_samples_by_composer)
    track_by_composer = {}

    for track, comp_id, song_id in allowed_tracks:
        if comp_id not in track_by_composer:
            track_by_composer[comp_id] = []

        track_by_composer[comp_id].append((track, comp_id, song_id))

    return track_by_composer


def create_split_paths():
    track_by_composer = tracks_by_composer_id()

    if sum(split_fraction) != 100:
        raise ValueError("split needs to sum up to 100")

    split = [s / 100 for s in split_fraction]

    train = []
    val = []
    test = []

    print(track_by_composer)

    for comp_id, tracks in track_by_composer.items():
        n = len(tracks)

        num_val = math.ceil(n * split[1])
        num_test = math.ceil(n * split[2])

        num_train = n - num_val - num_test

        track_train = tracks[:num_train]
        tracks_val = tracks[num_train: num_train + num_val]
        tracks_test = tracks[-num_test:]

        train += track_train
        val += tracks_val
        test += tracks_test

    return train, val, test


################################################################################
# main function executing the splitting logic

def save_objects(output_path, object_list):
    if not os.path.isdir(output_path):
        os.mkdir(output_path)

    for idx, (id, sample) in enumerate(object_list):
        full_path = os.path.join(output_path, "sample{}.npz".format(idx))

        np.savez_compressed(full_path, (id, sample))


def main():
    if len(sys.argv) != 2:
        print("usage: python3 data_split path_to_storage")
        exit()

    root_path = sys.argv[1]
    print("saving data to", root_path)

    if not os.path.isdir(root_path):
        os.mkdir(root_path)

    tr_paths, v_paths, t_paths = create_split_paths()

    print(tr_paths[0:5])
    # Training data
    print("extracting training data...")
    tr = get_data(tr_paths, split_data=False, only_first_window=True,
                  progress_bar=True)
    # print(tr)
    print(tr[0])
    # output_pa




    # print("training data saved to", output_path)
    #
    # # Validation data
    # print("extracting validation data...")
    # v = data_util._get_data(v_paths, split_data=False, only_first_window=True,
    #                         progress_bar=True)
    # output_path = os.path.join(root_path, "val")
    # save_objects(output_path, v)
    #
    # v = None
    # print("validation data saved to", output_path)
    #
    # # Testing data
    # print("extracting test data...")
    # t = data_util._get_data(t_paths, split_data=False, only_first_window=True,
    #                         progress_bar=True)
    #
    # output_path = os.path.join(root_path, "test")
    # save_objects(output_path, t)
    #
    # t = None
    # print("test data saved to", output_path)


if __name__ == '__main__':
    main()
