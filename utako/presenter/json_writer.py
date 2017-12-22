#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class JsonWriter:
    def __call__(
        self,
        data,
        fp,
        coding = 'utf-8',
        indent = False,
        compress = True
    ):
        with codecs.open(fp, 'w', coding) as fobj:
            if indent and compress:
                json.dump(self._float_compressor(data), fobj, ensure_ascii = False, indent = 2)
            elif indent:
                json.dump(data, fobj, ensure_ascii = False, indent = 2)
            elif compress:
                json.dump(self._float_compressor(data), fobj, ensure_ascii = False)
            else:
                json.dump(data, fobj, ensure_ascii = False)

    def _float_compressor(self, obj):
        if isinstance(obj, float):
            return round(obj,2)
            # return CompressedFloat(obj)
        elif isinstance(obj, dict):
            return dict((k, self._float_compressor(v)) for k, v in obj.items())
        elif isinstance(obj,(list,tuple)):
            return list(map(self._float_compressor, obj))
        else:
            return obj

