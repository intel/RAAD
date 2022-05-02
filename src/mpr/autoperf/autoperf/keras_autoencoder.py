#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Brad McDonald, Mejbah ul Alam, Justin Gottschlich, Abdullah Muzahid
# *****************************************************************************/
"""keras_autoencoder.py

A keras implementation of an autoEncoderObj for AutoPerf, accompanied by required
callback functions.
"""

import os
import sys
import logging
import warnings
from copy import deepcopy
from datetime import datetime

import numpy as np
from tensorflow.keras.utils import Progbar

# Keras is included as part of TensorFlow in v2
import tensorflow as tf
from tensorflow.keras import callbacks, optimizers
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense
from tensorboard.plugins import projector

from autoperf.utils import getAutoperfDir as getAutoPerfDir
from autoperf.config import loadConfig_TryDetect

log = logging.getLogger("rich")

timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")


class LossHistory(callbacks.Callback):
    """A callback class for logging the training and validation losses."""

    monitor = dict()
    record = dict()

    def __init__(self, monitor: dict = None):
        """Constructor to specify some monitoring criteria.

        Args:
            monitor (optional): Types of values to monitor at different points. Ex:
                                {'batch_end': ['loss'], 'epoch_end': ['val_loss']}
        """
        super().__init__()
        self.monitor = monitor

    def on_train_begin(self, logs: dict = None):
        """Callback that runs when training is begun."""
        for k in self.monitor.keys():
            self.record[k] = dict()
            for val in self.monitor[k]:
                self.record[k][val] = []

    def on_batch_end(self, batch: int, logs: dict = None):
        """Callback that runs at the end of every training batch.

        Args:
            batch: Training batch number.
            logs: Log dictionary containing metrics.
        """
        status = 'batch_end'
        if (logs is not None) and (self.monitor is not None) and (status in self.monitor):
            for v in self.monitor[status]:
                if v in logs:
                    self.record[status][v].append(logs.get(v))

    def on_epoch_end(self, epoch: int, logs: dict = None):
        """Callback that runs at the end of every training epoch.

        Args:
            epoch: Training epoch number.
            logs: Log dictionary containing metrics.
        """
        status = 'epoch_end'
        if (logs is not None) and (self.monitor is not None) and (status in self.monitor):
            for v in self.monitor[status]:
                if v in logs:
                    self.record[status][v].append(logs.get(v))


class EarlyStoppingByLossVal(callbacks.Callback):
    """A callback class for early stopping during model training."""

    def __init__(self, monitor: str = 'val_loss', value: float = 0.00001, verbose: bool = False):
        """Constructor to specify some monitoring criteria.

        Args:
            monitor (optional): Type of loss value to monitor.
            value (optional): Early stopping threshold.
            verbose (optional): Verbosity flag.
        """
        super().__init__()
        self.monitor = monitor
        self.value = value
        self.verbose = verbose

    def on_epoch_end(self, epoch: int, logs: dict = None):
        """Callback at the end of an epoch, check if we should early stop.

        Args:
            epoch: Current epoch iteration.
            logs: Logs being tracked by the LossHistory class.
        """
        if logs is not None:
            current = logs.get(self.monitor)

            if current is None:
                warnings.warn(f"Early stopping requires {self.monitor} available!", RuntimeWarning)

            elif current < self.value:
                if self.verbose:
                    log.info('Epoch %d: early stopping THR', epoch)
                self.model.stop_training = True


def trainAutoEncoder(autoEncoderObj: Model, trainingData: np.ndarray,
                     monitor: dict) -> tuple[Model, LossHistory]:
    """Trains an autoEncoderObj with provided trainingData.

    Args:
        autoEncoderObj: A Keras autoEncoderObj.
        trainingData: Data to train on.
        monitor: Data to record during training. Ex:
                 {'batch_end': ['loss'], 'epoch_end': ['val_loss']}

    Returns:
        A trained model.
        The history of the monitored values.
    """
    cfg = loadConfig_TryDetect()
    history = LossHistory(monitor)

    # Force the training data to be evenly divisible by the batch size
    log.info('Training data length: %d', len(trainingData))

    if len(trainingData) < cfg.training.batch_size:
        log.error('Size of dataset (%d) is less than batch size (%s).',
                  len(trainingData), cfg.training.batch_size)
        sys.exit(-1)

    num_batches = len(trainingData) // cfg.training.batch_size
    trainingData = trainingData[:(num_batches * cfg.training.batch_size)]

    noisyTrainingData = deepcopy(trainingData)
    noisyTrainingData += np.random.normal(loc=0.0,
                                          scale=cfg.training.noise,
                                          size=trainingData.shape)

    log.info('Noisy training data: [%s]', ', '.join(map(str, noisyTrainingData[0])))
    log.info('Original training data: [%s]', ', '.join(map(str, trainingData[0])))

    log_dir = getAutoPerfDir(f'logs/fit/{timestamp}')
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir, update_freq=100, histogram_freq=1)

    autoEncoderObj.fit(x=noisyTrainingData, y=trainingData,
                       epochs=cfg.training.epochs,
                       batch_size=cfg.training.batch_size,
                       shuffle=True,
                       validation_split=0.2,
                       verbose=0,
                       callbacks=[history,
                                  tensorboard_callback,
                                  Progbar(target=None,
                                          stateful_metrics=f'epochs={cfg.training.epochs},'
                                                           f'data_size={noisyTrainingData.shape[0]},'
                                                           f'batch_size={cfg.training.batch_size}',
                                          verbose=2)])

    return autoEncoderObj, history


