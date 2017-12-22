#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# from http://aidiary.hatenablog.com/entry/20121014/1350211413
import os
import sys

# mp3_to_mfcc.py
# usage: python mp3_to_mfcc.py [mp3dir] [mfccdir] [rawdir]
# ディレクトリ内のMP3ファイルからMFCCを抽出する

def mp3ToRaw(mp3File, rawFile):
    # mp3を16kHz, 32bitでリサンプリング
    os.system("lame --resample 16 -b 32 -a '%s' temp.mp3" % mp3File)
    # mp3をwavに変換
    os.system("lame --decode temp.mp3 temp.wav")
    # wavをrawに変換
    os.system("sox temp.wav %s" % rawFile)
    os.remove("temp.mp3")
    os.remove("temp.wav")

def calcNumSample(rawFile):
    # 1サンプルはshort型（2byte）なのでファイルサイズを2で割る
    filesize = os.path.getsize("temp.raw")
    numsample = filesize / 2
    return numsample

def extractCenter(inFile, outFile, period):
    # 波形のサンプル数を求める
    numsample = calcNumSample(inFile)

    fs = 16000
    center = numsample / 2
    start = center - fs * period
    end = center + fs * period
    
    # period*2秒未満の場合は範囲を狭める
    if start < 0: start = 0
    if end > numsample - 1: end = numsample - 1

    # SPTKのbcutコマンドで切り出す
    os.system("bcut +s -s %d -e %d < '%s' > '%s'" \
              % (start, end, "temp.raw", rawFile))

def calcMFCC(rawFile, mfccFile):
    # サンプリング周波数: 16kHz
    # フレーム長: 400サンプル
    # シフト幅  : 160サンプル
    # チャンネル数: 40
    # MFCC: 19次元 + エネルギー
    os.system("x2x +sf < '%s' | frame -l 400 -p 160 | mfcc -l 400 -f 16 -n 40 -m 19 -E > '%s'"
              % (rawFile, mfccFile))

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("usage: python mp3_to_mfcc.py [mp3dir] [mfccdir] [rawdir]")
        sys.exit()

    mp3Dir = sys.argv[1]
    mfccDir = sys.argv[2]
    rawDir = sys.argv[3]

    if not os.path.exists(mfccDir):
        os.mkdir(mfccDir)
    if not os.path.exists(rawDir):
        os.mkdir(rawDir)

    for file in os.listdir(mp3Dir):
        if not file.endswith(".mp3"): continue
        mp3File = os.path.join(mp3Dir, file)
        mfccFile = os.path.join(mfccDir, file.replace(".mp3", ".mfc"))
        rawFile = os.path.join(rawDir, file.replace(".mp3", ".raw"))

        try:
            # MP3を変換
            mp3ToRaw(mp3File, "temp.raw")
        
            # 中央の30秒だけ抽出してrawFileへ
            extractCenter("temp.raw", rawFile, 15)

            # MFCCを計算
            calcMFCC(rawFile, mfccFile)

            print("%s => %s" % (mp3File, mfccFile))

            # 後片付け
            os.remove("temp.raw")
        except:
            continue
