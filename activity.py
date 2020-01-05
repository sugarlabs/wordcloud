# -*- coding: utf-8 -*-

# Copyright 2014 Walter Bender
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import logging
import subprocess

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import GObject

from gettext import gettext as _

from sugar3.graphics.palettemenu import PaletteMenuItem
from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics.palettemenu import PaletteMenuBox
from sugar3.graphics.toolbarbox import ToolbarButton
from sugar3.activity.widgets import EditToolbar
from sugar3.activity.widgets import StopButton
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.toggletoolbutton import ToggleToolButton
from sugar3.graphics import style
from sugar3.datastore import datastore
from sugar3.graphics.alert import NotifyAlert
from sugar3 import profile

from pytagcloud import (FONT_CACHE, LAYOUT_HORIZONTAL, LAYOUT_VERTICAL,
                        LAYOUT_MIX, LAYOUT_FORTYFIVE, LAYOUT_RANDOM)
from pytagcloud.colors import COLOR_SCHEMES

LAYOUT_SCHEMES = {'horizontal': LAYOUT_HORIZONTAL,
                  'vertical': LAYOUT_VERTICAL,
                  'mix': LAYOUT_MIX,
                  'fortyfive': LAYOUT_FORTYFIVE,
                  'random': LAYOUT_RANDOM}

_TEXT = _('Type your text here and then click on the start button. '
          'Your word cloud will be saved to the Journal.')

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


def _hex(color):
    ''' created a #RRGGBB from a (r, g, b) color '''
    return '#%02x%02x%02x' % (color)


def _rgb(color):
    ''' extracts (r, g, b) from Sugar color'''
    return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))


def _color_icon(colors, selected=False):
    ''' returns a pixbuf for a color icon '''
    svg = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' \
          '<svg\n' \
          'xmlns:dc="http://purl.org/dc/elements/1.1/"\n' \
          'xmlns:cc="http://creativecommons.org/ns#"\n' \
          'version="1.1"\n' \
          'width="55"\n' \
          'height="55">\n'

    svg += '<rect\n' \
        'width="9"\n' \
        'height="45"\n' \
        'x="5"\n' \
        'y="5"\n' \
        'style="fill:%s;fill-opacity:1;fill-rule:nonzero;stroke:none" />\n' \
        '<rect\n' \
        'width="9"\n' \
        'height="45"\n' \
        'x="14"\n' \
        'y="5"\n' \
        'style="fill:%s;fill-opacity:1;fill-rule:nonzero;stroke:none" />\n' \
        '<rect\n' \
        'width="9"\n' \
        'height="45"\n' \
        'x="23"\n' \
        'y="5"\n' \
        'style="fill:%s;fill-opacity:1;fill-rule:nonzero;stroke:none" />\n' \
        '<rect\n' \
        'width="9"\n' \
        'height="45"\n' \
        'x="32"\n' \
        'y="5"\n' \
        'style="fill:%s;fill-opacity:1;fill-rule:nonzero;stroke:none" />\n' \
        '<rect\n' \
        'width="9"\n' \
        'height="55"\n' \
        'x="41"\n' \
        'y="5"\n' \
        'style="fill:%s;fill-opacity:1;fill-rule:nonzero;stroke:none" />\n' \
        % (_hex(colors[0]), _hex(colors[1]), _hex(colors[2]), _hex(colors[3]),
           _hex(colors[4]))
    svg += '<rect\n' \
           'width="50"\n' \
           'height="50"\n' \
           'ry="0"\n' \
           'x="2.5"\n' \
           'y="2.5"\n' \
           'style="stroke-width:5;stroke:#282828;fill:none" />\n'
    if selected:
        svg += '<rect\n' \
               'width="50"\n' \
               'height="50"\n' \
               'ry="5"\n' \
               'x="2.5"\n' \
               'y="2.5"\n' \
               'style="stroke-width:5;stroke:#a0a0a0;fill:none" />\n'
    svg += '</svg>'

    pixbuf = svg_str_to_pixbuf(svg)
    return pixbuf


