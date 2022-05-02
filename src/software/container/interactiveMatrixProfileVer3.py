#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Tyler Woods, Joseph Tarango
# *****************************************************************************/
# @package simularityProfile
# Based on https://www.cs.ucr.edu/~eamonn/MatrixProfile.html
"""
# The prototype for interactive matrix profile calculation using SCRIMP++
# Original tool created by Chin-Chia Michael Yeh / Eamonn Keogh 01/26/2016
# Modified by Yan Zhu 02/2018 (SCRIMP++)
%
# For details of the SCRIMP++ algorithm, see:
# Yan Zhu, Chin-Chia Michael Yeh, Zachary Zimmerman, Kaveh Kamgar, and Eamonn Keogh,
# "Solving Time Series Data Mining Problems at Scale with SCRIMP++", published in ICDM 2018.
%
# Usage:
# [matrixProfile, profileIndex, motifIndex, discordIndex] = interactiveMatrixProfileVer3_website(data, subLen);
# Output:
#     matrixProfile: matrix porfile of the self-join (vector)
#     profileIndex: matrix porfile index of the self-join (vector)
#     motifIndex: index of the first, second, and third motifs and their
#                 associated neighbors when stopped (3x2 cell)
#                 +-----------------------+------------------------+
#                 | indices for 1st motif | neighbors of 1st motif |
#                 +-----------------------+------------------------+
#                 | indices for 2nd motif | neighbors of 2nd motif |
#                 +-----------------------+------------------------+
#                 | indices for 3rd motif | neighbors of 3rd motif |
#                 +-----------------------+------------------------+
#     discordIndex: index of discords when stopped (vector)
# Input:
#     data: input time series (vector)
#     subLen: subsequence length (scalar)
%
# We uploaded this code as a courtesy to the community. Note that as the
# Matlab GUI eats up a lot of time, the SCRIMP++ runtime reported in the
# paper is not measured by this tool, but the non-GUI implementations on the
# website.
"""

from __future__ import absolute_import, division, print_function, \
    unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
from native import *
import numpy


def cell2mat_(x: list) -> numpy.matrixlib.defmatrix.matrix:
    """
    Convert cell array of matrices to single matrix.
    x: A list.
    returns: Returns cell arrays.
    """
    try:
        return numpy.matrix(x)
    except Exception as e:
        print('Exception = ', str(e))


def get_(*args):
    return


def set_(*args):
    return


def axes_(*args):
    return


def uicontrol_(*args):
    return


def hold_(*args):
    return


def plot__(*args):
    return


def any_(*args):
    return


def inf_(*args):
    return


def randperm_(*args):
    return


def plot_(*args):
    return


def drawnow(*args):
    return


def tic_():
    return


def toc_(*args):
    return


def exist_(*args):
    return


def delete_(*args):
    return


def sprintf_(*args):
    return


pushStopBtn = None


def findMotifs_(matrixProfileCur, profileIndex, dataLen, subLen, proLen, data, dataFreq, dataMu, dataSig, isSkip,
                excZoneLen, radius, nargout=1):
    motifIdxs = cell(3, 2)
    for i in arange(1, 3).reshape(-1):
        motifDistance, minIdx = min(matrixProfileCur, nargout=2)
        motifDistance = motifDistance ** 2
        motifIdxs[i, 1] = sort([minIdx, profileIndex[minIdx]])
        motifIdx = motifIdxs[i, 1](1)
        query = data[motifIdx:motifIdx + subLen - 1]
        distProfile = mass_(dataFreq, query, dataLen, subLen, dataMu, dataSig, dataMu[motifIdx], dataSig[motifIdx])
        distProfile = abs(distProfile)
        distProfile[distProfile > motifDistance * radius] = inf
        motifZoneStart = max(1, motifIdx - excZoneLen)
        motifZoneEnd = min(proLen, motifIdx + excZoneLen)
        distProfile[motifZoneStart:motifZoneEnd] = inf
        motifIdx = motifIdxs[i, 1](2)
        motifZoneStart = max(1, motifIdx - excZoneLen)
        motifZoneEnd = min(proLen, motifIdx + excZoneLen)
        distProfile[motifZoneStart:motifZoneEnd] = inf
        distProfile[isSkip] = inf
        distanceOrder, distanceIdxOrder = sort(distProfile, 'ascend', nargout=2)
        longestLength = length(distanceOrder)
        motifNeighbor = zeros(1, longestLength)
        for j in arange(1, longestLength).reshape(-1):
            if isinf(distanceOrder[1]) or length(distanceOrder) < j:
                motifNeighbor = motifNeighbor[motifNeighbor != 0]
                break
            motifNeighbor[j] = distanceIdxOrder[1]
            distanceOrder[1] = []
            distanceIdxOrder[1] = []
            distanceOrder[abs(distanceIdxOrder - motifNeighbor[j]) < excZoneLen] = []
            distanceIdxOrder[abs(distanceIdxOrder - motifNeighbor[j]) < excZoneLen] = []
        motifNeighbor[motifNeighbor == 0] = []
        motifIdxs[i, 2] = motifNeighbor
        removeIdx = cell2mat_(motifIdxs[i, :])
        for j in arange(1, length(removeIdx)).reshape(-1):
            removeZoneStart = max(1, removeIdx[j] - excZoneLen)
            removeZoneEnd = min(proLen, removeIdx[j] + excZoneLen)
            matrixProfileCur[removeZoneStart:removeZoneEnd] = inf
    return motifIdxs, matrixProfileCur


