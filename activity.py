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

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import GObject
from gi.repository import Pango

from gettext import gettext as _

from sugar3.graphics.palettemenu import PaletteMenuItem
from sugar3.graphics.palette import ToolInvoker
from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics.palettemenu import PaletteMenuBox
from sugar3.graphics.toolbarbox import ToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.menuitem import MenuItem
from sugar3.graphics.icon import Icon
from sugar3.graphics import style
from sugar3.graphics.xocolor import XoColor
from sugar3.graphics.palette import Palette
from sugar3.datastore import datastore
from sugar3 import profile
from sugar3 import env

from pytagcloud import create_tag_image, make_tags, load_font, FONT_CACHE
from pytagcloud.lang.counter import get_tag_counts

_TEXT = _('Type your text here and then click on the start button. '
          'Your word cloud will be saved to the Journal.')


class WordCloudActivity(activity.Activity):

    def __init__(self, handle):
        """Set up the HelloWorld activity."""
        activity.Activity.__init__(self, handle)

        self.connect('realize', self.__realize_cb)

        self.max_participants = 1  # No sharing
        self._font_name = None

        self._toolbox = ToolbarBox()

        self.activity_button = ActivityToolbarButton(self)
        self._toolbox.toolbar.insert(self.activity_button, 0)
        self.activity_button.show()

        self.set_toolbar_box(self._toolbox)
        self._toolbox.show()
        self.toolbar = self._toolbox.toolbar

        edit_toolbar = Gtk.Toolbar()
        self.edit_toolbar_button = ToolbarButton(
            page=edit_toolbar,
            label=_('Edit'),
            icon_name='toolbar-edit')
        self._toolbox.toolbar.insert(self.edit_toolbar_button, 1)
        edit_toolbar.show()
        self.edit_toolbar_button.show()

        self._copy_button = ToolButton('edit-copy')
        self._copy_button.set_tooltip(_('Copy'))
        self._copy_button.props.accelerator = '<Ctrl>C'
        edit_toolbar.insert(self._copy_button, -1)
        self._copy_button.show()
        self._copy_button.connect('clicked', self._copy_cb)
        self._copy_button.set_sensitive(True)

        self._paste_button = ToolButton('edit-paste')
        self._paste_button.set_tooltip(_('Paste'))
        self._paste_button.props.accelerator = '<Ctrl>V'
        edit_toolbar.insert(self._paste_button, -1)
        self._paste_button.show()
        self._paste_button.connect('clicked', self._paste_cb)
        self._paste_button.set_sensitive(False)

        self.font_palette_content = set_palette_list(
            self._setup_font_palette())
        self._font_button = FontToolItem(self)
        self.font_palette_content.show()
        self._toolbox.toolbar.insert(self._font_button, -1)
        self._font_button.show()
        
        self._text_item = TextItem(self)
        self._toolbox.toolbar.insert(self._text_item, -1)
        self._text_item.show()

        go_button = ToolButton('media-playback-start')
        self._toolbox.toolbar.insert(go_button, -1)
        go_button.set_tooltip(_('Create the cloud'))
        go_button.show()
        go_button.connect('clicked', self._go_cb)

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        self._toolbox.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        stop_button.props.accelerator = '<Ctrl>q'
        self._toolbox.toolbar.insert(stop_button, -1)
        stop_button.show()

        image = Gtk.Image.new_from_file(os.path.join(
            activity.get_bundle_path(), 'WordCloud.png'))
        self.set_canvas(image)
        image.show()

    def __realize_cb(self, window):
        self.window_xid = window.get_window().get_xid()

    def _go_cb(self, widget):
        self._text_item.set_expanded(False)
        text = self._text_item.get_text_from_buffer()
        if len(text) > 0:
            self.get_window().set_cursor(Gdk.Cursor.new(Gdk.CursorType.WATCH))

            GObject.idle_add(self._create_image, text)

    def _create_image(self, text):
        tags = make_tags(get_tag_counts(text), maxsize=150)
        path = os.path.join(activity.get_activity_root(), 'tmp',
                            'cloud_large.png')
        if self._font_name is not None:
            create_tag_image(tags, path,
                             size=(Gdk.Screen.width(), Gdk.Screen.height()),
                             fontname=self._font_name)
        else:
            create_tag_image(tags, path,
                             size=(Gdk.Screen.width(), Gdk.Screen.height()))
        self.get_window().set_cursor(Gdk.Cursor.new(Gdk.CursorType.LEFT_PTR))

        image = Gtk.Image.new_from_file(path)
        self.set_canvas(image)
        image.show()

        dsobject = datastore.create()
        dsobject.metadata['title'] = _('Word Cloud')
        dsobject.metadata['icon-color'] = profile.get_color().to_string()
        dsobject.metadata['mime_type'] = 'image/png'
        dsobject.set_file_path(path)
        datastore.write(dsobject)
        dsobject.destroy()

    def _copy_cb(self, button):
        self._text_item.get_text_buffer().copy_clipboard()

    def _paste_cb(self, button):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard_text = clipboard.wait_for_text()
        self._entry.paste_clipboard()

    def _init_font_list(self):
        self._font_list = []
        for f in FONT_CACHE:
            self._font_list.append(f['name'].encode('utf-8'))
        return

    def _setup_font_palette(self):
        self._init_font_list()

        palette_list = []
        for font in sorted(self._font_list):
            palette_list.append({'icon': FontImage(font.replace(' ', '-')),
                                 'callback': self.__font_selected_cb,
                                 'label': font})
        return palette_list

    def __font_selected_cb(self, widget, event, font_name):
        self._font_name = font_name
        return


class TextItem(ToolButton):

    def __init__(self, activity, **kwargs):
        ToolButton.__init__(self, 'edit-description', **kwargs)
        self.set_tooltip(_('Cloud Text'))
        self.palette_invoker.props.toggle_palette = True
        self.palette_invoker.props.lock_palette = True
        self.props.hide_tooltip_on_click = False
        self._palette = self.get_palette()

        description_box = PaletteMenuBox()

        sw = Gtk.ScrolledWindow()
        sw.set_size_request(int(Gdk.Screen.width() / 2),
                            2 * style.GRID_CELL_SIZE)
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

    def __init__(self, font_name):
        super(Gtk.Image, self).__init__()

        path = os.path.join(activity.get_bundle_path(), 'pytagcloud', 'fonts',
                            font_name.replace(' ', '-') + '.png')
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
            path, style.SMALL_ICON_SIZE, style.SMALL_ICON_SIZE) # 24, 24)
        self.set_from_pixbuf(pixbuf)
        self.show()


class FontToolItem(ToolButton):

    def __init__(self, activity, **kwargs):
        ToolButton.__init__(self, 'font-text', **kwargs)
        self.set_tooltip(_('Select_font'))
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


def set_palette_list(palette_list):
    item_width = style.GRID_CELL_SIZE * 3
    item_height = style.SMALL_ICON_SIZE + style.DEFAULT_SPACING + \
                  style.DEFAULT_PADDING

    nx = 3
    ny = int((len(palette_list) + 2) / 3)

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

        menu_item.connect('button-release-event', item['callback'],
                          item['label'])
        grid.attach(menu_item, x, y, 1, 1)
        x += 1
        if x == nx:
            x = 0
            y += 1

        menu_item.show()

    return scrolled_window