def svg_str_to_pixbuf(string):
    ''' Load pixbuf from SVG string '''
    pl = GdkPixbuf.PixbufLoader.new_with_type('svg')
    pl.write(string.encode())
    pl.close()
    pixbuf = pl.get_pixbuf()
    return pixbuf


class WordCloudActivity(activity.Activity):

    def __init__(self, handle):
        """Set up the HelloWorld activity."""
        activity.Activity.__init__(self, handle)

        self.connect('realize', self.__realize_cb)

        self.max_participants = 1  # No sharing

        self._font_name = None
        self._layout = LAYOUT_RANDOM
        self._xo_colors = (_rgb(profile.get_color().to_string().split(',')[0]),
                           _rgb(profile.get_color().to_string().split(',')[1]))
        self._color_scheme = self._xo_colors
        self._repeat_tags = False

        self._toolbox = ToolbarBox()

        self.activity_button = ActivityToolbarButton(self)
        self._toolbox.toolbar.insert(self.activity_button, 0)
        self.activity_button.show()

        self.set_toolbar_box(self._toolbox)
        self._toolbox.show()
        self.toolbar = self._toolbox.toolbar

        self._edit_toolbar = EditToolbar()
        button = ToolbarButton()
        button.set_page(self._edit_toolbar)
        button.props.icon_name = 'toolbar-edit'
        button.props.label = _('Edit')
        self._toolbox.toolbar.insert(button, -1)
        button.show()
        self._edit_toolbar.show()

        # self._edit_toolbar.undo.connect('clicked', self._undo_cb)
        # self._edit_toolbar.redo.connect('clicked', self._redo_cb)
        self._edit_toolbar.undo.hide()
        self._edit_toolbar.redo.hide()
        self._edit_toolbar.copy.connect('clicked', self._copy_cb)
        self._edit_toolbar.paste.connect('clicked', self._paste_cb)

        go_button = ToolButton('generate-cloud')
        self._toolbox.toolbar.insert(go_button, -1)
        go_button.set_tooltip(_('Create the cloud'))
        go_button.show()
        go_button.connect('clicked', self._go_cb)

        self._text_item = TextItem(self)
        self._toolbox.toolbar.insert(self._text_item, -1)
        self._text_item.show()
        text = self._read_metadata('text')
        if text is not None:
            self._text_item.set_text(text)

        self._repeat_button = ToggleToolButton('repeat-cloud')
        self._toolbox.toolbar.insert(self._repeat_button, -1)
        self._repeat_button.set_tooltip(_('Repeat words'))
        self._repeat_button.show()
        self._repeat_button.connect('clicked', self._repeat_cb)

        self.font_palette_content, self.font_palette_dict = \
            set_palette_list(
                self._setup_font_palette(), 3, 7,
                style.SMALL_ICON_SIZE + style.DEFAULT_SPACING +
                style.DEFAULT_PADDING, return_dict=True)
        self._font_button = FontToolItem(self)
        self.font_palette_content.show()
        self._toolbox.toolbar.insert(self._font_button, -1)
        self._font_button.show()

        self.color_palette_content, self.color_palette_dict = \
            set_palette_list(
                self._setup_color_palette(), 3, 5,
                style.GRID_CELL_SIZE + style.DEFAULT_SPACING +
                style.DEFAULT_PADDING, return_dict=True)
        self._color_button = ColorToolItem(self)
        self.color_palette_content.show()
        self._toolbox.toolbar.insert(self._color_button, -1)
        self._color_button.show()

        self.layout_palette_content, self.layout_palette_dict = \
            set_palette_list(self._setup_layout_palette(), 1, 5,
                             style.GRID_CELL_SIZE + style.DEFAULT_SPACING +
                             style.DEFAULT_PADDING, return_dict=True)
        self._layout_button = LayoutToolItem(self)
        self.layout_palette_content.show()
        self._toolbox.toolbar.insert(self._layout_button, -1)
        self._layout_button.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        self._toolbox.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        stop_button.props.accelerator = '<Ctrl>q'
        self._toolbox.toolbar.insert(stop_button, -1)
        stop_button.show()

        self._show_image(os.path.join(
            activity.get_bundle_path(), 'WordCloud.png'))

        self._set_color('XO')
        self._set_font('Droid Sans')

        for layout in list(LAYOUT_SCHEMES.keys()):
            if LAYOUT_SCHEMES[layout] == self._layout:
                self._set_layout(layout)
                break

    def _read_metadata(self, keyword, default_value=None):
        ''' If the keyword is found, return stored value '''
        if keyword in self.metadata:
            return(self.metadata[keyword])
        else:
            return(default_value)

    def write_file(self, file_path):
        self.metadata['text'] = self._text_item.get_text_from_buffer()

    def _show_image(self, path):
        if Gdk.Screen.height() < Gdk.Screen.width():
            height = Gdk.Screen.height() - style.GRID_CELL_SIZE
            width = int(height * 4 / 3)
        else:
            width = Gdk.Screen.width()
            height = int(width * 3 / 4)

        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
            path, width, height)

        image = Gtk.Image()
        image.set_from_pixbuf(pixbuf)

        align = Gtk.Alignment.new(xalign=0.5, yalign=0.5, xscale=1.0,
                                  yscale=1.0)
        align.add(image)
        image.show()
        evbox = Gtk.EventBox()
        evbox.set_size_request(Gdk.Screen.width(),
                               Gdk.Screen.height() - style.GRID_CELL_SIZE)
        evbox.modify_bg(
            Gtk.StateType.NORMAL, style.COLOR_WHITE.get_gdk_color())
        evbox.add(align)
        align.show()
        self.set_canvas(evbox)
        evbox.show()

    def __realize_cb(self, window):
        self.window_xid = window.get_window().get_xid()

    def _repeat_cb(self, widget):
        self._repeat_tags = not self._repeat_tags

    def _go_cb(self, widget):
        self._text_item.set_expanded(False)
        text = self._text_item.get_text_from_buffer()
        if len(text) > 0:
            self.get_window().set_cursor(Gdk.Cursor.new(Gdk.CursorType.WATCH))

            GObject.idle_add(self._create_image, text)

    def _create_image(self, text):
        fd = open('/tmp/cloud_data.txt', 'w')
        data = json_dump({'repeat': self._repeat_tags,
                          'layout': self._layout,
                          'font': self._font_name,
                          'colors': self._color_scheme})
        fd.write(data)
        fd.close()
        fd = open('/tmp/cloud_text.txt', 'w')
        fd.write(text)
        fd.close()
        path = os.path.join('/tmp/cloud_large.png')
        try:
            subprocess.check_call(
                [os.path.join(activity.get_bundle_path(), 'wordcloud.py')])
        except subprocess.CalledProcessError as e:
            self.get_window().set_cursor(
                Gdk.Cursor.new(Gdk.CursorType.LEFT_PTR))
            alert = NotifyAlert(5)
            alert.props.title = _('WordCloud error')
            logging.error(e)
            logging.error(e.returncode)
            if e.returncode == 255:
                logging.error('STOP WORD ERROR')
                MESSAGE = _('All of your words are "stop words."'
                            ' Please try adding more words.')
            else:
                logging.error('MEMORY ERROR')
                MESSAGE = _('Oops. There was a problem. Please try again.')
            alert.props.msg = MESSAGE
            alert.connect('response', self._remove_alert_cb)
            self.add_alert(alert)
            return

        self.get_window().set_cursor(Gdk.Cursor.new(Gdk.CursorType.LEFT_PTR))

        self._show_image(path)

        dsobject = datastore.create()
        dsobject.metadata['title'] = _('Word Cloud')
        dsobject.metadata['icon-color'] = profile.get_color().to_string()
        dsobject.metadata['mime_type'] = 'image/png'
        dsobject.set_file_path(path)
        datastore.write(dsobject)
        dsobject.destroy()

    def _remove_alert_cb(self, alert, response_id):
        self.remove_alert(alert)

    def _undo_cb(self, butston):
        text_buffer = self._text_item.get_text_buffer()
        if text_buffer.can_undo():
            text_buffer.undo()

    def _redo_cb(self, button):
        text_buffer = self._text_item.get_text_buffer()
        if text_buffer.can_redo():
            text_buffer.redo()

    def _copy_cb(self, button):
        text_buffer = self._text_item.get_text_buffer()
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        text_buffer.copy_clipboard(clipboard)

    def _paste_cb(self, button):
        text_buffer = self._text_item.get_text_buffer()
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        text_buffer.paste_clipboard(
            clipboard, None, True)

    def _init_font_list(self):
        self._font_list = []
        for f in FONT_CACHE:
            self._font_list.append(f['name'])
        return

    def _setup_font_palette(self):
        self._init_font_list()

        palette_list = []
        for font in sorted(self._font_list):
            palette_list.append({'icon': FontImage(font.replace(' ', '-')),
                                 'selected': FontImage(font.replace(' ', '-'),
                                                       selected=True),
                                 'callback': self.__font_selected_cb,
                                 'label': font})
        return palette_list

    def __font_selected_cb(self, widget, event, font_name):
        self._font_name = font_name
        self._set_font(font_name)
        return

    def _set_font(self, font):
        for entry in list(self.font_palette_dict.keys()):
            if entry == font:
                self.font_palette_dict[entry]['icon'].hide()
                self.font_palette_dict[entry]['selected'].show()
            else:
                self.font_palette_dict[entry]['icon'].show()
                self.font_palette_dict[entry]['selected'].hide()

    def _setup_color_palette(self):
        palette_list = []
        palette_list.append({'icon': ColorImage('xo'),
                             'selected': ColorImage('xo', selected=True),
                             'callback': self.__color_selected_cb,
                             'label': 'XO'})
        for color in list(COLOR_SCHEMES.keys()):
            palette_list.append({'icon': ColorIcon(COLOR_SCHEMES[color]),
                                 'selected': ColorIcon(
                                     COLOR_SCHEMES[color], selected=True),
                                 'callback': self.__color_selected_cb,
                                 'label': color})
        palette_list.append({'icon': ColorImage('random'),
                             'selected': ColorImage('random', selected=True),
                             'callback': self.__color_selected_cb,
                             'label': _('random')})

        return palette_list

    def __color_selected_cb(self, widget, event, color):
        self._set_color(color)
        if color == _('random'):
            self._color_scheme = None
        elif color == 'XO':
            self._color_scheme = self._xo_colors
        else:
            self._color_scheme = COLOR_SCHEMES[color]
        return

    def _set_color(self, color):
        for entry in list(self.color_palette_dict.keys()):
            if entry == color:
                self.color_palette_dict[entry]['icon'].hide()
                self.color_palette_dict[entry]['selected'].show()
            else:
                self.color_palette_dict[entry]['icon'].show()
                self.color_palette_dict[entry]['selected'].hide()

    def _setup_layout_palette(self):
        palette_list = []
        for layout in list(LAYOUT_SCHEMES.keys()):
            palette_list.append({'icon': LayoutImage(layout),
                                 'selected': LayoutImage(layout,
                                                         selected=True),
                                 'callback': self.__layout_selected_cb,
                                 'label': layout})
        return palette_list

    def __layout_selected_cb(self, widget, event, layout):
        self._set_layout(layout)
        self._layout = LAYOUT_SCHEMES[layout]

    def _set_layout(self, layout):
        for entry in list(self.layout_palette_dict.keys()):
            if entry == layout:
                self.layout_palette_dict[entry]['icon'].hide()
                self.layout_palette_dict[entry]['selected'].show()
            else:
                self.layout_palette_dict[entry]['icon'].show()
                self.layout_palette_dict[entry]['selected'].hide()


