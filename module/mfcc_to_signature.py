#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# from http://aidiary.hatenablog.com/entry/20121014/1350211413
import os
import struct
import sys
import numpy as np
import scipy.cluster

# mfcc_to_signature.py
# usage: python mfcc_to_signature.py [mfccdir] [sigdir]
# 各曲のMFCCをシグネチャに変換する

def loadMFCC(mfccFile, m):
    """MFCCをロードする、mはMFCCの次元数"""
    mfcc = []
    fp = open(mfccFile, "rb")
    while True:
        b = fp.read(4)
        if b == "": break
        val = struct.unpack("f", b)[0]
        mfcc.append(val)
    fp.close()

    # 各行がフレームのMFCC
    # numFrame行、m列の行列形式に変換
    mfcc = np.array(mfcc)
    numFrame = len(mfcc) / m
    mfcc = mfcc.reshape(numFrame, m)

    return mfcc

def vq(mfcc, k):
    """mfccのベクトル集合をk個のクラスタにベクトル量子化"""
    codebook, destortion = scipy.cluster.vq.kmeans(mfcc, k)
    code, dist = scipy.cluster.vq.vq(mfcc, codebook)
    return code

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python mfcc_to_signature.py [mfccdir] [sigdir]")
        sys.exit()

    mfccDir = sys.argv[1]
    sigDir  = sys.argv[2]

    if not os.path.exists(sigDir):
        os.mkdir(sigDir)

    for file in os.listdir(mfccDir):
        if not file.endswith(".mfc"): continue
        mfccFile = os.path.join(mfccDir, file)
        sigFile = os.path.join(sigDir, file.replace(".mfc", ".sig"))

        print(mfccFile, "=>", sigFile)

        fout = open(sigFile, "w")

        # MFCCをロード
        # 各行がフレームのMFCCベクトル
        mfcc = loadMFCC(mfccFile, 20)

        # MFCCをベクトル量子化してコードを求める
        code = vq(mfcc, 16)

        # 各クラスタのデータ数、平均ベクトル、
        # 共分散行列を求めてシグネチャとする
        for k in range(16):
            # クラスタkのフレームのみ抽出
            frames = np.array([mfcc[i] for i in range(len(mfcc)) if code[i] == k])
            # MFCCの各次元の平均をとって平均ベクトルを求める
            m = np.apply_along_axis(np.mean, 0, frames)  # 0は縦方向
            # MFCCの各次元間での分散・共分散行列を求める
            sigma = np.cov(frames.T)
            # 重み（各クラスタのデータ数）
            w = len(frames)
            # このクラスタの特徴量をフラット形式で出力
            # 1行が重み1個、平均ベクトル20個、分散・共分散行列400個の計421個の数値列
            features = np.hstack((w, m, sigma.flatten()))
            features = [str(x) for x in features]
            fout.write(" ".join(features) + "\n")
        fout.close()