def pushDiscardBtn_(src, __, btnNum, nargout=1):
    mainWindowFig = get_(src, 'parent')
    mainWindow = get_(mainWindowFig, 'userdata')
    mainWindow.discardIdx = [mainWindow.discardIdx, mainWindow.motifIdxs[btnNum, 1]]
    for i in arange(1, 3).reshape(-1):
        set_(mainWindow.discardBtn(i), 'enable', 'off')
    set_(mainWindow.fig, 'userdata', mainWindow)
    return


def pushStopBtn_(src, __, nargout=1):
    mainWindowFig = get_(src, 'parent')
    mainWindow = get_(mainWindowFig, 'userdata')
    mainWindow.stopping = True
    for i in arange(1, 3).reshape(-1):
        set_(mainWindow.discardBtn(i), 'enable', 'off')
    set_(src, 'enable', 'off')
    set_(mainWindow.fig, 'userdata', mainWindow)
    return


def massPre_(data, dataLen, subLen, nargout=1):
    data[dataLen + 1:(subLen + dataLen)] = 0
    dataFreq = fft(data)
    dataCumsum = cumsum(data)
    data2Cumsum = cumsum(data ** 2)
    data2Sum = data2Cumsum[subLen:dataLen] - [[0], [data2Cumsum[1:dataLen - subLen]]]
    dataSum = dataCumsum[subLen:dataLen] - [[0], [dataCumsum[1:dataLen - subLen]]]
    dataMu = dataSum / subLen
    data2Sig = (data2Sum / subLen) - (dataMu ** 2)
    dataSig = sqrt(data2Sig)
    return dataFreq, dataMu, dataSig


def mass_(dataFreq, query, dataLen, subLen, dataMu, dataSig, queryMu, querySig, nargout=1):
    query = query[query.shape[0]:- 1:1]
    query[subLen + 1:(subLen + dataLen)] = 0
    queryFreq = fft(query)
    productFreq = dataFreq.dot(queryFreq)
    product = ifft(productFreq)
    distProfile = 2 * (subLen - (product[subLen:dataLen] - subLen * dataMu * queryMu) / (dataSig * querySig))
    return distProfile


def diagonalDist_(data, idx, dataLen, subLen, proLen, dataMu, dataSig, nargout=1):
    xTerm = ones(proLen - idx + 1, 1) * (data[idx:idx + subLen - 1].T * data[1:subLen])
    mTerm = data[idx:proLen - 1].dot(data[1:proLen - idx])
    aTerm = data[idx + subLen:data.shape[0]].dot(data[subLen + 1:dataLen - idx + 1])
    if proLen != idx:
        xTerm[2:xTerm.shape[0]] = xTerm[2:xTerm.shape[0]] - cumsum(mTerm) + cumsum(aTerm)
    distProfile = (xTerm - subLen.dot(dataMu[idx:dataMu.shape[0]]).dot(dataMu[1:proLen - idx + 1])) / (
        subLen.dot(dataSig[idx:dataSig.shape[0]]).dot(dataSig[1:proLen - idx + 1]))
    distProfile = 2 * subLen * (1 - distProfile)
    return distProfile