class TextItem(ToolButton):

    def __init__(self, activity, **kwargs):
        ToolButton.__init__(self, 'edit-cloud', **kwargs)
        self.set_tooltip(_('Cloud Text'))
        self.palette_invoker.props.toggle_palette = True
        self.palette_invoker.props.lock_palette = True
        self.props.hide_tooltip_on_click = False
        self._palette = self.get_palette()

        description_box = PaletteMenuBox()

        sw = Gtk.ScrolledWindow()
        sw.set_size_request(int(Gdk.Screen.width() / 3),
                            5 * style.GRID_CELL_SIZE)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self._text_view = Gtk.TextView()
        self._text_view.set_left_margin(style.DEFAULT_PADDING)
        self._text_view.set_right_margin(style.DEFAULT_PADDING)
        self._text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._text_buffer = Gtk.TextBuffer()
        self._text_buffer.set_text(_TEXT)
        self._text_view.set_buffer(self._text_buffer)
        self._text_view.connect('focus-in-event', self._text_focus_in_cb)
        sw.add(self._text_view)

        description_box.append_item(sw, vertical_padding=0)
        self._palette.set_content(description_box)
        description_box.show_all()

        self.set_expanded(True)

    def get_toolbar_box(self):
        parent = self.get_parent()
        if not hasattr(parent, 'owner'):
            return None
        return parent.owner

    toolbar_box = property(get_toolbar_box)

    def set_expanded(self, expanded):
        box = self.toolbar_box
        if not box:
            return

        if not expanded:
            self.palette_invoker.notify_popdown()
            return

        if box.expanded_button is not None:
            box.expanded_button.queue_draw()
            if box.expanded_button != self:
                box.expanded_button.set_expanded(False)
        box.expanded_button = self

    def get_text_buffer(self):
        return self._text_view.get_buffer()

    def set_text(self, text):
        self._text_buffer.set_text(text)

    def get_text_from_buffer(self):
        buf = self._text_view.get_buffer()
        start_iter = buf.get_start_iter()
        end_iter = buf.get_end_iter()
        return buf.get_text(start_iter, end_iter, False)

    def _text_focus_in_cb(self, widget, event):
        bounds = self._text_buffer.get_bounds()
        text = self._text_buffer.get_text(bounds[0], bounds[1], True)
        if text == _TEXT:
            self._text_buffer.set_text('')


