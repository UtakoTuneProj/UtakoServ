#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class MovDeletedException(Exception):
    def __init__(self,e):
        Exception.__init__(self,e)