def zeroOneNorm_(x, nargout=1):
    x = x - min(x[not isinf(x) and not isnan(x)])
    x = x / max(x[not isinf(x) and not isnan(x)])
    return x


def mainResize_(src, __, nargout=1):
    mainWindow = get_(src, 'userdata')
    figPosition = get_(mainWindow.fig, 'position')
    axGap = 38
    axesHeight = round((figPosition[4] - axGap * 5 - 60) / 6)
    set_(mainWindow.dataAx, 'position', [30, 5 * axesHeight + 5 * axGap + 30, figPosition[3] - 60, axesHeight])
    set_(mainWindow.profileAx, 'position', [30, 4 * axesHeight + 4 * axGap + 30, figPosition[3] - 60, axesHeight])
    set_(mainWindow.discordAx, 'position', [30, 30, figPosition[3] - 160, axesHeight])
    set_(mainWindow.stopBtn, 'position', [figPosition[3] - 120, 30, 90, 20])
    set_(mainWindow.dataText, 'position', [30, 6 * axesHeight + 5 * axGap + 30, figPosition[3] - 60, 18])
    set_(mainWindow.profileText, 'position', [30, 5 * axesHeight + 4 * axGap + 30, figPosition[3] - 60, 18])
    set_(mainWindow.discordText, 'position', [30, 1 * axesHeight + 30, figPosition[3] - 160, 18])
    for i in arange(1, 3).reshape(-1):
        set_(mainWindow.motifAx(i), 'position',
             [30, (4 - i) * axesHeight + (4 - i) * axGap + 30, figPosition[3] - 160, axesHeight])
    for i in arange(1, 3).reshape(-1):
        set_(mainWindow.motifText(i), 'position',
             [30, (5 - i) * axesHeight + (4 - i) * axGap + 30, figPosition[3] - 160, 18])
    for i in arange(1, 3).reshape(-1):
        set_(mainWindow.discardBtn(i), 'position',
             [figPosition[3] - 120, (4 - i) * axesHeight + (4 - i) * axGap + 30, 90, 20])
    return