class FontImage(Gtk.Image):

    def __init__(self, font_name, selected=False):
        super(Gtk.Image, self).__init__()

        if selected:
            path = os.path.join(
                activity.get_bundle_path(), 'pytagcloud', 'fonts',
                font_name.replace(' ', '-') + '-selected.png')
        else:
            path = os.path.join(
                activity.get_bundle_path(), 'pytagcloud', 'fonts',
                font_name.replace(' ', '-') + '.png')
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
            path, style.SMALL_ICON_SIZE, style.SMALL_ICON_SIZE)
        self.set_from_pixbuf(pixbuf)
        self.show()


class ColorImage(Gtk.Image):

    def __init__(self, color_name, selected=False):
        super(Gtk.Image, self).__init__()

        if selected:
            path = os.path.join(activity.get_bundle_path(), 'colors',
                                color_name + '-selected.png')
        else:
            path = os.path.join(activity.get_bundle_path(), 'colors',
                                color_name + '.png')
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
            path, style.GRID_CELL_SIZE, style.GRID_CELL_SIZE)
        self.set_from_pixbuf(pixbuf)
        self.show()


class ColorIcon(Gtk.Image):

    def __init__(self, colors, selected=False):
        super(Gtk.Image, self).__init__()

        pixbuf = _color_icon(colors, selected=selected)
        self.set_from_pixbuf(pixbuf)
        self.show()


