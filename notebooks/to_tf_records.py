#!/usr/bin/env python
# coding: utf-8

# In[1]:


from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np
import tensorflow as tf
from tqdm import tqdm_notebook as tqdm

import os
import re
import json

__author__ = "Sri Datta Budaraju"

tf.enable_eager_execution()


# In[2]:


def convert_to_tfRecords(data_path, info_path, dataset, tfRecord_name):
    """
    Convert each sample.npz to tf record along with the label
    
    Arguments:
        data_path -- path to .npz files
        info_path -- path to json file
        dataset -- train/val/test according to the json keys
        tfRecord_name -- name the tfRecord
        
    outputs:
        writes tfRecords
    """
    
    # Helper functions to Format features
    def _float_feature(value):
        """Returns a float_list from a float / double."""
        return tf.train.Feature(float_list=tf.train.FloatList(value=value))

    def _int64_feature(value):
        """Returns an int64_list from a bool / enum / int / uint."""
        return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))

    
    # Progress bar
    totalfiles = 0
    for root, dirs, files in os.walk(data_path):
        for file in files:
            if file.endswith('.npz'):
                totalfiles += 1
    
    pbar = tqdm(total=totalfiles)

    # get ground truth info
    with open("../data/debug/info.json") as json_file:
        info = json.load(json_file)
    label_list = info[dataset]['composer-label']
    counter = 0
    
    # tfRecord Writer
    if(os.path.isfile(tfRecord_name+".tfrecords")):
        print("Record with the same name exists")
        return 
    writer = tf.python_io.TFRecordWriter(tfRecord_name +
                                         '.tfrecords')

    # for each spectrogram
    for sample in sorted(os.listdir(data_path),
                         key=lambda x: int(re.split(r'(\d+)', x)[1])):
        sample = np.load(data_path + sample)
        sample_lmfcc = sample["arr_0"]

        # Features 1D spectrogram and composer-label
        feature = {
            'feature0': _float_feature(sample['arr_0'].flatten(order='F')),
            'feature1': _int64_feature(label_list[counter])
        }

        example = tf.train.Example(features=tf.train.Features(feature=feature))
        serialized = example.SerializeToString()
        # Write serialized record
        writer.write(serialized)
        
        counter += 1
        pbar.update(1)
        pbar.refresh()
    
    pbar.close()


# In[3]:


# Testing the function

data_path = "../data/debug/test/"
info_path = "../data/debug/info.json"
dataset = "test"
tfRecord_name = "../data/debug/sample"

convert_to_tfRecords(data_path, info_path, dataset, tfRecord_name)


# In[4]:


# Reading from records

for record in tf.python_io.tf_record_iterator(tfRecord_name+'.tfrecords'):
    example = tf.train.Example()
    _ = example.ParseFromString(record)
    LMFCC = np.array(example.features.feature['feature0'].float_list.value)
    LMFCC = LMFCC.reshape(128, 256, order="F")
    label = np.array(example.features.feature['feature1'].int64_list.value)
    print(LMFCC.shape, end=' --> ')
    print(*label)
    break


# In[5]:


# Sanity Check

sample = np.load("../data/debug/test/sample0.npz")
sample = sample["arr_0"]
print(sample.shape)
assert(np.allclose([sample], LMFCC))


# In[ ]:




