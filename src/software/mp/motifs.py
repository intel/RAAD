#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Yan Zhu, Chin-Chia Michael Yeh, Zachary Zimmerman, Kaveh Kamgar, Eamonn Keogh, Tyler Woods, Joseph Tarango
# *****************************************************************************/
# Internal meta functions of python.
from __future__ import absolute_import, division, print_function, \
    unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations

from . import distanceProfile
import numpy as np


def motifs(ts, mp, max_motifs=3, radius=2, n_neighbors=None, ex_zone=None):
    """
    Computes the top k motifs from a matrix profile

    Parameters
    ----------
    ts: time series to used to calculate mp
    mp: tuple, (matrix profile numpy array, matrix profile indices)
    max_motifs: the maximum number of motifs to discover
    ex_zone: the number of samples to exclude and set to Inf on either side of a found motifs defaults to m/2
    radius:
    n_neighbors:

    Returns tuple (motifs, distances)
    @todo motifs: a list of lists of indexes representing the motif starting locations.
    @todo distances: list of minimum distances for each motif
    """

    motifsFound = []
    distances = []
    try:
        mp_current, mp_idx = mp
    except TypeError:
        raise ValueError("argument mp must be a tuple")
    mp_current = np.copy(mp_current)

    if len(ts) <= 1 or len(mp_current) <= 1 or max_motifs == 0:
        return [], []

    m = len(ts) - len(mp_current) + 1
    if m <= 1:
        raise ValueError('Matrix profile is longer than time series.')
    if ex_zone is None:
        ex_zone = m / 2

    for _ in range(max_motifs):
        # find minimum distance and index location
        min_idx = mp_current.argmin()
        motif_distance = mp_current[min_idx]
        if motif_distance == np.inf:
            return motifsFound, distances
        if motif_distance == 0.0:
            motif_distance += np.finfo(mp_current.dtype).eps

        motif_set = set()
        initial_motif = [min_idx]
        pair_idx = int(mp[1][min_idx])
        if mp_current[pair_idx] != np.inf:
            initial_motif += [pair_idx]

        motif_set = set(initial_motif)

        prof, _ = distanceProfile.massDistanceProfile(ts, initial_motif[0], m)

        # kill off any indices around the initial motif pair since they are
        # trivial solutions
        for idx in initial_motif:
            _applyExclusionZone(prof, idx, ex_zone)
        # exclude previous motifs
        for ms in motifsFound:
            for idx in ms:
                _applyExclusionZone(prof, idx, ex_zone)

        # keep looking for the closest index to the current motif. Each
        # index found will have an exclusion zone applied as to remove
        # trivial solutions. This eventually exits when there's nothing
        # found within the radius distance.
        prof_idx_sort = prof.argsort()

        for nn_idx in prof_idx_sort:
            if n_neighbors is not None and len(motif_set) >= n_neighbors:
                break
            if prof[nn_idx] == np.inf:
                continue
            if prof[nn_idx] < motif_distance * radius:
                motif_set.add(nn_idx)
                _applyExclusionZone(prof, nn_idx, ex_zone)
            else:
                break

        for motifItem in motif_set:
            _applyExclusionZone(mp_current, motifItem, ex_zone)

        if len(motif_set) < 2:
            continue
        motifsFound += [list(sorted(motif_set))]
        distances += [motif_distance]

    return motifsFound, distances


def _applyExclusionZone(prof, idx, zone):
    start = int(max(0, idx - zone))
    end = int(idx + zone + 1)
    prof[start:end] = np.inf