class LayoutImage(Gtk.Image):

    def __init__(self, layout_name, selected=False):
        super(Gtk.Image, self).__init__()

        if selected:
            path = os.path.join(activity.get_bundle_path(), 'layouts',
                                'format-' + layout_name + '-selected.png')
        else:
            path = os.path.join(activity.get_bundle_path(), 'layouts',
                                'format-' + layout_name + '.png')
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
            path, style.GRID_CELL_SIZE, style.GRID_CELL_SIZE)
        self.set_from_pixbuf(pixbuf)
        self.show()


class LayoutToolItem(ToolButton):

    def __init__(self, activity, **kwargs):
        ToolButton.__init__(self, 'format-cloud-4', **kwargs)
        self.set_tooltip(_('Select layout'))
        self.palette_invoker.props.toggle_palette = True
        self.palette_invoker.props.lock_palette = True
        self.props.hide_tooltip_on_click = False
        self._palette = self.get_palette()

        layout_box = PaletteMenuBox()

        layout_box.append_item(activity.layout_palette_content,
                               vertical_padding=0)
        self._palette.set_content(layout_box)
        layout_box.show_all()

        self.set_expanded(True)

    def get_toolbar_box(self):
        parent = self.get_parent()
        if not hasattr(parent, 'owner'):
            return None
        return parent.owner

    toolbar_box = property(get_toolbar_box)

    def set_expanded(self, expanded):
        box = self.toolbar_box
        if not box:
            return

        if not expanded:
            self.palette_invoker.notify_popdown()
            return

        if box.expanded_button is not None:
            box.expanded_button.queue_draw()
            if box.expanded_button != self:
                box.expanded_button.set_expanded(False)
        box.expanded_button = self


class ColorToolItem(ToolButton):

    def __init__(self, activity, **kwargs):
        ToolButton.__init__(self, 'color-cloud', **kwargs)
        self.set_tooltip(_('Select color scheme'))
        self.palette_invoker.props.toggle_palette = True
        self.palette_invoker.props.lock_palette = True
        self.props.hide_tooltip_on_click = False
        self._palette = self.get_palette()

        color_box = PaletteMenuBox()

        color_box.append_item(activity.color_palette_content,
                              vertical_padding=0)
        self._palette.set_content(color_box)
        color_box.show_all()

        self.set_expanded(True)

    def get_toolbar_box(self):
        parent = self.get_parent()
        if not hasattr(parent, 'owner'):
            return None
        return parent.owner

    toolbar_box = property(get_toolbar_box)

    def set_expanded(self, expanded):
        box = self.toolbar_box
        if not box:
            return

        if not expanded:
            self.palette_invoker.notify_popdown()
            return

        if box.expanded_button is not None:
            box.expanded_button.queue_draw()
            if box.expanded_button != self:
                box.expanded_button.set_expanded(False)
        box.expanded_button = self


class FontToolItem(ToolButton):

    def __init__(self, activity, **kwargs):
        ToolButton.__init__(self, 'font-text', **kwargs)
        self.set_tooltip(_('Select font'))
        self.palette_invoker.props.toggle_palette = True
        self.palette_invoker.props.lock_palette = True
        self.props.hide_tooltip_on_click = False
        self._palette = self.get_palette()

        font_box = PaletteMenuBox()

        font_box.append_item(activity.font_palette_content,
                             vertical_padding=0)
        self._palette.set_content(font_box)
        font_box.show_all()

        self.set_expanded(True)

    def get_toolbar_box(self):
        parent = self.get_parent()
        if not hasattr(parent, 'owner'):
            return None
        return parent.owner

    toolbar_box = property(get_toolbar_box)

    def set_expanded(self, expanded):
        box = self.toolbar_box
        if not box:
            return

        if not expanded:
            self.palette_invoker.notify_popdown()
            return

        if box.expanded_button is not None:
            box.expanded_button.queue_draw()
            if box.expanded_button != self:
                box.expanded_button.set_expanded(False)
        box.expanded_button = self


def set_palette_list(palette_list, nx, ny, item_height, return_dict=False):
    palette_dict = {}
    item_width = style.GRID_CELL_SIZE * 3

    grid = Gtk.Grid()
    grid.set_row_spacing(style.DEFAULT_PADDING)
    grid.set_column_spacing(0)
    grid.set_border_width(0)

    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrolled_window.set_size_request(nx * item_width, ny * item_height)
    scrolled_window.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
    scrolled_window.add_with_viewport(grid)
    grid.show()

    x = 0
    y = 0

    for item in palette_list:
        menu_item = PaletteMenuItem()
        menu_item.set_label(item['label'])
        menu_item.set_image(item['icon'])
        item['icon'].show()
        if return_dict:
            menu_item.set_image(item['selected'])
            item['selected'].hide()

        if return_dict:
            palette_dict[item['label']] = {'menu': menu_item,
                                           'icon': item['icon'],
                                           'selected': item['selected']}

        menu_item.connect('button-release-event', item['callback'],
                          item['label'])
        grid.attach(menu_item, x, y, 1, 1)
        x += 1
        if x == nx:
            x = 0
            y += 1

        menu_item.show()

    if return_dict:
        return scrolled_window, palette_dict
    else:
        return scrolled_window