def interactiveMatrixProfileVer3_(data, subLen, nargout=1):
    excZoneLen = round(subLen)
    radius = 2.0
    updatePeriod = 1
    anytimeMode = 3
    preStep = floor(subLen * 0.25)
    dataLen = length(data)
    if subLen > dataLen / 2:
        error(['Error: Time series is too short ', 'relative to desired subsequence length'])
    if subLen < 4:
        error('Error: Subsequence length must be at least 4')
    if subLen > dataLen / 5:
        error('Error: subsequenceLength > dataLength / 20')
    if dataLen == size(data, 2):
        data = data.T
    titleTxt = 'UCR Interactive Matrix Profile Calculation 3.0'
    mainWindow = None
    mainWindow.fig = figure(name=titleTxt, visible='off', toolbar='none', ResizeFcn=mainResize_)
    backColor = get_(mainWindow.fig, 'color')
    mainWindow.dataAx = axes_('parent', mainWindow.fig, 'units', 'pixels', 'xlim', [1, dataLen], 'xtick', [1, dataLen],
                              'ylim', [- 0.05, 1.05], 'ytick', [], 'ycolor', [1, 1, 1])
    mainWindow.profileAx = axes_('parent', mainWindow.fig, 'units', 'pixels', 'xlim', [1, dataLen], 'xtick',
                                 [1, dataLen], 'ylim', [0, 2 * sqrt(subLen)])
    mainWindow.discordAx = axes_('parent', mainWindow.fig, 'units', 'pixels', 'xlim', [1, subLen], 'xtick', [1, subLen],
                                 'ylim', [- 0.05, 1.05], 'ytick', [], 'ycolor', [1, 1, 1])
    mainWindow.stopBtn = uicontrol_('parent', mainWindow.fig, 'style', 'pushbutton', 'string', 'Stop', 'fontsize', 10,
                                    'callback', pushStopBtn)
    mainWindow.dataText = uicontrol_('parent', mainWindow.fig, 'style', 'text', 'string', '', 'fontsize', 10,
                                     'backgroundcolor', backColor, 'horizontalalignment', 'left')
    mainWindow.profileText = uicontrol_('parent', mainWindow.fig, 'style', 'text', 'string',
                                        'The best-so-far matrix profile', 'fontsize', 10, 'backgroundcolor', backColor,
                                        'horizontalalignment', 'left')
    mainWindow.discordText = uicontrol_('parent', mainWindow.fig, 'style', 'text', 'string', '', 'fontsize', 10,
                                        'backgroundcolor', backColor, 'horizontalalignment', 'left')
    mainWindow.motifAx = zeros(3, 1)
    for i in arange(1, 3).reshape(-1):
        mainWindow.motifAx[i] = axes_('parent', mainWindow.fig, 'units', 'pixels', 'xlim', [1, subLen], 'xtick',
                                      [1, subLen], 'ylim', [- 0.05, 1.05], 'ytick', [], 'ycolor', [1, 1, 1])
    mainWindow.motifText = zeros(3, 1)
    for i in arange(1, 3).reshape(-1):
        mainWindow.motifText[i] = uicontrol_('parent', mainWindow.fig, 'style', 'text', 'string', '', 'fontsize', 10,
                                             'backgroundcolor', backColor, 'horizontalalignment', 'left')
    mainWindow.discardBtn = zeros(3, 1)
    for i in arange(1, 3).reshape(-1):
        mainWindow.discardBtn[i] = uicontrol_('parent', mainWindow.fig, 'style', 'pushbutton', 'string', 'Discard',
                                              'fontsize', 10, 'callback',
                                              lambda src, cbdata: pushDiscardBtn_(src, cbdata, i))
    dataPlot = zeroOneNorm_(data)
    hold_(mainWindow.dataAx, 'on')
    plot_(arange(1, dataLen), dataPlot, 'r', 'parent', mainWindow.dataAx)
    hold_(mainWindow.dataAx, 'off')
    proLen = dataLen - subLen + 1
    isSkip = False(proLen, 1)
    for i in arange(1, proLen).reshape(-1):
        if any_(isnan(data[i:i + subLen - 1])) or any(isinf(data[i:i + subLen - 1])):
            isSkip[i] = True
    data[isnan(data) or isinf(data)] = 0
    dataFreq, dataMu, dataSig = massPre_(data, dataLen, subLen, nargout=3)
    matrixProfile = inf_(proLen, 1)
    profileIndex = zeros(proLen, 1)
    if anytimeMode == 1:
        idxOrder = randperm_(proLen)
    else:
        if anytimeMode == 2:
            idxOrder = arange(excZoneLen + 1, proLen)
            idxOrder = idxOrder[randperm_(length(idxOrder))]
        else:
            if anytimeMode == 3:
                Preidx = arange(1, proLen, preStep)
                PreidxOrder = Preidx[randperm_(length(Preidx))]
                idxOrder = arange(excZoneLen + 1, proLen)
                idxOrder = idxOrder[randperm_(length(idxOrder))]
    txtTemp = ['The best-so-far 1st motifs are located at %d (green) and %d (cyan)',
               'The best-so-far 2nd motifs are located at %d (green) and %d (cyan)',
               'The best-so-far 3rd motifs are located at %d (green) and %d (cyan)']
    motifColor = ['g', 'c']
    discordColor = ['b', 'r', 'g']
    neighborColor = 0.5 * ones(1, 3)
    mainWindow.stopping = False
    mainWindow.discardIdx = []
    set_(mainWindow.fig, 'userdata', mainWindow)
    firstUpdate = copy(True)
    if anytimeMode == 1 or anytimeMode == 2:
        iterationEnd = length(idxOrder)
    else:
        if anytimeMode == 3:
            iterationEnd = length(PreidxOrder) + length(idxOrder)
            dotproduct = zeros(proLen, 1)
            refine_distance = inf_(proLen, 1)
            orig_index = arange(1, proLen)
    timer = tic_()
    for i in arange(1, iterationEnd).reshape(-1):
        if anytimeMode == 1 or anytimeMode == 2:
            idx = idxOrder[i]
        else:
            if anytimeMode == 3:
                if i <= length(PreidxOrder):
                    curStage = 1
                    idx = PreidxOrder[i]
                else:
                    curStage = 2
                    idx = idxOrder[i - length(PreidxOrder)]
        if isSkip[idx]:
            continue
        drawnow
        query = data[idx:idx + subLen - 1]
        if anytimeMode == 1:
            distProfile = mass_(dataFreq, query, dataLen, subLen, dataMu, dataSig, dataMu[idx], dataSig[idx])
            distProfile = abs(distProfile)
            distProfile = sqrt(distProfile)
            distProfile[isSkip] = inf
            excZoneStart = max(1, idx - excZoneLen)
            excZoneEnd = min(proLen, idx + excZoneLen)
            distProfile[excZoneStart:excZoneEnd] = inf
            updatePos = distProfile < matrixProfile
            profileIndex[updatePos] = idx
            matrixProfile[updatePos] = distProfile[updatePos]
            matrixProfile[idx], profileIndex[idx] = min(distProfile, nargout=2)
        else:
            if anytimeMode == 2 or (anytimeMode == 3 and curStage == 2):
                distProfile = diagonalDist_(data, idx, dataLen, subLen, proLen, dataMu, dataSig)
                distProfile = abs(distProfile)
                distProfile = sqrt(distProfile)
                pos1 = arange(idx, proLen)
                pos2 = arange(1, proLen - idx + 1)
                updatePos = matrixProfile[pos1] > distProfile
                profileIndex[pos1[updatePos]] = pos2[updatePos]
                matrixProfile[pos1[updatePos]] = distProfile[updatePos]
                updatePos = matrixProfile[pos2] > distProfile
                profileIndex[pos2[updatePos]] = pos1[updatePos]
                matrixProfile[pos2[updatePos]] = distProfile[updatePos]
                matrixProfile[isSkip] = inf
                profileIndex[isSkip] = 0
            else:
                if (anytimeMode == 3 and curStage == 1):
                    distProfile = mass_(dataFreq, query, dataLen, subLen, dataMu, dataSig, dataMu[idx], dataSig[idx])
                    distProfile = abs(distProfile)
                    distProfile = sqrt(distProfile)
                    distProfile[isSkip] = inf
                    excZoneStart = max(1, idx - excZoneLen)
                    excZoneEnd = min(proLen, idx + excZoneLen)
                    distProfile[excZoneStart:excZoneEnd] = inf
                    updatePos = distProfile < matrixProfile
                    profileIndex[updatePos] = idx
                    matrixProfile[updatePos] = distProfile[updatePos]
                    matrixProfile[idx], profileIndex[idx] = min(distProfile, nargout=2)
                    idx_nn = profileIndex[idx]
                    idx_diff = idx_nn - idx
                    dotproduct[idx] = (subLen - matrixProfile[idx] ** 2 / 2) * dataSig[idx] * dataSig[idx_nn] + subLen * \
                                      dataMu[idx] * dataMu[idx_nn]
                    endidx = min([proLen, idx + preStep - 1, proLen - idx_diff])
                    dotproduct[idx + 1:endidx] = dotproduct[idx] + cumsum(data[idx + subLen:endidx + subLen - 1].dot(
                        data[idx_nn + subLen:endidx + subLen - 1 + idx_diff]) - data[idx:endidx - 1].dot(
                        data[idx_nn:endidx - 1 + idx_diff]))
                    refine_distance[idx + 1:endidx] = sqrt(abs(2 * (subLen - (
                                dotproduct[idx + 1:endidx] - subLen * dataMu[idx + 1:endidx].dot(
                            dataMu[idx_nn + 1:endidx + idx_diff])) / (dataSig[idx + 1:endidx].dot(
                        dataSig[idx_nn + 1:endidx + idx_diff])))))
                    beginidx = max([1, idx - preStep + 1, 1 - idx_diff])
                    dotproduct[idx - 1:- 1:beginidx] = dotproduct[idx] + cumsum(
                        data[idx - 1:- 1:beginidx].dot(data[idx_nn - 1:- 1:beginidx + idx_diff]) - data[
                                                                                                   idx - 1 + subLen:- 1:beginidx + subLen].dot(
                            data[idx_nn - 1 + subLen:- 1:beginidx + idx_diff + subLen]))
                    refine_distance[beginidx:idx - 1] = sqrt(abs(2 * (subLen - (
                                dotproduct[beginidx:idx - 1] - subLen * dataMu[beginidx:idx - 1].dot(
                            dataMu[beginidx + idx_diff:idx_nn - 1])) / (dataSig[beginidx:idx - 1].dot(
                        dataSig[beginidx + idx_diff:idx_nn - 1])))))
                    update_pos1 = find(refine_distance[beginidx:endidx] < matrixProfile[beginidx:endidx])
                    matrixProfile[update_pos1 + beginidx - 1] = refine_distance[update_pos1 + beginidx - 1]
                    profileIndex[update_pos1 + beginidx - 1] = orig_index[update_pos1 + beginidx - 1] + idx_diff
                    update_pos2 = find(
                        refine_distance[beginidx:endidx] < matrixProfile[beginidx + idx_diff:endidx + idx_diff])
                    matrixProfile[update_pos2 + beginidx + idx_diff - 1] = refine_distance[update_pos2 + beginidx - 1]
                    profileIndex[update_pos2 + beginidx + idx_diff - 1] = orig_index[
                                                                              update_pos2 + beginidx + idx_diff - 1] - idx_diff
        if toc_(timer) < updatePeriod and i != iterationEnd:
            continue
        if exist_('prefilePlot', 'var'):
            delete_(prefilePlot)
        hold_(mainWindow.profileAx, 'on')
        prefilePlot = plot_(arange(1, proLen), matrixProfile, 'b', 'parent', mainWindow.profileAx)
        hold_(mainWindow.profileAx, 'off')
        if exist_('motifMarkPlot', 'var'):
            for j in arange(1, 2).reshape(-1):
                delete_(motifMarkPlot[j])
        if exist_('discordPlot', 'var'):
            for j in arange(1, length(discordPlot)).reshape(-1):
                delete_(discordPlot[j])
        if exist_('motifPlot', 'var'):
            for j in arange(1, 3).reshape(-1):
                for k in arange(1, 2).reshape(-1):
                    for l in arange(1, length(motifPlot[j, k])).reshape(-1):
                        delete_(motifPlot[j, k](l))
        mainWindow = get_(mainWindow.fig, 'userdata')
        discardIdx = mainWindow.discardIdx
        matrixProfileCur = copy(matrixProfile)
        for j in arange(1, length(discardIdx)).reshape(-1):
            discardZoneStart = max(1, discardIdx[j] - excZoneLen)
            discardZoneEnd = min(proLen, discardIdx[j] + excZoneLen)
            matrixProfileCur[discardZoneStart:discardZoneEnd] = inf
            matrixProfileCur[abs(profileIndex - discardIdx[j]) < excZoneLen] = inf
        motifIdxs, matrixProfileCur = findMotifs_(matrixProfileCur, profileIndex, dataLen, subLen, proLen, data,
                                                  dataFreq, dataMu, dataSig, isSkip, excZoneLen, radius, nargout=2)
        motifMarkPlot = zeros(2, 1)
        for j in arange(1, 2).reshape(-1):
            motifPos = arange(motifIdxs[1, 1](j), motifIdxs[1, 1](j) + subLen - 1)
            hold_(mainWindow.dataAx, 'on')
            motifMarkPlot[j] = plot_(motifPos, dataPlot[motifPos], motifColor[j], 'parent', mainWindow.dataAx)
            hold_(mainWindow.dataAx, 'off')
        motifPlot = cell(3, 2)
        for j in arange(1, 3).reshape(-1):
            motifPlot[j, 2] = zeros(length(motifIdxs[j, 2]), 1)
            for k in arange(1, length(motifIdxs[j, 2])).reshape(-1):
                neighborPos = arange(motifIdxs[j, 2](k), motifIdxs[j, 2](k) + subLen - 1)
                hold_(mainWindow.motifAx(j), 'on')
                motifPlot[j, 2][k] = plot_(arange(1, subLen), zeroOneNorm_(dataPlot[neighborPos]), 'color',
                                           neighborColor, 'linewidth', 2, 'parent', mainWindow.motifAx(j))
                hold_(mainWindow.motifAx(j), 'off')
        for j in arange(1, 3).reshape(-1):
            motifPlot[j, 1] = zeros(2, 1)
            for k in arange(1, 2).reshape(-1):
                motifPos = arange(motifIdxs[j, 1](k), motifIdxs[j, 1](k) + subLen - 1)
                hold_(mainWindow.motifAx(j), 'on')
                set_(mainWindow.motifText(j), 'string', sprintf_(txtTemp[j], motifIdxs[j, 1](1), motifIdxs[j, 1](2)))
                motifPlot[j, 1][k] = plot_(arange(1, subLen), zeroOneNorm_(dataPlot[motifPos]), motifColor[k], 'parent',
                                           mainWindow.motifAx(j))
                hold_(mainWindow.motifAx(j), 'off')
        matrixProfileCur[isinf(matrixProfileCur)] = - inf
        __, profileIdxOrder = sort(matrixProfileCur, 'descend', nargout=2)
        discordIdx = zeros(3, 1)
        for j in arange(1, 3).reshape(-1):
            if length(profileIdxOrder) < j:
                break
            discordIdx[j] = profileIdxOrder[1]
            profileIdxOrder[1] = []
            profileIdxOrder[abs(profileIdxOrder - discordIdx[j]) < excZoneLen] = []
        discordIdx[discordIdx == 0] = nan
        discordPlot = zeros(sum(not isnan(discordIdx)), 1)
        for j in arange(1, 3).reshape(-1):
            if isnan(discordIdx[j]):
                break
            discordPos = arange(discordIdx[j], discordIdx[j] + subLen - 1)
            hold_(mainWindow.discordAx, 'on')
            discordPlot[j] = plot_(arange(1, subLen), zeroOneNorm_(dataPlot[discordPos]), discordColor[j], 'parent',
                                   mainWindow.discordAx)
            hold_(mainWindow.discordAx, 'off')
        if anytimeMode == 3:
            if curStage == 1:
                set_(mainWindow.dataText, 'string', sprintf_(['PreSCRIMP %.1f%% done: The input time series: ',
                                                              'The best-so-far motifs are color coded (see bottom panel)'],
                                                             i * 100 / length(PreidxOrder)))
            else:
                if curStage == 2:
                    set_(mainWindow.dataText, 'string', sprintf_(['SCRIMP %.1f%% done: The input time series: ',
                                                                  'The best-so-far motifs are color coded (see bottom panel)'],
                                                                 (i - length(PreidxOrder)) * 100 / length(idxOrder)))
        else:
            set_(mainWindow.dataText, 'string', sprintf_(['We are %.1f%% done: The input time series: ',
                                                          'The best-so-far motifs are color coded (see bottom panel)'],
                                                         i * 100 / length(idxOrder)))
        set_(mainWindow.discordText, 'string',
             sprintf_(['The top three discords ', '%d(blue), %d(red), %d(green)'], discordIdx[1], discordIdx[2],
                      discordIdx[3]))
        if firstUpdate:
            set_(mainWindow.fig, 'userdata', mainWindow)
            set_(mainWindow.fig, 'visible', 'on')
            firstUpdate = copy(False)
        mainWindow = get_(mainWindow.fig, 'userdata')
        mainWindow.motifIdxs = motifIdxs
        set_(mainWindow.fig, 'userdata', mainWindow)
        if i == iterationEnd:
            set_(mainWindow.fig, 'name', [titleTxt, ' (Completed)'])
        else:
            if mainWindow.stopping:
                set_(mainWindow.fig, 'name', [titleTxt, ' (Stopped)'])
        if i == iterationEnd or mainWindow.stopping:
            for j in arange(1, 3).reshape(-1):
                set_(mainWindow.discardBtn(j), 'enable', 'off')
            set_(mainWindow.stopBtn, 'enable', 'off')
            return matrixProfile, profileIndex, motifIdxs, discordIdx
        for j in arange(1, 3).reshape(-1):
            set_(mainWindow.discardBtn(j), 'enable', 'on')
        timer = tic_()
    return matrixProfile, profileIndex, motifIdxs, discordIdx
