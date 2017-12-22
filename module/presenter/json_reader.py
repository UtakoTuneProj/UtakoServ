#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class JsonReader:
    #self.path:ファイルパスを保存
    #self.encoding:エンコードを保存
    #self.data:データを保存
    #
    #self.read():self.pathのファイルから読み込む関数
    #self.write(indent):self.dataを書き込む関数
    def __init__(self, path, encoding = 'utf-8'):
        self.path = path
        self.encoding = encoding
        self.data = self.read()
    def read(self):
        fobj = codecs.open(self.path,'r',self.encoding)
        stream = json.load(fobj, encoding = self.encoding)
        fobj.close()
        return stream
    def write(self, indent = False, compress = True):
        fobj= codecs.open(self.path,'w',self.encoding)
        if indent and compress:
            json.dump(float_compressor(self.data), fobj, ensure_ascii = False, indent = 2)
        elif indent:
            json.dump(self.data, fobj, ensure_ascii = False, indent = 2)
        elif compress:
            json.dump(float_compressor(self.data), fobj, ensure_ascii = False)
        else:
            json.dump(self.data, fobj, ensure_ascii = False)

        fobj.close()
        return None

