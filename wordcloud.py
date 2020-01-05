#!/usr/bin/python
# wordclound.py
"""
    Copyright (C) 2014 Walter Bender

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

"""

from pytagcloud import create_tag_image, make_tags, LAYOUT_MIX
from pytagcloud.lang.counter import get_tag_counts

import sys
import os
import gi

gi.require_version('Gdk', '3.0')

from gi.repository import Gdk

from io import StringIO

import json
json.dumps
from json import load as jload
from json import dump as jdump


def json_load(text):
    """ Load JSON data using what ever resources are available. """
    # strip out leading and trailing whitespace, nulls, and newlines
    io = StringIO(text)
    try:
        listdata = jload(io)
    except ValueError:
        # assume that text is ascii list
        listdata = text.split()
        for i, value in enumerate(listdata):
            listdata[i] = int(value)
    return listdata


def json_dump(data):
    """ Save data using available JSON tools. """
    _io = StringIO()
    jdump(data, _io)
    return _io.getvalue()


class WordCloud():

    def __init__(self):
        try:
            fd = open('/tmp/cloud_data.txt', 'r')
            data = fd.read()
            fd.close()
            cloud_dict = json_load(data)
            self._repeat_tags = cloud_dict['repeat']
            self._layout = cloud_dict['layout']
            self._font_name = cloud_dict['font']
            self._color_scheme = cloud_dict['colors']
        except:
            self._repeat_tags = False
            self._layout = LAYOUT_MIX
            self._font_name = None
            self._color_scheme = ((241, 143, 0), (128, 186, 39),
                                  (13, 147, 210), (231, 30, 108),
                                  (135, 135, 135))
        try:
            fd = open('/tmp/cloud_text.txt', 'r')
            self._text = fd.read()
            fd.close()
        except:
            self._text = 'Could not read cloud_text'

    def run(self):
        self._create_image(self._text)

    def _create_image(self, text):
        tag_counts = get_tag_counts(text)
        if tag_counts is None:
            sys.exit(-1)

        if self._repeat_tags:
            expanded_tag_counts = []
            for tag in tag_counts:
                expanded_tag_counts.append((tag[0], 5))
            for tag in tag_counts:
                expanded_tag_counts.append((tag[0], 2))
            for tag in tag_counts:
                expanded_tag_counts.append((tag[0], 1))
            tag_counts = expanded_tag_counts

        tags = make_tags(tag_counts, maxsize=150, colors=self._color_scheme)
        path = os.path.join('/tmp/cloud_large.png')

        if Gdk.Screen.height() < Gdk.Screen.width():
            height = Gdk.Screen.height()
            width = int(height * 4 / 3)
        else:
            width = Gdk.Screen.width()
            height = int(width * 3 / 4)

        if self._font_name is not None:
            create_tag_image(tags, path, layout=self._layout,
                             size=(width, height),
                             fontname=self._font_name)
        else:
            create_tag_image(tags, path, layout=self._layout,
                             size=(width, height))
        return 0


if __name__ == "__main__":
    game = WordCloud()
    game.run()
    sys.exit(0)
