#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Tyler Woods, Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import tensorflow as tf
from tensorflow import keras

import numpy as np
import os, json, random
import matplotlib.pyplot as plt

def main():
    #fashion_mnist = keras.datasets.fashion_mnist

    #(train_images, train_labels), (test_images, test_labels) = fashion_mnist.load_data()


    if os.path.exists("QDist_2.txt") and os.path.exists("labels_1.txt"):
        with open("QDist_2.txt") as jF:
            shapelets = json.load(jF)

        with open("labels_1.txt") as jF:
            labels = json.load(jF)

        dists = []

        for key in shapelets:
            dists.append(shapelets[key])

        shuffArr = [i for i in zip(dists, labels)]
        random.shuffle(shuffArr)
        #print(shuffArr)


        dists = np.array([i[0] for i in shuffArr])
        labels = np.array([i[1] for i in shuffArr])
        print(labels)

        test = np.array(dists[0:1])
        train = dists[1:]
        test_labels = np.array(labels[0:1])
        train_labels = labels[1:]


        print(train.shape)

        #print(train_images)

        #class_names = ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat',
        #               'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']

        #train_images = train_images / 255.0
        #
        #test_images = test_images / 255.0

        model = keras.Sequential([
            keras.layers.Flatten(input_shape=(11, 11)),
            keras.layers.Dense(128, activation=tf.nn.relu),
            keras.layers.Dense(64, activation=tf.nn.relu),
            keras.layers.Dense(3, activation=tf.nn.softmax)
        ])

        model.compile(optimizer='adam',
                      loss='sparse_categorical_crossentropy',
                      metrics=['accuracy'])

        checkpoint_path = "training_2/cp_1.ckpt"
        checkpoint_dir = os.path.dirname(checkpoint_path)

        # Create checkpoint callback
        cp_callback = tf.keras.callbacks.ModelCheckpoint(checkpoint_path,
                                                         save_weights_only=True,
                                                         verbose=1)

        model.fit(train, train_labels, epochs=50, callbacks = [cp_callback])

        test_loss, test_acc = model.evaluate(dists, labels)
        #test_loss, test_acc = model.evaluate(test, test_labels)

        print(test_labels)

        print('Test accuracy:', test_acc)

        predictions = model.predict(test)

        model.save('my_model_new_data.h5')

if __name__ == '__main__':
    main()