def predict(autoEncoderObj: Model, test_data: np.ndarray) -> np.ndarray:
    """Runs inference with the autoEncoderObj on `test_data`.

    Args:
        autoEncoderObj: A Keras autoEncoderObj.
        test_data: Data to test on.

    Returns:
        The autoEncoderObj predictions.
    """
    decoded_data = autoEncoderObj.predict(test_data, verbose=False)
    return decoded_data


def getAutoEncoderShape(model: Model) -> list:
    """Get the topology of an autoEncoderObj network.

    Args:
        model: A Keras autoEncoderObj.

    Returns:
        The network topology as a list.
    """
    topology = []
    for x in model.layers:
        if isinstance(x.output_shape, list):
            topology.append(x.output_shape[0][1])
        else:
            topology.append(x.output_shape[1])
    return topology


def getAutoEncoder(input_dim: int, encoder_dim: int, layer_dims: list = None) -> Model:
    """Construct a palindromic autoEncoderObj based on the provided configurations.

       This function creates a `tied weights` autoEncoderObj:
       [input_dim -> layers_dims -> encoder_dim -> reverse(layers_dims) -> input_dim]

    Args:
        input_dim: Input vector shape.
        encoder_dim: Latent space shape.
        layer_dims (optional): Specific layer dimensions to use.

    Returns:
        An untrained autoEncoderObj model.
    """
    cfg = loadConfig_TryDetect()
    input_layer = Input(shape=input_dim, name='input')

    index = 0
    prev = input_layer
    lDimsValid = layer_dims is not None
    lDimsSize = True if lDimsValid or 0 == len(layer_dims) else False
    if lDimsSize:
        for curr_dim in layer_dims:
            encoded = Dense(curr_dim, activation=cfg.model.activation, name=f'down_{index}')(prev)
            index += 1
            prev = encoded

    index -= 1
    encoded = Dense(encoder_dim, activation=cfg.model.activation, name='latent')(prev)
    prev = encoded
    if layer_dims is not None:
        for curr_dim in reversed(layer_dims):
            decoded = Dense(curr_dim, activation=cfg.model.activation, name=f'up_{index}')(prev)
            index -= 1
            prev = decoded

    decoded = Dense(input_dim, activation='sigmoid', name='output')(prev)
    if decoded is None:
        log.error(f"Decoded is none...")

    autoEncoder = Model(input_layer, decoded)

    opt = optimizers.get(cfg.training.optimizer)
    if opt.learning_rate:
        opt.learning_rate = cfg.training.learning_rate

    autoEncoder.compile(optimizer=opt, loss=cfg.training.loss)
    return autoEncoder


def loadTrainedModel() -> Model:
    """Loads a trained model from the .autoperf directory.

    Returns:
        Model: A trained Keras autoEncoderObj.
    """
    cfg = loadConfig_TryDetect()
    return tf.keras.models.load_model(getAutoPerfDir(cfg.model.filename))


def visualizeLatentSpace(model: Model, nominal_data: np.ndarray,
                         anomalous_data: np.ndarray):
    """Visualize the latent space using Tensorboard's Embeddings Projector.

    Args:
        model: A trained Keras autoEncoderObj.
        nominal_data: A list of nominal HPC measurements.
        anomalous_data: A list of anomalous HPC measurements.
    """
    # Down sample the data if needed
    desired_size = 2000
    if nominal_data.shape[0] > desired_size:
        indices = np.arange(nominal_data.shape[0])
        nominal_data = nominal_data[np.random.choice(indices, desired_size, replace=False)]

    if anomalous_data.shape[0] > desired_size:
        indices = np.arange(anomalous_data.shape[0])
        anomalous_data = anomalous_data[np.random.choice(indices, desired_size, replace=False)]

    latent = Model(inputs=model.input, outputs=model.get_layer('latent').output)
    nom_embeddings = latent.predict(nominal_data)
    anomalous_embeddings = latent.predict(anomalous_data)
    embeddings = tf.Variable(np.vstack([nom_embeddings, anomalous_embeddings]), name='embedding')
    log.info('Embeddings shape: (%s)', ', '.join(map(str, embeddings.shape)))

    log_dir = getAutoPerfDir(f'logs/fit/{timestamp}')
    os.makedirs(log_dir, exist_ok=True)

    with open(os.path.join(log_dir, 'metadata.tsv'), 'w') as f:
        for _ in range(nom_embeddings.shape[0]):
            f.write('Nominal\n')
        for _ in range(anomalous_embeddings.shape[0]):
            f.write('Anomalous\n')

    checkpoint = tf.train.Checkpoint(embedding=embeddings)
    checkpoint.save(os.path.join(log_dir, 'embeddings.ckpt'))

    config = projector.ProjectorConfig()
    embedding = config.embeddings.add()
    embedding.tensor_name = 'embedding/.ATTRIBUTES/VARIABLE_VALUE'
    embedding.metadata_path = 'metadata.tsv'
    projector.visualize_embeddings(log_dir, config)
