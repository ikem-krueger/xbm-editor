#!/usr/bin/env python

# Copyright (C) 2009  Xyne
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# (version 2) as published by the Free Software Foundation.
#
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# METADATA
# Version: 0.7
VERSION = '0.7'

import pygtk
pygtk.require('2.0')
import gtk
from gtk import FILL,EXPAND,SHRINK
import gobject

import colorsys
import commands
import errno
import fuse
from fuse import Fuse,Stat
import math
import os
import os.path
import re
import shutil
import stat
import subprocess
import sys
from time import time
from types import StringType

gobject.threads_init()
gtk.gdk.threads_init()

############################################
########## Openbox Theme Elements ##########
############################################

themeElements = {
  'border.color':{
    'type':'color',
    'default':'#000000',
    'info':"This property is obsolete and only present for backwards compatibility.\nSee also: window.active.border.color, window.inactive.border.color, menu.border.color\n"
  },
  'border.width':{
    'type':'integer',
    'default':'1',
    'lbound':0,
    'ubound':100,
    'info':"Specifies the size of the border drawn around window frames.\nSee also: window.active.border.color, window.inactive.border.color\n"
  },
  'menu.border.color':{
    'type':'color',
    'default':'window.active.border.color',
    'info':"Specifies the border color for menus.\nSee also: menu.border.width\n"
  },
  'menu.border.width':{
    'type':'integer',
    'default':'border.width',
    'lbound':0,
    'ubound':100,
    'info':"Specifies the size of the border drawn around menus.\nSee also: menu.border.color\n"
  },
  'menu.items.active.bg':{
    'type':'texture',
    'default':'none',
    'parentrelative':1,
    'info':"Specifies the background for the selected menu entry (whether or not it is disabled). When it is parentrelative, then it uses the menu.items.bg which is underneath it.\nSee also: menu.items.bg\n"
  },
  'menu.items.active.disabled.text.color':{
    'type':'color',
    'default':'menu.items.disabled.text.color',
    'info':"Specifies the text color for disabled menu entries when they are selected.\n"
  },
  'menu.items.active.text.color':{
    'type':'color',
    'default':'#000000',
    'info':"Specifies the text color for normal menu entries when they are selected.\n"
  },
  'menu.items.bg':{
    'type':'texture',
    'default':'none',
    'parentrelative':False,
    'info':"Specifies the background for menus.\nSee also: menu.items.active.bg\n"
  },
  'menu.items.disabled.text.color':{
    'type':'color',
    'default':'#000000',
    'info':"Specifies the text color for disabled menu entries.\n"
  },
  'menu.items.font':{
    'type':'text shadow string',
    'default':'shadow=n',
    'info':"Specifies the shadow for all menu entries.\n"
  },
  'menu.items.text.color':{
    'type':'color',
    'default':'#FFFFFF',
    'info':"Specifies the text color for normal menu entries.\n"
  },
  'menu.overlap':{
    'type':'integer',
    'default':'0',
    'lbound':-100,
    'ubound':100,
    'info':"This property is obsolete and only present for backwards compatibility.\nSee also: menu.overlap.x, menu.overlap.y\n"
  },
  'menu.overlap.x':{
    'type':'integer',
    'default':'menu.overlap',
    'lbound':-100,
    'ubound':100,
    'info':"Specifies how sub menus should overlap their parents. A positive value moves the submenu over top of their parent by that amount. A negative value moves the submenu away from their parent by that amount. (As of version 3.4.7)\nSee also: menu.overlap.y\n"
  },
  'menu.overlap.y':{
    'type':'integer',
    'default':'menu.overlap',
    'lbound':-100,
    'ubound':100,
    'info':"Specifies how sub menus should be positioned relative to their parents. A positive value moves the submenu vertically down by that amount, a negative value moves it up by that amount. (As of version 3.4.7)\nSee also: menu.overlap.x\n"
  },
  'menu.separator.color':{
    'type':'color',
    'default':'menu.items.text.color',
    'info':"The color of menu line separators. (As of version 3.4.7)\nSee also: menu.items.text.color\n"
  },
  'menu.separator.padding.height':{
    'type':'integer',
    'default':'3',
    'lbound':0,
    'ubound':100,
    'info':"Specifies the space on the top and bottom of menu line separators. (As of version 3.4.7)\nSee also: menu.separator.padding.width\n"
  },
  'menu.separator.padding.width':{
    'type':'integer',
    'default':'6',
    'lbound':0,
    'ubound':100,
    'info':"Specifies the space on the left and right side of menu line separators. (As of version 3.4.7)\nSee also: menu.separator.padding.height\n"
  },
  'menu.separator.width':{
    'type':'integer',
    'default':'1',
    'lbound':1,
    'ubound':100,
    'info':"Specifies the size of menu line separators. (As of version 3.4.7)\n"
  },
  'menu.title.bg':{
    'type':'texture',
    'default':'none',
    'parentrelative':1,
    'info':"Specifies the background for menu headers. When it is parentrelative, then it uses the menu.items.bg which is underneath it.\nSee also: menu.items.bg\n"
  },
  'menu.title.text.color':{
    'type':'color',
    'default':'#000000',
    'info':"Specifies the text color for menu headers.\n"
  },
  'menu.title.text.font':{
    'type':'text shadow string',
    'default':'shadow=n',
    'info':"Specifies the shadow for all menu headers.\n"
  },
  'menu.title.text.justify':{
    'type':'justification',
    'default':'Left',
    'info':"Specifies how text is aligned in all menu headers.\n"
  },
  'osd.bg':{
    'type':'texture',
    'default':'window.active.title.bg',
    'parentrelative':False,
    'info':"Specifies the background for on-screen-dialogs, such as the focus cycling (Alt-Tab) dialog.\n"
  },
  'osd.border.color':{
    'type':'color',
    'default':'window.active.border.color',
    'info':"Specifies the border color for on-screen-dialogs, such as the focus cycling (Alt-Tab) dialog.\nSee also: osd.border.width\n"
  },
  'osd.border.width':{
    'type':'integer',
    'default':'border.width',
    'lbound':0,
    'ubound':100,
    'info':"Specifies the size of the border drawn on-screen-dialogs, such as the focus cycling (Alt-Tab) dialog.\nSee also: osd.border.color\n"
  },
  'osd.hilight.bg':{
    'type':'texture',
    'default':'window.active.label.bg, if it is not parentrelative. Otherwise, window.active.title.bg',
    'parentrelative':False,
    'info':"Specifies the texture for the selected desktop in the desktop cycling (pager) dialog.\n"
  },
  'osd.label.bg':{
    'type':'texture',
    'default':'window.active.label.bg',
    'parentrelative':1,
    'info':"Specifies the background for text in on-screen-dialogs, such as the focus cycling (Alt-Tab) dialog.\n"
  },
  'osd.label.text.color':{
    'type':'color',
    'default':'#000000',
    'info':"Specifies the text color for on-screen-dialogs, such as the focus cycling (Alt-Tab) dialog.\n"
  },
  'osd.label.text.font':{
    'type':'text shadow string',
    'default':'shadow=n',
    'info':"Specifies the text shadow for on-screen-dialogs, such as the focus cycling (Alt-Tab) dialog.\n"
  },
  'osd.unhilight.bg':{
    'type':'texture',
    'default':'window.inactive.label.bg, if it is not parentrelative. Otherwise, window.inactive.title.bg',
    'parentrelative':False,
    'info':"Specifies the texture for unselected desktops in the desktop cycling (pager) dialog.\n"
  },
  'padding.height':{
    'type':'integer',
    'default':'padding.width',
    'lbound':0,
    'ubound':100,
    'info':"Specifies the padding size, used for spacing out elements in the window decorations. This can be used to give a theme a more compact or a more relaxed feel. This specifies padding in only the vertical direction.\nSee also: padding.width\n"
  },
  'padding.width':{
    'type':'integer',
    'default':'3',
    'lbound':0,
    'ubound':100,
    'info':"Specifies the padding size, used for spacing out elements in the window decorations. This can be used to give a theme a more compact or a more relaxed feel. This specifies padding in the horizontal direction (and vertical direction if padding.height is not explicitly set).\nSee also: padding.height\n"
  },
  'window.active.border.color':{
    'type':'color',
    'default':'border.color',
    'info':"Specifies the border color for the focused window.\nSee also: border.width, window.inactive.border.color\n"
  },
  'window.active.button.disabled.bg':{
    'type':'texture',
    'default':'none',
    'parentrelative':1,
    'info':"Specifies the background for titlebar buttons when they are disabled for the window. This element is for the focused window. When it is parentrelative, then it uses the window.active.title.bg which is underneath it.\nSee also: titlebar colors, window.active.title.bg, window.inactive.button.disabled.bg\n"
  },
  'window.active.button.disabled.image.color':{
    'type':'color',
    'default':'#FFFFFF',
    'info':"Specifies the color of the images in titlebar buttons when they are disabled for the window. This element is for the focused window.\nSee also: window.inactive.button.disabled.image.color\n"
  },
  'window.active.button.hover.bg':{
    'type':'texture',
    'default':'window.active.button.unpressed.bg',
    'parentrelative':1,
    'info':"Specifies the background for titlebar buttons when the mouse is over them. This element is for the focused window. When it is parentrelative, then it uses the window.active.title.bg which is underneath it.\nSee also: titlebar colors, window.active.title.bg, window.inactive.button.hover.bg\n"
  },
  'window.active.button.hover.image.color':{
    'type':'color',
    'default':'window.active.button.unpressed.image.color',
    'info':"Specifies the color of the images in titlebar buttons when the mouse is over top of the button. This element is for the focused window.\nSee also: window.inactive.button.hover.image.color\n"
  },
  'window.active.button.pressed.bg':{
    'type':'texture',
    'default':'none',
    'parentrelative':1,
    'info':"Specifies the background for titlebar buttons when they are being pressed by the user. This element is for the focused window. When it is parentrelative, then it uses the window.active.title.bg which is underneath it.\nSee also: titlebar colors, window.active.title.bg, window.inactive.button.pressed.bg\n"
  },
  'window.active.button.pressed.image.color':{
    'type':'color',
    'default':'window.active.button.unpressed.image.color',
    'info':"Specifies the color of the images in titlebar buttons when they are being pressed by the user. This element is for the focused window.\nSee also: window.inactive.button.pressed.image.color\n"
  },
  'window.active.button.toggled.bg':{
    'type':'texture',
    'default':'window.active.button.pressed.bg',
    'parentrelative':1,
    'info':"This property is obsolete and only present for backwards compatibility.\n"
  },
  'window.active.button.toggled.hover.bg':{
    'type':'texture',
    'default':'window.active.button.toggled.unpressed.bg',
    'parentrelative':1,
    'info':"Specifies the default background for titlebar buttons if the user is pressing them with the mouse while they are toggled - such as when a window is maximized. This element is for the focused window. When it is parentrelative, then it uses the window.inactive.title.bg which is underneath it.\nSee also: titlebar colors, window.active.title.bg, window.inactive.button.toggled.hover.bg\n"
  },
  'window.active.button.toggled.hover.image.color':{
    'type':'color',
    'default':'window.active.button.toggled.unpressed.image.color',
    'info':"Specifies the color of the images in the titlebar buttons when the mouse is hovered over them while they are in the toggled state - such as when a window is maximized. This element is for the focused window.\nSee also: window.inactive.button.toggled.hover.image.color\n"
  },
  'window.active.button.toggled.image.color':{
    'type':'color',
    'default':'window.active.button.pressed.image.color',
    'info':"This property is obsolete and only present for backwards compatibility.\n"
  },
  'window.active.button.toggled.pressed.bg':{
    'type':'texture',
    'default':'window.active.button.pressed.bg',
    'parentrelative':1,
    'info':"Specifies the default background for titlebar buttons if the user is pressing them with the mouse while they are toggled - such as when a window is maximized. This element is for the focused window. When it is parentrelative, then it uses the window.inactive.title.bg which is underneath it.\nSee also: titlebar colors, window.active.title.bg, window.inactive.button.toggled.pressed.bg\n"
  },
  'window.active.button.toggled.pressed.image.color':{
    'type':'color',
    'default':'window.active.button.pressed.image.color',
    'info':"Specifies the color of the images in the titlebar buttons if they are pressed on with the mouse while they are in the toggled state - such as when a window is maximized. This element is for the focused window.\nSee also: window.inactive.button.toggled.pressed.image.color\n"
  },
  'window.active.button.toggled.unpressed.bg':{
    'type':'texture',
    'default':'window.active.button.toggled.bg',
    'parentrelative':1,
    'info':"Specifies the default background for titlebar buttons when they are toggled - such as when a window is maximized. This element is for the focused window. When it is parentrelative, then it uses the window.inactive.title.bg which is underneath it.\nSee also: titlebar colors, window.active.title.bg, window.inactive.button.toggled.unpressed.bg\n"
  },
  'window.active.button.toggled.unpressed.image.color':{
    'type':'color',
    'default':'window.active.button.toggled.image.color',
    'info':"Specifies the color of the images in titlebar buttons when the button is toggled - such as when a window is maximized. This element is for the focused window.\nSee also: window.inactive.button.toggled.unpressed.image.color\n"
  },
  'window.active.button.unpressed.bg':{
    'type':'texture',
    'default':'none',
    'parentrelative':1,
    'info':"Specifies the background for titlebar buttons in their default, unpressed, state. This element is for the focused window. When it is parentrelative, then it uses the window.active.title.bg which is underneath it.\nSee also: titlebar colors, window.active.title.bg, window.inactive.button.unpressed.bg\n"
  },
  'window.active.button.unpressed.image.color':{
    'type':'color',
    'default':'#000000',
    'info':"Specifies the color of the images in titlebar buttons in their default, unpressed, state. This element is for the focused window.\nSee also: window.inactive.button.unpressed.image.color\n"
  },
  'window.active.client.color':{
    'type':'color',
    'default':'#FFFFFF',
    'info':"Specifies the color of the inner border for the focused window, drawn around the window but inside the other decorations.\nSee also: window.client.padding.width, window.inactive.client.color\n"
  },
  'window.active.grip.bg':{
    'type':'texture',
    'default':'none',
    'parentrelative':False,
    'info':"Specifies the background for the focused window's grips. The grips are located at the left and right sides of the window's handle. When it is parentrelative, then it uses the window.active.handle.bg which is underneath it.\nSee also: window.handle.width, window.inactive.grip.bg, window.active.handle.bg\n"
  },
  'window.active.handle.bg':{
    'type':'texture',
    'default':'none',
    'parentrelative':False,
    'info':"Specifies the background for the focused window's handle. The handle is the window decorations placed on the bottom of windows.\nSee also: window.handle.width, window.inactive.handle.bg\n"
  },
  'window.active.label.bg':{
    'type':'texture',
    'default':'none',
    'parentrelative':1,
    'info':"Specifies the background for the focused window's titlebar label. The label is the container for the window title. When it is parentrelative, then it uses the window.active.title.bg which is underneath it.\nSee also: titlebar colors, window.inactive.label.bg, window.active.title.bg\n"
  },
  'window.active.label.text.color':{
    'type':'color',
    'default':'#000000',
    'info':"Specifies the color of the titlebar text for the focused window.\nSee also: window.inactive.label.text.color\n"
  },
  'window.active.label.text.font':{
    'type':'text shadow string',
    'default':'shadow=n',
    'info':"Specifies the shadow for the focused window's title.\nSee also: window.inactive.label.text.font\n"
  },
  'window.active.title.bg':{
    'type':'texture',
    'default':'none',
    'parentrelative':False,
    'info':"Specifies the background for the focused window's titlebar.\nSee also: window.inactive.title.bg\n"
  },
  'window.active.title.separator.color':{
    'type':'color',
    'default':'window.active.border.color',
    'info':"Specifies the border color for the border between the titlebar and the window, for the focused window.\nSee also: window.inactive.title.separator.color\n"
  },
  'window.client.padding.height':{
    'type':'integer',
    'default':'window.client.padding.width',
    'lbound':0,
    'ubound':100,
    'info':"Specifies the size of the top and bottom sides of the inner border. The inner border is drawn around the window, but inside the other decorations.\nSee also: window.active.client.color, window.inactive.client.color window.client.padding.width\n"
  },
  'window.client.padding.width':{
    'type':'integer',
    'default':'padding.width',
    'lbound':0,
    'ubound':100,
    'info':"Specifies the size of the left and right sides of the inner border. The inner border is drawn around the window, but inside the other decorations.\nSee also: window.active.client.color, window.inactive.client.color window.client.padding.height\n"
  },
  'window.handle.width':{
    'type':'integer',
    'default':'6',
    'lbound':0,
    'ubound':100,
    'info':"Specifies the size of the window handle. The window handle is the piece of decorations on the bottom of windows. A value of 0 means that no handle is shown.\nSee also: window.active.handle.bg, window.inactive.handle.bg, window.active.grip.bg, window.inactive.grip.bg\n"
  },
  'window.inactive.border.color':{
    'type':'color',
    'default':'window.active.border.color',
    'info':"Specifies the border color for all non-focused windows.\nSee also: border.width, window.active.border.color\n"
  },
  'window.inactive.button.disabled.bg':{
    'type':'texture',
    'default':'none',
    'parentrelative':1,
    'info':"Specifies the background for titlebar buttons when they are disabled for the window. This element is for non-focused windows. When it is parentrelative, then it uses the window.inactive.title.bg which is underneath it.\nSee also: titlebar colors, window.inactive.title.bg, window.active.button.disabled.bg\n"
  },
  'window.inactive.button.disabled.image.color':{
    'type':'color',
    'default':'#000000',
    'info':"Specifies the color of the images in titlebar buttons when they are disabled for the window. This element is for non-focused windows.\nSee also: window.active.button.disabled.image.color\n"
  },
  'window.inactive.button.hover.bg':{
    'type':'texture',
    'default':'window.inactive.button.unpressed.bg',
    'parentrelative':1,
    'info':"Specifies the background for titlebar buttons when the mouse is over them. This element is for non-focused windows. When it is parentrelative, then it uses the window.inactive.title.bg which is underneath it.\nSee also: titlebar colors, window.inactive.title.bg, window.active.button.hover.bg\n"
  },
  'window.inactive.button.hover.image.color':{
    'type':'color',
    'default':'window.inactive.button.unpressed.image.color',
    'info':"Specifies the color of the images in titlebar buttons when the mouse is over top of the button. This element is for non-focused windows.\nSee also: window.active.button.hover.image.color\n"
  },
  'window.inactive.button.pressed.bg':{
    'type':'texture',
    'default':'none',
    'parentrelative':1,
    'info':"Specifies the background for titlebar buttons when they are being pressed by the user. This element is for non-focused windows. When it is parentrelative, then it uses the window.inactive.title.bg which is underneath it.\nSee also: titlebar colors, window.inactive.title.bg, window.active.button.pressed.bg\n"
  },
  'window.inactive.button.pressed.image.color':{
    'type':'color',
    'default':'window.inactive.button.unpressed.image.color',
    'info':"Specifies the color of the images in titlebar buttons when they are being pressed by the user. This element is for non-focused windows.\nThis color is also used for pressed color when the button is toggled.\nSee also: window.active.button.pressed.image.color\n"
  },
  'window.inactive.button.toggled.bg':{
    'type':'texture',
    'default':'window.inactive.button.pressed.bg',
    'parentrelative':1,
    'info':"This property is obsolete and only present for backwards compatibility.\n"
  },
  'window.inactive.button.toggled.hover.bg':{
    'type':'texture',
    'default':'window.inactive.button.toggled.unpressed.bg',
    'parentrelative':1,
    'info':"Specifies the default background for titlebar buttons if the user is pressing them with the mouse while they are toggled - such as when a window is maximized. This element is for non-focused windows. When it is parentrelative, then it uses the window.inactive.title.bg which is underneath it.\nSee also: titlebar colors, window.inactive.title.bg, window.active.button.toggled.hover.bg\n"
  },
  'window.inactive.button.toggled.hover.image.color':{
    'type':'color',
    'default':'window.inactive.button.toggled.unpressed.image.color',
    'info':"Specifies the color of the images in the titlebar buttons when the mouse is hovered over them while they are in the toggled state - such as when a window is maximized. This element is for non-focused windows.\nSee also: window.active.button.toggled.hover.image.color\n"
  },
  'window.inactive.button.toggled.image.color':{
    'type':'color',
    'default':'window.active.button.pressed.image.color',
    'info':"This property is obsolete and only present for backwards compatibility.\n"
  },
  'window.inactive.button.toggled.pressed.bg':{
    'type':'texture',
    'default':'window.inactive.button.pressed.bg',
    'parentrelative':1,
    'info':"Specifies the default background for titlebar buttons if the user is pressing them with the mouse while they are toggled - such as when a window is maximized. This element is for non-focused windows. When it is parentrelative, then it uses the window.inactive.title.bg which is underneath it.\nSee also: titlebar colors, window.inactive.title.bg, window.active.button.toggled.pressed.bg\n"
  },
  'window.inactive.button.toggled.pressed.image.color':{
    'type':'color',
    'default':'window.inactive.button.pressed.image.color',
    'info':"Specifies the color of the images in the titlebar buttons if they are pressed on with the mouse while they are in the toggled state - such as when a window is maximized. This element is for non-focused windows.\nSee also: window.active.button.toggled.pressed.image.color\n"
  },
  'window.inactive.button.toggled.unpressed.bg':{
    'type':'texture',
    'default':'window.inactive.button.toggled.bg',
    'parentrelative':1,
    'info':"Specifies the default background for titlebar buttons when they are toggled - such as when a window is maximized. This element is for non-focused windows. When it is parentrelative, then it uses the window.inactive.title.bg which is underneath it.\nSee also: titlebar colors, window.inactive.title.bg, window.active.button.toggled.unpressed.bg\n"
  },
  'window.inactive.button.toggled.unpressed.image.color':{
    'type':'color',
    'default':'window.inactive.button.toggled.image.color',
    'info':"Specifies the color of the images in titlebar buttons when the button is toggled - such as when a window is maximized. This element is for non-focused windows.\nSee also: window.active.button.toggled.unpressed.image.color\n"
  },
  'window.inactive.button.unpressed.bg':{
    'type':'texture',
    'default':'none',
    'parentrelative':1,
    'info':"Specifies the background for titlebar buttons in their default, unpressed, state. This element is for non-focused windows. When it is parentrelative, then it uses the window.inactive.title.bg which is underneath it.\nSee also: titlebar colors, window.inactive.title.bg, window.active.button.unpressed.bg\n"
  },
  'window.inactive.button.unpressed.image.color':{
    'type':'color',
    'default':'#FFFFFF',
    'info':"Specifies the color of the images in titlebar buttons in their default, unpressed, state. This element is for non-focused windows.\nSee also: window.active.button.unpressed.image.color\n"
  },
  'window.inactive.client.color':{
    'type':'color',
    'default':'#FFFFFF',
    'info':"Specifies the color of the inner border for non-focused windows, drawn around the window but inside the other decorations.\nSee also: window.client.padding.width, window.active.client.color\n"
  },
  'window.inactive.grip.bg':{
    'type':'texture',
    'default':'none',
    'parentrelative':False,
    'info':"Specifies the background for non-focused windows' grips. The grips are located at the left and right sides of the window's handle. When it is parentrelative, then it uses the window.inactive.handle.bg which is underneath it.\nSee also: window.handle.width, window.active.grip.bg, window.inactive.handle.bg\n"
  },
  'window.inactive.handle.bg':{
    'type':'texture',
    'default':'none',
    'parentrelative':False,
    'info':"Specifies the background for non-focused windows' handles. The handle is the window decorations placed on the bottom of windows.\nSee also: window.handle.width, window.active.handle.bg\n"
  },
  'window.inactive.label.bg':{
    'type':'texture',
    'default':'none',
    'parentrelative':1,
    'info':"Specifies the background for non-focused windows' titlebar labels. The label is the container for the window title. When it is parentrelative, then it uses the window.inactive.title.bg which is underneath it.\nSee also: titlebar colors, window.active.label.bg, window.inactive.title.bg\n"
  },
  'window.inactive.label.text.color':{
    'type':'color',
    'default':'#FFFFFF',
    'info':"Specifies the color of the titlebar text for non-focused windows.\nSee also: window.active.label.text.color\n"
  },
  'window.inactive.label.text.font':{
    'type':'text shadow string',
    'default':'shadow=n',
    'info':"Specifies the shadow for non-focused windows' titles.\nSee also: window.active.label.text.font\n"
  },
  'window.inactive.title.bg':{
    'type':'texture',
    'default':'none',
    'parentrelative':False,
    'info':"Specifies the background for non-focused windows' titlebars.\nSee also: window.active.title.bg\n"
  },
  'window.inactive.title.separator.color':{
    'type':'color',
    'default':'window.inactive.border.color',
    'info':"Specifies the border color for the border between the titlebar and the window, for non-focused windows.\nSee also: window.active.title.separator.color\n"
  },
  'window.label.text.justify':{
    'type':'justification',
    'default':'Left',
    'info':"Specifies how window titles are aligned in the titlebar for both the focused and non-focused windows.\n"
  }
}



imageButtons = {
  'max':{
    'default':[None],
    'info':"Maximize button in its default, unpressed state.\n"
  },
  'max_toggled':{
    'default':['max',None],
    'info':"Maximize button when it is in toggled state.\n"
  },
  'max_pressed':{
    'default':['max',None],
    'info':"Maximized button when pressed.\n"
  },
  'max_disabled':{
    'default':['max',None],
    'info':"Maximized button when disabled.\n"
  },
  'max_hover':{
    'default':['max',None],
    'info':"Maximized button when mouse is over it.\n"
  },
  'max_toggled_pressed':{
    'default':['max_toggled','max',None],
    'info':"Maximized button when pressed, in toggled state.\n"
  },
  'max_toggled_hover':{
    'default':['max_toggled','max',None],
    'info':"Maximized button when mouse is over it, in toggled state.\n"
  },

  'iconify':{
    'default':[None],
    'info':"Iconify button in its default, unpressed state.\n"
  },
  'iconify_pressed':{
    'default':['iconify',None],
    'info':"Iconify button when pressed.\n"
  },
  'iconify_disabled':{
    'default':['iconify',None],
    'info':"Iconify button when disabled.\n"
  },
  'iconify_hover':{
    'default':['iconify',None],
    'info':"Iconify button when mouse is over it.\n"
  },

  'close':{
    'default':[None],
    'info':"Close button in its default, unpressed state.\n"
  },
  'close_pressed':{
    'default':['close',None],
    'info':"Close button when pressed.\n"
  },
  'close_disabled':{
    'default':['close',None],
    'info':"Close button when disabled.\n"
  },
  'close_hover':{
    'default':['close',None],
    'info':"Close button when mouse is over it.\n"
  },

  'desk':{
    'default':[None],
    'info':"All-desktops button in its default, unpressed state.\n"
  },
  'desk_toggled':{
    'default':['desk',None],
    'info':"All-desktops button when it is in toggled state.\n"
  },
  'desk_pressed':{
    'default':['desk',None],
    'info':"All-desktops button when pressed.\n"
  },
  'desk_disabled':{
    'default':['desk',None],
    'info':"All-desktops button when disabled.\n"
  },
  'desk_hover':{
    'default':['desk_toggled','desk',None],
    'info':"All-desktops button when mouse is over it.\n"
  },
  'desk_toggled_pressed':{
    'default':['desk_toggled','desk',None],
    'info':"All-desktops button when pressed, in toggled state.\n"
  },

  'shade':{
    'default':[None],
    'info':"Shade button in its default, unpressed state.\n"
  },
  'shade_toggled':{
    'default':['shade',None],
    'info':"Shade button when it is in toggled state.\n"
  },
  'shade_pressed':{
    'default':['shade',None],
    'info':"Shade button when pressed.\n"
  },
  'shade_disabled':{
    'default':['shade',None],
    'info':"Shade button when disabled.\n"
  },
  'shade_hover':{
    'default':['shade',None],
    'info':"Shade button when mouse is over it.\n"
  },
  'shade_toggled_pressed':{
    'default':['shade_toggled','shade',None],
    'info':"Shade button when pressed, in toggled state.\n"
  },
  'shade_toggled_hover':{
    'default':['shade_toggled','shade',None],
    'info':"Shade button when mouse is over it, in toggled state.\n"
  },

  'bullet':{
    'default':[None],
    'info':"The bullet shown in a menu for submenu entries.\n"
  }
}

#######################################
########## General Functions  ##########
#######################################


def color_to_str(color):
  red = round((color.red / 65535.0) * 255)
  green = round((color.green / 65535.0) * 255)
  blue = round((color.blue / 65535.0) * 255)
  return "#%02X%02X%02X" % (red,green,blue)

def str_to_color(string):
  return gtk.gdk.color_parse(string)

def format_ob_color_str(string):
  if string.startswith('rgb:'):
    string = string.replace('rgb:','#')
    string = string.replace('/','')

  # this is to handle color names
  if not string.startswith('#'):
    string = color_to_str(str_to_color(string))

  if len(string) == 4:
    string = re.sub(r'([\da-fA-F])', '\g<1>0', string)

  return string

def multiply_color(color,f):
  r = int(color[1:3],16) * f
  if r > 255:
    r = 255
  g = int(color[3:5],16) * f
  if g > 255:
    g = 255
  b = int(color[5:7],16) * f
  if b > 255:
    b = 255
  return "#%02X%02X%02X" % (r,g,b)

def read_file(path):
  f = open(path,'r')
  contents = f.read()
  f.close()
  return contents

def write_file(path,contents):
  try:
    f = open(path,'w')
  except IOError:
    return False
  else:
    f.write(contents)
    f.close()
    return True

def which(program):
  def is_exe(fpath):
    return os.path.exists(fpath) and os.access(fpath, os.X_OK)
  fpath, fname = os.path.split(program)
  if fpath:
    if is_exe(program):
      return program
  else:
    for path in os.environ["PATH"].split(os.pathsep):
      exe_file = os.path.join(path, program)
      if is_exe(exe_file):
        return exe_file
  return None

def clear_dir(dpath):
  if os.path.exists(dpath):
    for item in os.listdir(dpath):
      if dpath[-1:] == '/':
        spath = dpath+item
      else:
        spath = dpath+'/'+item
      if os.path.isdir(spath):
        shutil.rmtree(spath)
      else:
        os.remove(spath)

#########################################
########## Modifed ColorButton ##########
#########################################

class ColorButton(gtk.ColorButton):

  def __init__(self,*args):
    gtk.ColorButton.__init__(self,*args)
    self.drag_dest_set(0,[],0)
    self.connect("drag_motion", self.drag_motion)
    self.connect("drag_drop", self.drag_drop)

  def drag_motion(self, widget, context, x, y, time):
    context.drag_status(gtk.gdk.ACTION_COPY, time)
    return True

  def drag_drop(self, widget, context, x, y, time):
    source_widget = context.get_source_widget()
    if source_widget.__class__.__name__ == 'ColorButton':
      color = source_widget.get_value()
      self.set_value(color)
    else:
      source_widget = source_widget.get_parent().get_parent().get_parent()
      if source_widget.__class__.__name__ == 'Palette':
        color = source_widget.get_value()
        if color:
          self.set_value(color)
    context.finish(True, False, time)
    self.emit('color-set')
    return True

  def get_value(self):
    return color_to_str(self.get_color())

  def set_value(self,string):
    return self.set_color(str_to_color(string))


###################################
########## Integer Frame ##########
###################################

class IntegerFrame(gtk.Frame):
  def update_value(self,*arg):
    if self.callback and self.sensitive:
      self.callback(int(self.value.get_value()))

  def configure(self,name,value,theme):
    self.sensitive = False
    value = int(value)
    if themeElements[name].has_key('ubound'):
      ubound = themeElements[name]['ubound']
      if value > ubound:
        value = ubound
    else:
      ubound = 100
    self.set_ubound(ubound)
    if themeElements[name].has_key('lbound'):
      lbound = themeElements[name]['lbound']
      if value < lbound:
        value = lbound
    else:
      lbound = 0
    if themeElements[name].has_key('default'):
      self.default = themeElements[name]['default']
    self.set_lbound(lbound)
    self.set_value(value)
    self.sensitive = True


  def reset(self,*args):
    self.value.set_value(float(self.default))

  def set_value(self,string):
    self.value.set_value(int(string))

  def get_string(self):
    return str(self.value.get_value())

  def set_lbound(self,lbound):
    self.value.lower = int(lbound)

  def set_ubound(self,ubound):
    self.value.upper = int(ubound)

  def __init__(self,**args):
    gtk.Frame.__init__(self,**args)
    self.set_shadow_type(gtk.SHADOW_NONE)
    self.set_label_align(1,0.5)
    self.set_label("integer")
    self.default = 1
    self.callback = None

    self.value = gtk.Adjustment(1,0,100,1,1,0)
    self.value.connect("value_changed", self.update_value)

    hbox = gtk.HBox(True,5)
    self.add(hbox)
    boxargs = {'expand' : False, 'fill' : True, 'padding' : 5}


    label = gtk.Label("value:")
    label.set_alignment(0.5,0.5)
    hbox.pack_start(label, **boxargs)
    label.show()


    spinbutton = gtk.SpinButton(self.value,0,0)
    spinbutton.set_numeric(True)
    spinbutton.set_digits(0)
    spinbutton.set_alignment(0.5)
    hbox.pack_start(spinbutton, **boxargs)
    spinbutton.show()

    reset = gtk.Button(label="reset")
    reset.set_alignment(0.5,0.5)
    reset.connect("clicked",self.reset)
    hbox.pack_start(reset,**boxargs)
    reset.show()


    hbox.show()

    self.update_value()



#########################################
########## Justification Frame ##########
#########################################

class JustificationFrame(gtk.Frame):
  def update_value(self,*args):
    value = self.combobox.get_active_text()
    if self.callback and self.sensitive:
      self.callback(value)

  def configure(self,name,value,theme):
    self.sensitive = False
    value = value.lower()
    model = self.combobox.get_model()
    for i in range(len(model)):
      if model[i][0].lower() == value:
        self.combobox.set_active(i)
        break
    self.sensitive = True

  def __init__(self,**args):
    gtk.Frame.__init__(self,**args)
    self.set_shadow_type(gtk.SHADOW_NONE)
    self.set_label_align(1,0.5)
    self.set_label("justification")
    self.callback = None

    self.combobox = gtk.combo_box_new_text()
    self.add(self.combobox)
    self.combobox.append_text('Left')
    self.combobox.append_text('Center')
    self.combobox.append_text('Right')
    self.combobox.connect('changed', self.update_value)
    self.combobox.set_active(0)
    self.combobox.show()



###################################
########## Texture Frame ##########
###################################

class TextureFrame(gtk.Frame):

  def update_value(self,*args):
    attributes = {}
    texture = self.texture.get_active_text()
    if texture == 'ParentRelative':
      string = texture
    elif texture == 'Solid':
      string = texture
      attributes['color'] = self.color.get_value()
    elif texture == 'Gradient':
      gradient = self.gradient.get_active_text()
      string = "%s %s" % (texture,gradient)
      color = self.color.get_value()
      colorTo = self.colorTo.get_value()
      attributes['color'] = color
      attributes['colorTo'] = colorTo

      if gradient == 'SplitVertical':
        colorSplitTo = self.colorSplitTo.get_value()
        colorToSplitTo = self.colorToSplitTo.get_value()
        if self.colorSplitTo_tb.get_active() and colorSplitTo != multiply_color(color,5/4.0):
          attributes['color.splitTo'] = colorSplitTo
        if self.colorToSplitTo_tb.get_active() and colorToSplitTo != multiply_color(colorTo,17/16.0):
          attributes['colorTo.splitTo'] = colorToSplitTo
    else:
      return

    if self.interlaced.get_active():
      string += ' ' + 'Interlaced'
      attributes['interlace.color'] = self.interlacedColor.get_value()

    border = self.border.get_active_text()
    if border == 'None':
      string += ' ' + 'Flat'
    elif border == 'Flat':
      string += ' ' + 'Flat Border'
      attributes['border.color'] = self.borderColor.get_value()
    elif border == 'Raised' or border == 'Sunken':
      string += ' ' + border
      attributes['border.color'] = self.borderColor.get_value()
      if self.highlight.get_value() != 128:
        attributes['highlight'] = int(self.highlight.get_value())
      if self.shadow.get_value() != 64:
        attributes['shadow'] = int(self.shadow.get_value())
      if self.bevelButton2.get_active():
        string += ' ' + 'Bevel2'

    for name,value in attributes.iteritems():
      string += "\n.%s: %s" % (name,value)

    if self.callback and self.sensitive:
      self.callback(string)


  def configure(self,name,string,theme):
    self.sensitive = False
    attributes = {}
    if themeElements[name].has_key('parentrelative'):
      self.set_parentrelative(themeElements[name]['parentrelative'])
    else:
      self.set_parentrelative(True)
    for line in string.split("\n"):
      m = re.search(r'^\.([^:]+?)\s*:\s*(\S+)\s*$',line)
      if m:
        attribute = m.group(1).lower()
        value = m.group(2)
        if attribute == 'color':
          self.color.set_value(value)
        elif attribute == 'colorto':
          self.colorTo.set_value(value)
        elif attribute == 'color.splitto':
          self.colorSplitTo.set_value(value)
        elif attribute == 'colorto.splitto':
          self.colorToSplitTo.set_value(value)
        elif attribute == 'interlace.color':
          self.interlacedColor.set_value(value)
        elif attribute == 'border.color':
          self.borderColor.set_value(value)
        elif attribute == 'highlight':
          self.highlight.set_value(float(value))
        elif attribute == 'shadow':
          self.shadow.set_value(float(value))
        attributes[attribute] = True
      else:
        for word in re.split('\s+',line):
          word = word.lower()
          if word == 'solid' \
          or word == 'gradient' \
          or word == 'parentrelative':
            model = self.texture.get_model()
            for i in range(len(model)):
              if model[i][0].lower() == word:
                self.texture.set_active(i)
                break
          elif word == 'diagonal' \
          or word == 'crossdiagonal' \
          or word == 'pyramid' \
          or word == 'horizontal' \
          or word == 'mirrorhorizontal' \
          or word == 'vertical' \
          or word == 'splitvertical':
            model = self.gradient.get_model()
            for i in range(len(model)):
              if model[i][0].lower() == word:
                self.gradient.set_active(i)
                break
          elif word == 'flat' \
          or word == 'raised' \
          or word == 'sunken':
            model = self.border.get_model()
            for i in range(len(model)):
              if model[i][0].lower() == word:
                self.border.set_active(i)
                break
          elif word == 'interlaced':
            self.interlaced.set_active(True)
          elif word == 'bevel2':
            self.bevelButton2.set_active(True)

    if self.border.get_active_text() == 'Flat':
      if not attributes.has_key('border.color'):
        model = self.border.get_model()
        for i in range(len(model)):
          if model[i][0] == 'None':
            self.border.set_active(i)
            break
    if not attributes.has_key('color.splitto'):
      self.colorSplitTo.set_value(multiply_color(self.color.get_value(),5/4.0))
    if not attributes.has_key('color.splitto'):
      self.colorToSplitTo.set_value(multiply_color(self.colorTo.get_value(),17/16.0))
    self.sensitive = True



  def update_texture(self,*args):
    texture = self.texture.get_active_text()
    if texture == 'Solid':
      self.gradient.set_sensitive(False)
      self.color.set_sensitive(True)
      self.colorTo.set_sensitive(False)
      self.colorSplitTo.set_sensitive(False)
      self.colorToSplitTo.set_sensitive(False)
    elif texture == 'Gradient':
      self.gradient.set_sensitive(True)
      self.color.set_sensitive(True)
      self.colorTo.set_sensitive(True)
      self.update_gradient()
    elif texture == 'ParentRelative':
      self.gradient.set_sensitive(False)
      self.color.set_sensitive(False)
      self.colorTo.set_sensitive(False)
      self.colorSplitTo.set_sensitive(False)
      self.colorToSplitTo.set_sensitive(False)
    self.update_value()

  def update_gradient(self,*args):
    gradient = self.gradient.get_active_text()
    if gradient == 'SplitVertical': #gradient == 'MirrorHorizontal'
      self.colorSplitTo.set_sensitive(self.colorSplitTo_tb.get_active())
      self.colorToSplitTo.set_sensitive(self.colorToSplitTo_tb.get_active())
    else:
      self.colorSplitTo.set_sensitive(False)
      self.colorToSplitTo.set_sensitive(False)
    self.update_value()

  def update_interlaced(self,*args):
    if self.interlaced.get_active():
      self.interlacedColor.set_sensitive(True)
    else:
      self.interlacedColor.set_sensitive(False)
    self.update_value()

  def set_parentrelative(self,value):
    model = self.texture.get_model()
    string = 'ParentRelative'
    if value == True and model[0][0] != string:
      self.texture.prepend_text(string)
    elif value != True and model[0][0] == string:
      self.texture.set_active(1)
      self.texture.remove_text(0)

  def update_border(self,*args):
    border = self.border.get_active_text()
    if border == 'None':
      self.borderColor.set_sensitive(False)
      self.highlightButton.set_sensitive(False)
      self.shadowButton.set_sensitive(False)
      self.bevelButton1.set_sensitive(False)
      self.bevelButton2.set_sensitive(False)
    elif border == 'Flat':
      self.borderColor.set_sensitive(True)
      self.highlightButton.set_sensitive(False)
      self.shadowButton.set_sensitive(False)
      self.bevelButton1.set_sensitive(False)
      self.bevelButton2.set_sensitive(False)
      self.update_gradient()
    elif border == 'Raised' or border == 'Sunken':
      self.borderColor.set_sensitive(True)
      self.highlightButton.set_sensitive(True)
      self.shadowButton.set_sensitive(True)
      self.bevelButton1.set_sensitive(True)
      self.bevelButton2.set_sensitive(True)
    self.update_value()


  def reset(self,*args):
#     model = self.texture.get_model()
#     for i in range(len(model)):
#       if model[i][0].lower() == 'solid':
#         self.texture.set_active(i)
#         break
#     model = self.gradient.get_model()
#     for i in range(len(model)):
#       if model[i][0].lower() == 'vertical':
#         self.gradient.set_active(i)
#         break
#     model = self.border.get_model()
#     for i in range(len(model)):
#       if model[i][0].lower() == 'raised':
#         self.border.set_active(i)
#         break
#     self.color.set_value('#000000')
#     self.borderColor.set_value('#000000')
    self.colorSplitTo_tb.set_active(False)
    self.colorToSplitTo_tb.set_active(False)
    self.interlaced.set_active(False)
    self.highlight.set_value(128)
    self.shadow.set_value(64)
    self.bevelButton1.set_active(True)
    self.update_value()


  def __init__(self,**args):
    gtk.Frame.__init__(self,**args)
    self.set_shadow_type(gtk.SHADOW_NONE)
    self.set_label_align(1,0.5)
    self.set_label("texture")
    self.callback = None


    self.texture = gtk.combo_box_new_text()
    self.texture.append_text('ParentRelative')
    self.texture.append_text('Solid')
    self.texture.append_text('Gradient')
    self.texture.set_active(1)
    self.texture.connect('changed', self.update_texture)
    self.texture.show()
    textureLabel = gtk.Label('texture')
    textureLabel.set_alignment(0,0.5)


    self.gradient = gtk.combo_box_new_text()
    self.gradient.append_text('Diagonal')
    self.gradient.append_text('CrossDiagonal')
    self.gradient.append_text('Pyramid')
    self.gradient.append_text('Horizontal')
    self.gradient.append_text('MirrorHorizontal')
    self.gradient.append_text('Vertical')
    self.gradient.append_text('SplitVertical')
    self.gradient.set_active(5)
    self.gradient.connect('changed', self.update_gradient)
    self.gradient.show()
    gradientLabel = gtk.Label('gradient')
    gradientLabel.set_alignment(0,0.5)


    self.color = ColorButton()
    self.color.connect("color-set",self.update_value)
    colorLabel = gtk.Label('color')
    colorLabel.set_alignment(0,0.5)

    self.colorTo = ColorButton()
    self.colorTo.connect("color-set",self.update_value)
    colorToLabel = gtk.Label('colorTo')
    colorToLabel.set_alignment(0,0.5)

    self.colorSplitTo = ColorButton()
    self.colorSplitTo.connect("color-set",self.update_value)
    self.colorSplitTo_tb = gtk.CheckButton("color.splitTo")
    self.colorSplitTo_tb.connect("toggled", self.update_gradient)
    self.colorSplitTo_tb.set_active(False)
    self.colorSplitTo_tb.set_alignment(0,0.5)

    self.colorToSplitTo = ColorButton()
    self.colorToSplitTo.connect("color-set",self.update_value)
    self.colorToSplitTo_tb = gtk.CheckButton("colorTo.splitTo")
    self.colorToSplitTo_tb.connect("toggled", self.update_gradient)
    self.colorToSplitTo_tb.set_active(False)
    self.colorToSplitTo_tb.set_alignment(0,0.5)

    self.interlaced = gtk.CheckButton("interlaced")
    self.interlaced.connect("toggled", self.update_interlaced)
    self.interlacedColor = ColorButton()
    self.interlacedColor.connect("color-set",self.update_value)
    self.interlacedColor.set_sensitive(False)


    colortable = gtk.Table(rows=2,columns=2,homogeneous=False)
    i = 0
    colortable.attach(textureLabel,0,1,i,i+1,FILL,EXPAND,5,0)
    colortable.attach(self.texture,1,2,i,i+1,FILL,EXPAND,0,0)
    i += 1
    colortable.attach(gradientLabel,0,1,i,i+1,FILL,EXPAND,5,0)
    colortable.attach(self.gradient,1,2,i,i+1,FILL,EXPAND,0,0)
    i += 1
    colortable.attach(colorLabel,0,1,i,i+1,FILL,EXPAND,5,0)
    colortable.attach(self.color,1,2,i,i+1,FILL,EXPAND,0,0)
    i += 1
    colortable.attach(colorToLabel,0,1,i,i+1,FILL,EXPAND,5,0)
    colortable.attach(self.colorTo,1,2,i,i+1,FILL,EXPAND,0,0)
    i += 1
    colortable.attach(self.colorSplitTo_tb,0,1,i,i+1,FILL,EXPAND,5,0)
    colortable.attach(self.colorSplitTo,1,2,i,i+1,FILL,EXPAND,0,0)

    i += 1
    colortable.attach(self.colorToSplitTo_tb,0,1,i,i+1,FILL,EXPAND,5,0)
    colortable.attach(self.colorToSplitTo,1,2,i,i+1,FILL,EXPAND,0,0)
    i += 1
    colortable.attach(self.interlaced,0,1,i,i+1,FILL,EXPAND,5,0)
    colortable.attach(self.interlacedColor,1,2,i,i+1,FILL,EXPAND,0,0)
    i += 1
    colortable.show_all()





    self.border = gtk.combo_box_new_text()
    self.border.append_text('None')
    self.border.append_text('Flat')
    self.border.append_text('Raised')
    self.border.append_text('Sunken')
    self.border.set_active(2)
    self.border.connect('changed', self.update_border)
    borderLabel = gtk.Label('border')
    borderLabel.set_alignment(0,0.5)

    self.bevelButton1 = gtk.RadioButton(None,"Bevel1")
    self.bevelButton2 = gtk.RadioButton(self.bevelButton1,"Bevel2")
    self.bevelButton1.connect("toggled", self.update_interlaced)


    self.borderColor = ColorButton()
    self.borderColor.connect("color-set",self.update_value)
    borderColorLabel = gtk.Label('border color')
    borderColorLabel.set_alignment(0,0.5)

    self.highlight = gtk.Adjustment(128,0,65535,1,256,0)
    self.shadow = gtk.Adjustment(64,0,256,1,16,0)
    self.highlight.connect("value_changed", self.update_value)
    self.shadow.connect("value_changed", self.update_value)


    self.highlightButton = gtk.SpinButton(self.highlight,0,0)
    self.highlightButton.set_numeric(True)
    self.highlightButton.set_digits(0)
    highlightLabel = gtk.Label('highlight')
    highlightLabel.set_alignment(0,0.5)

    self.shadowButton = gtk.SpinButton(self.shadow,0,0)
    self.shadowButton.set_numeric(True)
    self.shadowButton.set_digits(0)
    shadowLabel = gtk.Label('shadow')
    shadowLabel.set_alignment(0,0.5)



    reset = gtk.Button(label="reset")
    reset.set_alignment(0.5,0.5)
    reset.connect("clicked",self.reset)



    bordertable = gtk.Table(rows=2,columns=2,homogeneous=False)
    i = 0
    bordertable.attach(borderLabel,0,1,i,i+1,FILL,EXPAND,5,0)
    bordertable.attach(self.border,1,2,i,i+1,FILL,EXPAND,0,0)
    i += 1
    bordertable.attach(borderColorLabel,0,1,i,i+1,FILL,EXPAND,5,0)
    bordertable.attach(self.borderColor,1,2,i,i+1,FILL,EXPAND,0,0)
    i += 1
    bordertable.attach(highlightLabel,0,1,i,i+1,FILL,EXPAND,5,0)
    bordertable.attach(self.highlightButton,1,2,i,i+1,FILL,EXPAND,0,0)
    i += 1
    bordertable.attach(shadowLabel,0,1,i,i+1,FILL,EXPAND,5,0)
    bordertable.attach(self.shadowButton,1,2,i,i+1,FILL,EXPAND,0,0)
    i += 1
    bordertable.attach(self.bevelButton1,0,1,i,i+1,FILL,EXPAND,5,0)
    bordertable.attach(self.bevelButton2,1,2,i,i+1,FILL,EXPAND,0,0)
    i += 1
    bordertable.attach(reset,0,2,i,i+1,FILL,FILL,5,0)
    bordertable.show_all()






    hbox = gtk.HBox(False,5)
    hbox.pack_start(colortable,False,False,5)
    hbox.pack_start(bordertable,False,False,5)
    hbox.show()
    self.add(hbox)
    self.update_texture()



#################################
########## Color Frame ##########
#################################

class ColorFrame(gtk.Frame):

  def update_value(self,*args):
    if self.callback and self.sensitive:
      self.callback(self.button.get_value())

  def configure(self,name,value,theme):
    self.sensitive = False
    self.button.set_value(value)
    self.sensitive = True

  def __init__(self,**args):
    gtk.Frame.__init__(self,**args)
    self.set_shadow_type(gtk.SHADOW_NONE)
    self.set_label_align(1,0.5)
    self.set_label("color")
    self.callback = None


    self.button = ColorButton()
    self.button.connect("color-set",self.update_value)
    self.add(self.button)
    self.button.show()





###############################################
########## Text Shadows String Frame ##########
###############################################

class TextShadowStringFrame(gtk.Frame):
  def update_value(self,*args):
    if self.shadow.get_active():
     self.value = "shadow=y:shadowtint=%d:shadowoffset=%d" % (self.shadowtint.get_value(), self.shadowoffset.get_value())
    else:
      self.value = "shadow=n"

    self.display.set_text(self.value)
    if self.callback and self.sensitive:
      self.callback(self.value)

  def configure(self,name,string,theme):
    self.sensitive = False
    self.set_value_by_str(string)
    if themeElements[name].has_key('default'):
      self.default=themeElements[name]['default']
    self.sensitive = True

  def reset(self,*args):
    self.shadowtint.set_value(self.default_tint)
    self.shadowoffset.set_value(self.default_offset)
    self._set_value_by_str(self.default)

  def set_value_by_str(self,string):
    self.reset()
    self._set_value_by_str(string)

  def _set_value_by_str(self,string):
    string = string.lower()
    for substr in string.split(":"):
      (name,value) = substr.split("=",1)
      if name == "shadow":
        if value == "y":
          self.shadow.set_active(True)
        else:
          self.shadow.set_active(False)
      elif name == "shadowtint":
        self.shadowtint.set_value(int(value))
      elif name == "shadowoffset":
        self.shadowoffset.set_value(int(value))
    self.update_value

  def get_string(self):
    return self.value

  def __init__(self,**args):
    gtk.Frame.__init__(self,**args)
    self.set_shadow_type(gtk.SHADOW_NONE)
    self.set_label_align(1,0.5)
    self.set_label("text shadow")
    self.callback = None

    self.default = 'shadow=n'
    self.default_tint = 50
    self.default_offset = 1

    self.display = gtk.Entry(max=0)
    self.display.set_editable(False)

    self.shadow = gtk.CheckButton("on/off")
    self.shadow.connect("toggled", self.update_value, "check button 1")

    self.shadowtint = gtk.Adjustment(self.default_tint,-100,100,1,1,0)
    self.shadowtint.connect("value_changed", self.update_value)
    shadowtint_label = gtk.Label("shadow tint:")
    shadowtint_label.set_alignment(0,0)
    shadowtint_spin = gtk.SpinButton(self.shadowtint,0,0)
    shadowtint_spin.set_numeric(True)
    shadowtint_spin.set_digits(0)

    self.shadowoffset = gtk.Adjustment(self.default_offset,-2,2,1,1,0)
    self.shadowoffset.connect("value_changed", self.update_value)
    shadowoffset_label = gtk.Label("shadow offset:")
    shadowoffset_label.set_alignment(0,0)
    shadowoffset_spin = gtk.SpinButton(self.shadowoffset,0,0)
    shadowoffset_spin.set_numeric(True)
    shadowoffset_spin.set_digits(0)

    reset = gtk.Button(label="reset")
    reset.connect("clicked",self.reset)

    table = gtk.Table(2,2)
    i=0
    table.attach(self.display,0,2,i,i+1,FILL,EXPAND,5,5)
    i+=1
    table.attach(shadowtint_label,0,1,i,i+1,FILL,EXPAND,5,5)
    table.attach(shadowtint_spin,1,2,i,i+1,FILL,EXPAND,5,5)
    i+=1
    table.attach(shadowoffset_label,0,1,i,i+1,FILL,EXPAND,5,5)
    table.attach(shadowoffset_spin,1,2,i,i+1,FILL,EXPAND,5,5)
    i+=1
    table.attach(self.shadow,0,1,i,i+1,FILL,EXPAND,5,5)
    table.attach(reset,1,2,i,i+1,FILL,EXPAND,5,5)
    table.show_all()

    self.add(table)
    self.show_all()
    self.update_value()



#################################
########## Theme Class ##########
#################################

class Theme():

  def __init__(self,*args):
    self.elements = {}
    self.palette = Palette(self)
    self.themerc = ''
    self.callback = None

  def get_theme(self,name):
    theme = {}
    f = open(name,'r')
    for line in f:
      m = re.search(r'^\s*([A-Za-z\.\*]+)\s*:\s*(.+?)\s*$',line)
      if m:
        name = m.group(1)
        value = m.group(2)
        if name.find('*') > -1:
          glob_pattern = name
          glob_was_successful = False
          i = glob_pattern.find('.bg.')
          if i > -1:
            glob_pattern = name[0:i+3]
            suffix = name[i+3:]
          else:
            suffix = ''
          glob_pattern = glob_pattern.replace('.','\.')
          glob_pattern = glob_pattern.replace('*','.*')
          for element in themeElements.keys():
            m = re.search("^(%s)$" % glob_pattern,element)
            if m:
              match = m.group(1)
              theme = self.parse_element(match + suffix,value,theme)
              glob_was_successful = True
          if not glob_was_successful:
            print "Warning: failed to match globbing pattern: " + name
        else:
          theme = self.parse_element(name,value,theme)
    f.close()
    return theme

  def parse_element(self,name,value,theme):
    recognized = themeElements.has_key(name)
    if recognized and themeElements[name]['type'] == 'color':
      value = format_ob_color_str(value)
    if recognized and themeElements[name]['type'] == 'texture' and theme.has_key(name):
      theme[name] += "\n" + value
      return theme
    elif recognized:
      theme[name] = value
      return theme
    i = name.find('.bg.')
    if i > -1:
      texture = name[0:i+3]
      texture_attr = name[i+3:]
      if themeElements.has_key(texture) and themeElements[texture]['type'] == 'texture':
        if texture_attr.lower().find('color') > -1:
          value = format_ob_color_str(value)
        if theme.has_key(texture):
          theme[texture] += "\n%s: %s" %(texture_attr,value)
        else:
          theme[texture] = "%s: %s" %(texture_attr,value)
        return theme
    print "Warning: ignoring unrecognized theme element \"%s\"" % name
    return theme


  def load_file(self,name):
    self.elements = self.get_theme(name)
    self.update_palette()
    self.report_change('loaded '+name)



  def __str__(self,*args):
    text =  "#openbox themerc edited with obtheme\n"
    if len(self.elements) > 0:
      elements = self.elements.keys()
      elements.sort()
      for name in elements:
        if self.is_default(name):
          continue
        value = self.elements[name]
        if isinstance(value,StringType) and value.find("\n") > -1:
          for line in value.split("\n"):
            i = line.find(':')
            if i > -1:
              attr = line[:i]
              attr_val = line[i+2:]
              text += "%s%s: %s\n" % (name,attr,attr_val)
            else:
              text += "%s: %s\n" % (name,line)
        else:
          text += "%s: %s\n" % (name,value)
    return text


  def save_file(self,file_name):
    text = self.__str__()
    return write_file(file_name,text)

  def is_default(self,element):
    if not self.elements.has_key(element):
      return True
    value = self.elements[element]
    if value == '':
      return True
    if themeElements.has_key(element) and themeElements[element].has_key('default'):
      default = themeElements[element]['default']
      if default.lower() == 'none':
        return False
      elif default.find('.') > -1:
        return (self.get_value(default) == value)
    return False

  def get_value(self,element):
    if self.elements.has_key(element):
      return self.elements[element]
    elif themeElements.has_key(element) and themeElements[element].has_key('default'):
      default = themeElements[element]['default']
      if default.lower() == 'none':
        return ''
      elif default.find('.') > -1:
        return self.get_value(default)
      else:
        return default
    else:
      return ''

  def extract_colors(self,key,value):
    colors = []
    if key[-6:].lower() == '.color':
      colors.append(value)
    elif isinstance(value,StringType) and value.find("\n")>-1:
      for line in value.split("\n"):
        m = re.search(r'\s*^\S*\.color(?:To)?\s*:\s*(.*?)\s*$',line)
        if m:
          colors.append(m.group(1))
    return colors

  def set_value(self,key,value):
    #if not self.elements.has_key(key):
    #  print "new key:", key
    self.elements[key] = value
    for color in self.extract_colors(key,value):
      self.palette.add_color(color,True)
    self.report_change("set %s -> %s" % (key,value))

  def get_palette(self,theme):
    palette = set()
    for key,value in theme.iteritems():
      for color in self.extract_colors(key,value):
        palette.add(color)
    return palette

  def update_palette(self):
    self.palette.set_theme_palette(self.get_palette(self.elements))
    self.report_change("updated palette")

  def import_palette(self,path):
    theme = self.get_theme(path)
    palette = self.get_palette(theme)
    self.palette.import_palette(palette)

  def replace_color(self,old,new):
    replaced = False
    for key,value in self.elements.iteritems():
      if (key[-6:].lower() == '.color' and value == old) \
      or (themeElements.has_key(key) and themeElements[key]['type'] == 'texture' and value.find(old) > -1):
        self.elements[key] = value.replace(old,new)
        if not replaced:
          replaced = True
    if replaced:
      self.palette.add_color(new,True)
      self.report_change("replaced %s with %s" % (old,new))

  def report_change(self,what=None):
    #print what
    themerc = self.__str__()
    if themerc != self.themerc:
      self.themerc = themerc
      if self.callback:
        self.callback(themerc)




############################################
########## Theme Element Selector ##########
############################################

class ThemeElementSelector(gtk.ScrolledWindow):
  def select(self,listview,*args):
    selection = listview.get_selection()
    (model,iter) = selection.get_selected()
    element =  model.get_value(iter, 0)
    if self.callback:
      self.callback(element)


  def __init__(self,**args):
    gtk.ScrolledWindow.__init__(self,**args)
    self.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
    self.callback = None

    self.liststore = gtk.ListStore(str,str)
    elements = themeElements.keys()
    elements.sort()
    for element in elements:
      self.liststore.append([element,themeElements[element]['type']])

    self.listview = gtk.TreeView(self.liststore)
    self.listview.set_rules_hint(True)
    self.listview.connect('cursor-changed', self.select, self.listview)

    i = 0
    for col in ('element','type'):
      tvcol = gtk.TreeViewColumn(col)
      cell = gtk.CellRendererText()
      tvcol.pack_start(cell, True)
      tvcol.add_attribute(cell, 'text', i)
      tvcol.set_sort_column_id(i)
      self.listview.append_column(tvcol)
      i += 1

    self.listview.set_reorderable(True)
    self.set_size_request(500, 100)

    self.add(self.listview)
    self.show_all()



#########################################
########## Theme File Selector ##########
#########################################

class ThemeFileSelector(gtk.ScrolledWindow):

  def select(self,treeview,event):
    if event.type == gtk.gdk._2BUTTON_PRESS:
      x = int(event.x)
      y = int(event.y)
      time = event.time
      pthinfo = treeview.get_path_at_pos(x, y)
      if pthinfo is not None:
        path, col, cellx, celly = pthinfo
        treeview.set_cursor( path, col, 0)
        selection = treeview.get_selection()
        (model,iter) = selection.get_selected()
        path =  model.get_value(iter, 1)
        #self.popup.popup( None, None, None, event.button, time)
        if self.callback:
          self.callback(path,event.button)


  def get_selected(self):
    selection = self.listview.get_selection()
    (model,iter) = selection.get_selected()
    return model.get_value(iter, 1)
    #selection = listview.get_selection()
    #(model,iter) = selection.get_selected()
    #self.selected =  model.get_value(iter, 1)


  def get_themes(self):
    themes = {}
    theme_dir_path = os.getenv('HOME')+'/.themes'
    if os.path.exists(theme_dir_path):
      for theme in os.listdir(theme_dir_path):
        if theme == 'obtheme':
          continue
        themerc_path = "%s/%s/openbox-3/themerc" % (theme_dir_path,theme)
        if os.path.exists(themerc_path):
          themes[theme] = themerc_path
    theme_dir_path = '/usr/share/themes'
    if os.path.exists(theme_dir_path):
      for theme in os.listdir(theme_dir_path):
        themerc_path = "%s/%s/openbox-3/themerc" % (theme_dir_path,theme)
        if os.path.exists(themerc_path):
          themes[theme] = themerc_path
    return themes



  def __init__(self,**args):
    gtk.ScrolledWindow.__init__(self,**args)
    self.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
    self.themes = self.get_themes()
    self.selected = None
    self.callback = None

    self.liststore = gtk.ListStore(str,str)
    names = self.themes.keys()
    names.sort()
    for name in names:
      self.liststore.append([name,self.themes[name]])

    self.listview = gtk.TreeView(self.liststore)
    #self.listview.set_rules_hint(True)
    #self.listview.connect('cursor-changed', self.get_selected, self.listview)
    self.listview.connect('button_press_event', self.select)

    i = 0
    for col in ('theme','path'):
      tvcol = gtk.TreeViewColumn(col)
      cell = gtk.CellRendererText()
      tvcol.pack_start(cell, True)
      tvcol.add_attribute(cell, 'text', i)
      tvcol.set_sort_column_id(i)
      self.listview.append_column(tvcol)
      i += 1

    self.listview.set_reorderable(True)
    self.set_size_request(100, 100)

    self.add(self.listview)
    self.show_all()



#############################
########## Palette ##########
#############################

class Palette(gtk.Frame):

  def __init__(self,theme,*args):
    gtk.Frame.__init__(self,*args)
    self.set_shadow_type(gtk.SHADOW_NONE)
    self.set_label_align(1,0.5)
    self.set_label("palette")

    self.color_set = set()
    self.used_set = set()
    self.color_list = []
    self.swatch_map = {}
    self.selected = None
    self.colorseldlg = None
    self.theme = theme
    self.swatch_dim = 25

    self.area = gtk.DrawingArea()
    self.area.set_events(gtk.gdk.EXPOSURE_MASK | gtk.gdk.BUTTON_PRESS_MASK)
    self.area.connect("expose_event", self.expose)
    self.area.connect("button_press_event", self.button_press)
    self.area.drag_dest_set(0,[],0)
    self.area.drag_source_set(gtk.gdk.BUTTON1_MASK,[],0)
    self.area.connect("drag_motion", self.drag_motion)
    self.area.connect("drag_drop", self.drag_drop)
    self.area.connect("drag_begin", self.drag_begin)
    self.area.connect("drag_data_get", self.drag_data_get)


    self.sw = gtk.ScrolledWindow()
    self.sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
    self.sw.add_with_viewport(self.area)
    self.area.show()

    self.menu = gtk.Menu()
    self.menu.set_title('Palette')
    menu_simplify = gtk.ImageMenuItem('_Simplify')
    self.menu.append(menu_simplify)
    menu_simplify.connect('activate',self.simplify)
    menu_simplify.show()

    self.add(self.sw)
    self.show_all()

    self.update_dimensions()


  def simplify(self,*args):
    self.color_set = set()
    self.theme.update_palette()


  def update(self):
    self.color_list = list(self.color_set)
    self.color_list.sort()
    self.draw_swatches()

  def set_theme_palette(self,palette):
    self.used_set = palette
    self.color_set.update(palette)
    self.update()

  def import_palette(self,palette):
    self.color_set.update(palette)
    self.update()

  def add_color(self,color,used=False):
    self.color_set.add(color)
    if used:
      self.used_set.add(color)
    self.update()

  def remove_color(self,color):
    if color in self.color_set:
      self.color_set.remove(color)
      self.update()

  def replace_color(self,old,new):
    if not new in self.color_set:
      self.color_set.add(new)
    if old in self.color_set:
      self.color_set.remove(old)
    self.theme.replace_color(old,new)
    self.update()

  def get_width(self):
    x1,y1,w1,h1 = self.sw.get_allocation()
    x2,y2,w2,h2 = self.sw.get_vscrollbar().get_allocation()
    w = w1 - w2
    if w < self.swatch_dim:
      return self.swatch_dim
    return w

  def update_dimensions(self):
    self.width = self.get_width()
    columns  = self.width/self.swatch_dim
    rows = int(math.ceil(float(len(self.color_set))/columns))
    self.height = rows * self.swatch_dim
    w = self.get_width()/self.swatch_dim
    self.area.set_size_request(w,self.height)
    return

  def map_swatch(self,x,y):
    for color in self.swatch_map.keys():
      if x >= self.swatch_map[color]['x1'] \
      and x <= self.swatch_map[color]['x2'] \
      and y >= self.swatch_map[color]['y1'] \
      and y <= self.swatch_map[color]['y2']:
        return color
    return None

  def get_color(self,default='#000000'):
    if self.colorseldlg == None:
      self.colorseldlg = gtk.ColorSelectionDialog("choose a replacement color")
    colorsel = self.colorseldlg.colorsel
    colorsel.set_current_color(str_to_color(default))
    response = self.colorseldlg.run()
    if response -- gtk.RESPONSE_OK:
      new_color = color_to_str(colorsel.get_current_color())
    else:
      new_color = None
    self.colorseldlg.hide()
    return new_color

  def button_press(self,area,event):
    if event.button == 1:
      self.selected = self.map_swatch(event.x,event.y)
      if event.type == gtk.gdk._2BUTTON_PRESS:
        if self.selected:
          new_color = self.get_color(self.selected)
          if new_color != None and new_color != self.selected:
            self.replace_color(self.selected,new_color)
        else:
          self.add_color(self.get_color())
    elif event.button == 3:
      self.menu.popup(None, None, None, event.button, event.time)

  def get_value(self):
    return self.selected

  def drag_color(self, widget, context, selection, info, time):
    #context.drag_status(gtk.gdk.ACTION_COPY, time)
    return True

  def drag_motion(self, widget, context, x, y, time):
    context.drag_status(gtk.gdk.ACTION_COPY, time)
    return True

  def drag_drop(self, widget, context, x, y, time):
    source_widget = context.get_source_widget()
    new_color = None
    if source_widget.__class__.__name__ == 'ColorButton':
      new_color = source_widget.get_value()
    else:
      source_widget = source_widget.get_parent()
      if source_widget.__class__.__name__ == 'ThemeFileSelector':
        path = source_widget.get_selected()
        self.theme.import_palette(path)
        return
      else:
        source_widget = source_widget.get_parent().get_parent()
        if source_widget.__class__.__name__ == 'Palette':
          new_color = source_widget.get_value()
    old_color = self.map_swatch(x,y)
    if new_color != None:
      if old_color != None and old_color != new_color:
        self.replace_color(old_color,new_color)
      elif old_color == None:
        self.add_color(new_color)
    context.finish(True, False, time)
    return True

  def drag_begin(self, widget, context, *args):
    #context.drag_status(gtk.gdk.ACTION_COPY, time)
    return True

  def drag_data_get(self, widget, context, x, y, time):
    return True

  def expose(self, area, event):
    self.update_dimensions()
    self.draw_swatches()
    return True

  def draw_swatches(self):
    i = 0
    w = self.swatch_dim
    divisor = self.width/w
    self.swatch_map = {}
    gc = self.area.window.new_gc()
    gc.set_rgb_fg_color(str_to_color('#eeeeee'))
    self.area.window.draw_rectangle(gc, True, *self.area.get_allocation())
    for color in self.color_list:
      self.swatch_map[color] = {}
      y,x = divmod(i,divisor)
      self.draw_swatch(x*w,y*w,w,color,gc)
      i += 1
    return

  def draw_swatch(self, x, y, w, color, gc=None):
    if gc == None:
      gc = self.area.window.new_gc()
    gc.set_rgb_fg_color(str_to_color('#000000'))
    self.area.window.draw_rectangle(gc, False, x, y, w, w)
    x1 = x+1
    y1 = y+1
    w1 = w-2
    gc.set_rgb_fg_color(str_to_color(color))
    self.area.window.draw_rectangle(gc, True, x1, y1, w1, w1)
    if color not in self.used_set:
      gc.set_rgb_fg_color(str_to_color('#eeeeee'))
      self.area.window.draw_polygon(gc, True, [(x1, y1), (x1+w1/2,y1), (x1,y1+w1/2)])
      gc.set_rgb_fg_color(str_to_color('#000000'))
      self.area.window.draw_line(gc, x1+w1/2, y1, x1, y1+w1/2)
    self.swatch_map[color]['x1'] = x1
    self.swatch_map[color]['x2'] = x1+w1
    self.swatch_map[color]['y1'] = y1
    self.swatch_map[color]['y2'] = y1+w1
    #if color == self.selected:
    #  pass
    return



#############################
########## ObTHeme ##########
#############################

class ObTheme:

  def display_about(self,*args):
    about_msg = "ObTheme %s\n\n GTK+ Openbox theme editor \n\nCopyright \302\251 2009 Xyne " % VERSION

    label = gtk.Label(about_msg)
    label.set_justify(gtk.JUSTIFY_CENTER)

    dialog = gtk.Dialog(None,None,gtk.DIALOG_DESTROY_WITH_PARENT,('_Close',1))
    dialog.set_title("About ObTheme")
    dialog.vbox.pack_start(label,False,True,10)
    dialog.vbox.show_all()
    response = dialog.run()
    dialog.destroy()


  def display_help(self,*args):
    help_msg = '''Most things in ObTheme are hopefully self-explanatory. Here are a few things which might not be:

The Palette
The palette displays the global set of colors as a set of swatches. Full swatches are colors used by the currently loaded theme. If you change a color in the palette, all elements in the theme which use that color will be updated to use the new one.

Double-click a swatch to open the color selection dialogue and change the color.
Swatches and color buttons can be dragged onto each other to replace colors.
Right-click the palette to bring up the context menu. "Simplify" will remove all unused colors from the palette.
Drag a theme from the theme list onto the palette to add its colors to the palette.

The Theme List
Double-left-click a theme to open it.
Double-right-click a theme to import it.
The difference between opening and importing is that importing does not set the current file name to the loaded theme.

Preview Mode
Theme->"Preview" will display a live version of the theme so you can see changes immediately.

Review the Openbox theme specification at http://openbox.org/wiki/Help:Themes for further information.
'''


    textview = gtk.TextView()
    textview.get_buffer().set_text(help_msg)
    textview.set_editable(False)
    textview.set_wrap_mode(gtk.WRAP_WORD)
    textview.set_left_margin(5)
    textview.set_right_margin(5)

    textview_window = gtk.ScrolledWindow()
    textview_window.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
    textview_window.add(textview)

    dialog = gtk.Dialog(None,None,gtk.DIALOG_DESTROY_WITH_PARENT,('_Close',1))
    dialog.set_title("ObTheme Info")
    dialog.set_default_size(600,500)
    dialog.vbox.pack_start(textview_window,True,True,5)
    dialog.vbox.show_all()
    response = dialog.run()
    dialog.destroy()


  def select(self,element,*args):
    if themeElements.has_key(element):
      typ = themeElements[element]['type']
      has_default = themeElements[element].has_key('default')
      if has_default:
        text = "Default: %s\n" % themeElements[element]['default']
      else:
        text = ''
      if themeElements[element].has_key('info'):
        text += themeElements[element]['info']
      self.info.get_buffer().set_text(text)

      self.selection = element
      value = self.theme.get_value(element.lower())

    else:
      typ = None
      self.selection = None
    for frame in self.frames.keys():
      if typ == frame:
        self.frames[frame].set_sensitive(True)
        if value != None:
          self.frames[frame].configure(element,value,self.theme)
      else:
        self.frames[frame].set_sensitive(False)

  def refresh(self,themerc):
    self.themerc = themerc
    if self.selection:
      self.select(self.selection)
    if self.preview_mode:
      self.save_and_reconfigure()

  def get_themerc(self):
    if not self.themerc:
      self.themerc=str(self.theme)
    return self.themerc


  def update(self,string):
    if self.selection != None:
      self.theme.set_value(self.selection,string)
      self.unsaved = True

  def delete_event(self, widget, event, data=None):
    if self.unsaved:
      label = gtk.Label("Would you like to save the theme file?")
      dialog = gtk.Dialog(None,None,gtk.DIALOG_DESTROY_WITH_PARENT,('Discard',0,'Cancel',1,'Save',2))
      dialog.vbox.pack_start(label,True,True,5)
      label.show()
      response = dialog.run()
      dialog.destroy()
      if response == 1:
        return True
      elif response == 2:
        self.save_theme()
    self.unmount_preview_dir()
    self.restore()
    return False

  def install(self,widget,arg=None,*args):
    if arg == 'install as':
      label = gtk.Label("Choose a name for this theme.")
      entry = gtk.Entry()
      dialog = gtk.Dialog(None,None,gtk.DIALOG_DESTROY_WITH_PARENT,('Cancel',0,'Install',1))
      dialog.vbox.pack_start(label,True,True,5)
      dialog.vbox.pack_start(entry,True,True,5)
      dialog.vbox.show_all()
      response = dialog.run()
      if response == 1:
        name = entry.get_text()
        dpath = os.getenv('HOME')+'/.themes/'+name+'/openbox-3'
        if not os.path.exists(dpath):
          os.makedirs(dpath)
        self.file_name = dpath + '/themerc'
        self.save_theme()
      dialog.destroy()

  def destroy(self, widget, data=None):
    gtk.main_quit()

  def set_title(self,title=None,*args):
    if title:
      self.window.set(title)
    elif self.file_name:
      self.window.set_title(self.file_name)

  def open_from_list(self,path,button):
    self.theme.load_file(path)
    if button == 1:
      self.set_title()
      self.file_name = path

  def open_theme(self,widget,arg=None,*args):
    name = self.file_name
    dialog = gtk.FileChooserDialog('Select an Openbox theme file',None,gtk.FILE_CHOOSER_ACTION_OPEN,
     (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    if name != None:
      dialog.set_current_folder(os.path.dirname(name))
    dialog.set_default_response(gtk.RESPONSE_OK)
    response = dialog.run()
    if response == gtk.RESPONSE_OK:
      name = dialog.get_filename()
    else:
      name = None
    dialog.destroy()
    if name != None:
      self.theme.load_file(name)
      if arg != 'import':
        self.set_title()
        self.file_name = name
      for item in os.listdir(self.preview_themerc_dir):
        if item[-4:] == '.xbm':
          os.remove(self.preview_themerc_dir+'/'+item)
      dpath = os.path.dirname(name)
      for item in os.listdir(dpath):
        if item[-4:] == '.xbm':
          shutil.copyfile(dpath+'/'+item,self.preview_themerc_dir+'/'+item)

  def save_theme(self,widget=None,arg=None,*args):
    name = self.file_name
    if name == None or arg == 'save as':
      if arg == 'save as':
        button = gtk.STOCK_SAVE_AS
      else:
        button = gtk.STOCK_SAVE
      dialog = gtk.FileChooserDialog('Select an Openbox theme file',None,gtk.FILE_CHOOSER_ACTION_SAVE,
       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, button, gtk.RESPONSE_OK))
      if name != None:
        dialog.set_current_folder(os.path.dirname(name))
        dialog.set_current_name(os.path.basename(name))
      dialog.set_default_response(gtk.RESPONSE_OK)
      response = dialog.run()
      if response == gtk.RESPONSE_OK:
        name = dialog.get_filename()
      dialog.destroy()
    if name != None:
      self.file_name = name
      if self.theme.save_file(name):
        self.set_title()
        self.unsaved = False
        dpath = os.path.dirname(name)
        if os.path.exists(self.preview_themerc_dir):
          if not os.path.exists(dpath):
            os.makedirs(dpath)
          for item in os.listdir(self.preview_themerc_dir):
            if item[-4:] == '.xbm':
              shutil.copyfile(self.preview_themerc_dir+'/'+item,dpath+'/'+item)
      else:
        #self.file_name = None
        self.save_theme(None,'save as')



  def get_theme(self,theme):
    rc_xml = read_file(self.openbox_config_path)
    m = re.search(r'<theme>.*?<name>(.*?)<\/name>',rc_xml,re.S)
    if m:
      return m.group(1)
    else:
      return None


  def set_theme(self,theme):
    rc_xml = read_file(self.openbox_config_path)
    m = re.search(r'(^.*?<theme>.*?<name>)(.*?)(<\/name>.*$)',rc_xml,re.S)
    if m:
      prev_theme = m.group(2)
      if theme == prev_theme:
        return True
      if prev_theme != 'obtheme':
        self.previous_theme = prev_theme
      rc_xml = m.group(1) + theme + m.group(3)
      if write_file(self.openbox_config_path,rc_xml):
        print "changed theme in rc.xml: %s -> %s" % (prev_theme,theme)
        self.reconfigure()
        return True
    sys.stderr.write("unable to parse theme element of %s\n" % rc_xml_path)
    return False

  def save_preview(self):
    if os.path.exists(self.preview_themerc_dir):
      write_file(self.preview_themerc_dir+'/themerc',self.get_themerc())

  def save_and_reconfigure(self):
    self.save_preview()
    self.reconfigure()

  def reconfigure(self):
    if self.preview_mode:
      try:
        subprocess.call(['openbox','--reconfigure'])
      except OSError:
        self.restore()
        sys.stderr.write("Error: unable to reconfigure openbox\n")
      except:
        sys.stderr.write("Unexpected error: %s" % sys.exc_info()[0])
        raise

  def toggle_preview_mode(self,widget):
    if widget.get_active():
      self.preview()
    else:
      self.restore()
    self.preview_mode = widget.get_active()

  def preview(self,*args):
    if self.preview_dir_is_mounted():
      self.save_preview()
      self.set_theme('obtheme')
      self.preview_mode = True
    else:
      self.restore()

  def restore(self,*args):
    if self.previous_theme != None:
      self.set_theme(self.previous_theme)
      self.previous_theme = None
    self.preview_mode = False
    self.preview_mode_checkbox.set_active(False)


  def __init__(self):
    self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.window.set_title("ObTheme")
    self.window.connect("destroy", self.destroy)
    self.window.connect("delete_event", self.delete_event)
    self.window.set_position(gtk.WIN_POS_CENTER)

    accel_group = gtk.AccelGroup()
    self.window.add_accel_group(accel_group)

    self.preview_themerc_dir = os.getenv('HOME') + '/.themes/obtheme/openbox-3'
    config_home = os.getenv('XDG_CONFIG_HOME')
    if not config_home:
      config_home = os.getenv('HOME') + '/.config'
      sys.stderr.write("Error: the environment variable \"XDG_CONFIG_HOME\" is not set\nDefaulting to %s.\n" % config_home)
    self.openbox_config_path = config_home + '/openbox/rc.xml'

    self.theme = Theme()
    self.theme.callback = self.refresh

    self.selection = None
    self.previous_theme = None
    self.file_name = None
    self.unsaved = False
    self.preview_mode = False
    self.themerc = None

    file_menu_open = gtk.ImageMenuItem('_Open...')
    file_menu_open.connect("activate", self.open_theme,'open')
    file_menu_open.add_accelerator("activate",accel_group,ord('o'),gtk.gdk.CONTROL_MASK,gtk.ACCEL_VISIBLE)
    file_menu_open.set_image(gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_MENU))

    file_menu_save = gtk.ImageMenuItem('_Save')
    file_menu_save.connect("activate", self.save_theme,'save')
    file_menu_save.add_accelerator("activate",accel_group,ord('s'),gtk.gdk.CONTROL_MASK,gtk.ACCEL_VISIBLE)
    file_menu_save.set_image(gtk.image_new_from_stock(gtk.STOCK_SAVE, gtk.ICON_SIZE_MENU))

    file_menu_save_as = gtk.ImageMenuItem('Save _As...')
    file_menu_save_as.connect("activate", self.save_theme,'save as')
    file_menu_save_as.add_accelerator("activate",accel_group,ord('s'),(gtk.gdk.CONTROL_MASK|gtk.gdk.SHIFT_MASK),gtk.ACCEL_VISIBLE)
    file_menu_save_as.set_image(gtk.image_new_from_stock(gtk.STOCK_SAVE_AS, gtk.ICON_SIZE_MENU))

    #file_menu_install_as = gtk.ImageMenuItem('Install As...')
    #file_menu_install_as.connect("activate", self.install,'install as')
    #file_menu_install_as.add_accelerator("activate",accel_group,ord('i'),gtk.gdk.CONTROL_MASK,gtk.ACCEL_VISIBLE)
    #file_menu_install_as.set_image(gtk.image_new_from_stock(gtk.STOCK_SAVE_AS, gtk.ICON_SIZE_MENU))

    #file_menu_import = gtk.ImageMenuItem('_Import...')
    #file_menu_import.connect("activate", self.open_theme, 'import')
    #file_menu_import.add_accelerator("activate",accel_group,ord('i'),gtk.gdk.CONTROL_MASK,gtk.ACCEL_VISIBLE)
    #file_menu_import.set_image(gtk.image_new_from_stock(gtk.STOCK_SAVE_AS, gtk.ICON_SIZE_MENU))

    file_menu_separator = gtk.SeparatorMenuItem()

    file_menu_quit = gtk.ImageMenuItem("_Quit")
    file_menu_quit.connect("activate", self.destroy)
    file_menu_quit.add_accelerator("activate",accel_group,ord('q'),gtk.gdk.CONTROL_MASK,gtk.ACCEL_VISIBLE)
    file_menu_quit.set_image(gtk.image_new_from_stock(gtk.STOCK_QUIT, gtk.ICON_SIZE_MENU))

    file_submenu = gtk.Menu()
    file_submenu.append(file_menu_open)
    file_submenu.append(file_menu_save)
    file_submenu.append(file_menu_save_as)
    #file_submenu.append(file_menu_install_as)
    #file_submenu.append(file_menu_import)
    file_submenu.append(file_menu_separator)
    file_submenu.append(file_menu_quit)
    file_submenu.show_all()

    file_menu = gtk.ImageMenuItem("_File")
    file_menu.set_submenu(file_submenu)
    file_menu.show()

    theme_menu_import = gtk.ImageMenuItem('_Import...')
    theme_menu_import.connect("activate", self.open_theme, 'import')
    theme_menu_import.add_accelerator("activate",accel_group,ord('i'),gtk.gdk.CONTROL_MASK,gtk.ACCEL_VISIBLE)
    #theme_menu_import.set_image(gtk.image_new_from_stock(gtk.STOCK_REVERT_TO_SAVED, gtk.ICON_SIZE_MENU))

    theme_menu_preview = gtk.CheckMenuItem('_Preview')
    theme_menu_preview.connect("toggled", self.toggle_preview_mode)
    theme_menu_preview.add_accelerator("activate",accel_group,ord('p'),gtk.gdk.CONTROL_MASK,gtk.ACCEL_VISIBLE)
    #theme_menu_preview.set_image(gtk.image_new_from_stock(gtk.STOCK_REVERT_TO_SAVED, gtk.ICON_SIZE_MENU))
    self.preview_mode_checkbox = theme_menu_preview

    #theme_menu_restore = gtk.ImageMenuItem('_Restore')
    #theme_menu_restore.connect("activate", self.restore)
    #theme_menu_restore.add_accelerator("activate",accel_group,ord('r'),gtk.gdk.CONTROL_MASK,gtk.ACCEL_VISIBLE)
    #theme_menu_restore.set_image(gtk.image_new_from_stock(gtk.STOCK_REVERT_TO_SAVED, gtk.ICON_SIZE_MENU))

    theme_submenu = gtk.Menu()
    theme_submenu.append(theme_menu_import)
    theme_submenu.append(theme_menu_preview)
    #theme_submenu.append(theme_menu_restore)
    theme_submenu.show_all()

    theme_menu = gtk.ImageMenuItem("_Theme")
    theme_menu.set_submenu(theme_submenu)
    theme_menu.show()

    info_menu = gtk.ImageMenuItem('_Info')
    info_menu.connect("activate", self.display_help)
    info_menu.add_accelerator("activate",accel_group,ord('h'),gtk.gdk.CONTROL_MASK,gtk.ACCEL_VISIBLE)
    info_menu.set_image(gtk.image_new_from_stock(gtk.STOCK_INFO, gtk.ICON_SIZE_MENU))

    about_menu = gtk.ImageMenuItem('_About')
    about_menu.connect("activate", self.display_about)
    #about_menu.add_accelerator("activate",accel_group,ord('h'),gtk.gdk.CONTROL_MASK,gtk.ACCEL_VISIBLE)
    about_menu.set_image(gtk.image_new_from_stock(gtk.STOCK_ABOUT, gtk.ICON_SIZE_MENU))

    help_submenu = gtk.Menu()
    help_submenu.append(info_menu)
    help_submenu.append(about_menu)
    help_submenu.show_all()

    help_menu = gtk.ImageMenuItem("_Help")
    help_menu.set_submenu(help_submenu)
    help_menu.show()

    xbm_menu = gtk.ImageMenuItem('_XBM Editor')
    #xbm_menu.connect("activate", self.open_xbm_editor)
    xbm_menu.connect("activate", os.system('python xbm-editor'))
    xbm_menu.add_accelerator("activate",accel_group,ord('x'),gtk.gdk.CONTROL_MASK,gtk.ACCEL_VISIBLE)
    #xbm_menu.set_image(gtk.image_new_from_stock(gtk.STOCK_ABOUT, gtk.ICON_SIZE_MENU))

    tools_submenu = gtk.Menu()
    tools_submenu.append(xbm_menu)
    tools_submenu.show_all()

    tools_menu = gtk.ImageMenuItem("Too_ls")
    tools_menu.set_submenu(tools_submenu)
    tools_menu.show()

    menu_bar = gtk.MenuBar()
    menu_bar.append(file_menu)
    menu_bar.append(theme_menu)
    menu_bar.append(tools_menu)
    menu_bar.append(help_menu)



    self.frames = {}
    integer = IntegerFrame()
    self.frames['integer'] = integer
    integer.callback=self.update

    color = ColorFrame()
    self.frames['color'] = color
    color.callback=self.update

    text_shadow_string = TextShadowStringFrame()
    self.frames['text shadow string'] = text_shadow_string
    text_shadow_string.callback=self.update

    justification = JustificationFrame()
    self.frames['justification'] = justification
    justification.callback=self.update

    texture = TextureFrame()
    self.frames['texture'] = texture
    texture.callback=self.update


    infopanel = gtk.ScrolledWindow()
    infopanel.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
    infolabel = gtk.Label(' information:')
    infolabel.set_alignment(0,1)
    self.info = gtk.TextView()
    self.info.set_wrap_mode(gtk.WRAP_WORD)
    self.info.set_left_margin(5)
    self.info.set_right_margin(5)
    self.info.set_size_request(400,50)
    self.info.set_editable(False)
    infopanel.add(self.info)

    theme_element_selector = ThemeElementSelector()
    theme_element_selector.callback = self.select
    themelist = ThemeFileSelector()
    themelist.callback = self.open_from_list


    hpane = gtk.HPaned()
    hpane.add1(theme_element_selector)
    hpane.add2(themelist)
    hpane.show_all()

    vpane = gtk.VPaned()
    vpane.add1(infopanel)
    vpane.add2(hpane)
    vpane.show_all()


    table = gtk.Table(rows=7,columns=4,homogeneous=False)
    i = 0
    j = 0
    table.attach(integer,i,i+2,j,j+1)
    i += 2
    table.attach(texture,i,i+1,j,j+3)
    i = 0
    j += 1
    table.attach(color,i,i+1,j,j+1)
    i += 1
    table.attach(justification,i,i+1,j,j+1)
    i = 0
    j += 1
    table.attach(text_shadow_string,i,i+2,j,j+1)
    table.show_all()


    hbox = gtk.HBox()
    hbox.pack_start(table,False,False,2)
    hbox.pack_start(self.theme.palette,True,True,2)
    hbox.show_all()


    vbox = gtk.VBox()
    vbox.pack_start(menu_bar,False,False,2)
    vbox.pack_start(hbox,False,False,2)
    vbox.pack_start(infolabel,False,False,2)
    vbox.pack_start(vpane,True,True,2)
    vbox.show_all()




    self.select(None)
    self.window.add(vbox)
    self.window.show_all()
    self.window.show()


  def unmount_preview_dir(self):
    if self.preview_dir_is_mounted():
      subprocess.call(['fusermount','-u',self.preview_themerc_dir])

  def preview_dir_is_mounted(self):
    mtab = read_file('/etc/mtab')
    if mtab.find(self.preview_themerc_dir) > -1:
      return True
    else:
      return False

  def main(self):
    gtk.main()

  def open_xbm_editor(self,*args):
    editor = XBMWindow()
    editor.callback = self.reconfigure

def start_fuse(fuse_obj,path):
  fuse_obj.main(['',path])






class MyStat(Stat):
  def __init__(self):
    self.st_mode = stat.S_IFDIR | 0755
    self.st_ino = 0
    self.st_dev = 0
    self.st_nlink = 2
    self.st_uid = os.getuid()
    self.st_gid = os.getgid()
    self.st_size = 4096
    self.st_atime = 0
    self.st_mtime = 0
    self.st_ctime = 0


class SimpleDir(Fuse):
  fuse.fuse_python_api =  (0,2)

  def __init__(self, *args, **kw):
    Fuse.__init__(self, *args, **kw)
    self.flags = 0
    self.multithreaded = 0
    self.files = {}
    #self.files['themerc'] = ''

  def getattr(self, path):
    st = MyStat()
    pe = path.split('/')[1:]

    st.st_atime = int(time())
    st.st_mtime = st.st_atime
    st.st_ctime = st.st_atime
    if path == '/':
       pass
    elif self.files.has_key(path[1:]):
       st.st_mode = stat.S_IFREG | 0666
       st.st_nlink = 1
       st.st_size = len(self.files[path[1:]])
    else:
       return -errno.ENOENT
    return st

  def readdir(self, path, offset):
    dirents = [ '.', '..' ]
    if path == '/':
      dirents.extend(self.files.keys())
    for r in dirents:
      yield fuse.Direntry(r)

  def read(self, path, size, offset):
    if self.files.has_key(path[1:]):
      return self.files[path[1:]][offset:offset+size]
    else:
      return -errno.ENOENT

  def write(self, path, buf, offset):
    l = len(buf)
    if self.files.has_key(path[1:]):
      if offset == 0:
        self.files[path[1:]] = ''
      self.files[path[1:]] += buf
      return l
    else:
      return -errno.ENOENT

  def mknod(self, path, mode, dev):
    if len(path) > 1:
      self.files[path[1:]] = ''
    return 0

  def unlink(self, path):
    if self.files.has_key(path[1:]):
      del self.files[path[1:]]
    return 0

  def open(self, path, flags):
    return 0

  def truncate(self, path, size):
    return 0

  def chown(self,*args):
    return 0

  def utime(self, path, times):
    return 0

  def mkdir(self, path, mode):
    return 0

  def rmdir(self, path):
    return 0

  def rename(self, pathfrom, pathto):
    return 0

  def fsync(self, path, isfsyncfile):
    return 0

  def release(self, path, flags):
    return 0

































################################
########## XBM Editor ##########
################################

class XBMEditor(gtk.Frame):

  def xbm_data_to_bool_array(self,data,width):
    bin_str = ''
    i = 0
    for byte in data:
      if byte[:2] == '0x':
        dec = int(byte[2:],16)
      else:
        dec = int(byte)
      hex_str = "%02x" % dec
      bin = self.hex_map[hex_str[:1]] + self.hex_map[hex_str[1:]]
      bin = bin[::-1]
      i+=8
      if i >= width:
        bin = bin[:((width+8)-i)]
        i = 0
      bin_str += bin
    bool_arr = []
    for bit in bin_str:
      bool_arr.append(bit == '1')
    return bool_arr

  def open_xbm(self,path):
    data = read_file(path)
    m = self.re_width.search(data)
    if m:
      width = int(m.group(1))
    else:
      sys.stderr.write("Error: unable to detect XBM width in %s\n" % path)
      return None,None,None
    m = self.re_height.search(data)
    if m:
      height = int(m.group(1))
    else:
      sys.stderr.write("Error: unable to detect XBM height in %s\n" % path)
      return None,None,None
    m = self.re_data.search(data)
    if m:
      bool_arr = self.xbm_data_to_bool_array(self.re_split.split(m.group(1)),width)
    else:
      sys.stderr.write("Error: unable to detect XBM mask in %s\n" % path)
      return None,None,None
    return width, height, bool_arr

  def load_xbm(self,path):
    width,height,bool_arr = self.open_xbm(path)
    if width != None:
      self.width = width
      self.height = height
      self.bool_arr = bool_arr
      self.set_size()
      self.draw_xbm()
      return True
    else:
      return False

  def bool_array_to_xbm_data(self,bool_arr):
    bin_str = ''
    hex_str = ''
    i = 0
    for val in bool_arr:
      if val:
        bin_str += '1'
      else:
        bin_str += '0'
      i += 1
      if i == self.width:
        m = self.width % 8
        if m > 0:
          bin_str += '0' * (8-m)
        i = 0
      if len(bin_str) == 8:
        if len(hex_str) > 0:
          hex_str += ', '
        hex_str += "0x%02x" % int(bin_str[::-1],2)
        bin_str = ''
    hex_str.strip()
    hex_str.strip(',')
    return hex_str

  def format_xbm(self,w,h,name,seq):
    xbm = '#define '+name+'_width '+str(w)+"\n"
    xbm += '#define '+name+'_height '+str(h)+"\n"
    xbm += 'static unsigned char '+name+"_bits[] = {\n"
    xbm += seq
    xbm += " };\n"
    return  xbm

  def save_xbm(self,path):
    w = self.width
    h = self.height
    name = os.path.basename(path)
    if name[-4:].lower() == '.xbm':
      name = name[:-4]
    seq = self.bool_array_to_xbm_data(self.bool_arr)
    data = self.format_xbm(w,h,name,seq)
    return write_file(path,data)

  def set_size(self):
    l = self.width * self. height
    self.size = l
    if self.bool_arr == None:
      self.bool_arr = []
    self.bool_arr = self.bool_arr[:l]
    while len(self.bool_arr) < l:
      self.bool_arr.append(False)

  def clear(self):
    self.bool_arr=[]
    self.set_size()


  def get_dim(self):
    return self.width,self.height

  def set_width(self,w):
    if w != self.width:
      pw = self.width
      bool_arr = []
      for i in range(self.height):
        if w < pw:
          j = i * pw
          bool_arr.extend(self.bool_arr[j:j+w])
        elif w > pw:
          j = i * pw
          d = w - pw
          bool_arr.extend(self.bool_arr[j:j+pw])
          for k in range(d):
            bool_arr.append(False)
      self.bool_arr = bool_arr
    self.width = w
    self.set_size()

  def set_height(self,h):
    self.height = h
    self.set_size()

  def __init__(self,*args):
    gtk.Frame.__init__(self,*args)
    self.set_shadow_type(gtk.SHADOW_NONE)
    #self.set_label_align(1,0.5)
    #self.set_label("xbm editor")

    self.bool_arr = None
    self.on = None
    self.off = None
    self.width = 1
    self.height = 1
    self.set_size()
    self.callback = None

    self.re_width = re.compile(r'^\s*#define\s+\S+_width\s+(\d+)\s*$',re.M)
    self.re_height = re.compile(r'^\s*#define\s+\S+_height\s+(\d+)\s*$',re.M)
    self.re_data = re.compile(r'_bits\[\]\s*=\s*\{\s*(.*?)\s*\};',re.S)
    self.re_split = re.compile(r'\s*,\s*',re.S)

    self.hex_map = {
      '0':'0000',
      '1':'0001',
      '2':'0010',
      '3':'0011',
      '4':'0100',
      '5':'0101',
      '6':'0110',
      '7':'0111',
      '8':'1000',
      '9':'1001',
      'a':'1010',
      'b':'1011',
      'c':'1100',
      'd':'1101',
      'e':'1110',
      'f':'1111',
    }



    self.area = gtk.DrawingArea()
    self.area.show()
    self.area.set_events(gtk.gdk.EXPOSURE_MASK | gtk.gdk.BUTTON_PRESS_MASK)
    self.area.connect("expose_event", self.draw_xbm)
    self.area.connect("button_press_event", self.button_press)
    self.area.connect("motion_notify_event", self.motion_notify)
    self.area.set_events(gtk.gdk.EXPOSURE_MASK
                            | gtk.gdk.BUTTON_PRESS_MASK
                            | gtk.gdk.LEAVE_NOTIFY_MASK
                            | gtk.gdk.POINTER_MOTION_MASK
                            | gtk.gdk.POINTER_MOTION_HINT_MASK)

    self.area.set_size_request(240, 240)

    self.add(self.area)
    self.show_all()

  def get_pixel_dim(self,*args):
    x,y,w,h = self.area.get_allocation()
    pw = int(w/self.width)
    ph = int(h/self.height)
    return pw,ph

  def is_within_area(self,px,py):
    x,y,w,h = self.area.get_allocation()
    return px > 0 and px < w and py > 0 and py < h

  def draw_xbm(self,*args):
    if not self.bool_arr:
      return False
    if not self.on:
      self.on = self.area.window.new_gc()
      self.on.set_rgb_fg_color(str_to_color('#000000'))
    if not self.off:
      self.off = self.area.window.new_gc()
      self.off.set_rgb_fg_color(str_to_color('#eeeeee'))
    pw,ph = self.get_pixel_dim()
    x,y,w,h = self.area.get_allocation()
    ew = pw * self.width
    eh = ph * self.height
    if ew < w:
      self.draw_swatch(ew,0,w,h,self.off)
    if eh < h:
      self.draw_swatch(0,eh,w,h,self.off)
    l = self.size
    for i in range(l):
      y,x = divmod(i,self.width)
      if self.bool_arr[i]:
        gc = self.on
      else:
        gc = self.off
      self.draw_swatch(pw*x,ph*y,pw,ph,gc)
    return True

  def draw_swatch(self, x, y, w, h, gc):
    self.area.window.draw_rectangle(gc, True, x, y, w, h)
    return

  def get_index(self,ex,ey):
    pw,ph = self.get_pixel_dim()
    i = int(ex/pw)
    j = int(ey/ph)
    if i == self.width:
      i -= 1
    return j * self.width + i

  def button_press(self,area,event):
    i = self.get_index(event.x,event.y)
    if i in range(self.size) and self.is_within_area(event.x,event.y):
      if event.button == 1:
        self.bool_arr[i] = True
      elif event.button == 3:
        self.bool_arr[i] = False
      self.draw_xbm()
      if self.callback:
        self.callback()
    return True

  def motion_notify(self,widget, event):
    if event.is_hint:
      x, y, state = event.window.get_pointer()
    else:
      x = event.x
      y = event.y
      state = event.state
    i = self.get_index(x,y)
    if i in range(self.size) and self.is_within_area(x,y):
      if state & gtk.gdk.BUTTON1_MASK:
        self.bool_arr[i] = True
      elif state & gtk.gdk.BUTTON3_MASK:
        self.bool_arr[i] = False
      self.draw_xbm()
      if self.callback:
        self.callback()
    return True



################################
########## XBM Window ##########
################################

class XBMWindow:
  def display_about(self,*args):
    dialog = gtk.AboutDialog()
    #dialog.set_title("About XBM Editor")
    dialog.set_icon_from_file("./xlogo32.pbm")
    dialog.set_logo(gtk.gdk.pixbuf_new_from_file('./xlogo32.pbm'))
    #dialog.set_logo(gtk.gdk.pixmap_new_from_file('/usr/include/X11/bitmaps/xlogo32'))
    dialog.set_program_name('XBM Editor')
    dialog.set_version('1.0')
    dialog.set_comments('X BitMap editor')
    dialog.set_copyright('(c) 2009 Xyne')
    dialog.set_website("http://xyne.archlinux.ca/projects/obtheme/")
    dialog.run()
    dialog.destroy()

  def display_settings(self, *args):
    self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.window.set_icon_from_file("./xlogo32.pbm")
    self.window.set_title("XBM Editor Settings")

    cm = gtk.Button(label='-')
    cm.connect('clicked', self.col_minus)
    cl = gtk.Label('cols')
    cp = gtk.Button(label='+')
    cp.connect('clicked', self.col_plus)
    rm = gtk.Button(label='-')
    rm.connect('clicked', self.row_minus)
    rl = gtk.Label('rows')
    rp = gtk.Button(label='+')
    rp.connect('clicked', self.row_plus)

    self.cl = cl
    self.rl = rl

    buttonbox = gtk.HBox(True, 0)
    buttonbox.pack_start(cl, True, True, 0)
    buttonbox.pack_start(cp, True, True, 0)
    buttonbox.pack_start(cm, True, True, 0)
    buttonbox.pack_start(rl, True, True, 0)
    buttonbox.pack_start(rp, True, True, 0)
    buttonbox.pack_start(rm, True, True, 0)
    buttonbox.show_all()

    box = gtk.VBox(False, 0)
    box.pack_start(buttonbox, False, False, 0)
    box.show_all()
    self.window.add(box)
    self.window.show_all()
    self.window.show()
    self.set_labels()

  def display_info(self, *args):
    dialog = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, "Left-click to set a pixel, right-click to unset it.")
    dialog.set_title("XBM Editor Info")
    dialog.set_icon_from_file("./xlogo32.pbm")
    dialog.run()
    dialog.destroy()

  def display_usage(self, *args):
    self.display_info()

  def display_help(self,*args):
    help_msg = '''Left-click to set a pixel, right-click to unset it.

Images will be saved along the themerc file.
'''


    textview = gtk.TextView()
    textview.get_buffer().set_text(help_msg)
    textview.set_editable(False)
    textview.set_wrap_mode(gtk.WRAP_WORD)
    textview.set_left_margin(5)
    textview.set_right_margin(5)

    textview_window = gtk.ScrolledWindow()
    textview_window.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
    textview_window.add(textview)

    dialog = gtk.Dialog(None,None,gtk.DIALOG_DESTROY_WITH_PARENT,('_Close',1))
    dialog.set_title("XBM Editor Info")
    dialog.set_default_size(300,250)
    dialog.vbox.pack_start(textview_window,True,True,5)
    dialog.vbox.show_all()
    response = dialog.run()
    dialog.destroy()


  def __init__(self):
    self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.window.set_icon_from_file("./xlogo32.pbm")
    self.window.set_title("XBM Editor")
    self.window.connect("destroy", self.destroy)
    self.window.set_position(gtk.WIN_POS_CENTER)
    self.file_name = None
    self.unsaved = False
    self.theme_dir = os.getenv('HOME')+'/.themes/obtheme/openbox-3'
    self.callback = None

    accel_group = gtk.AccelGroup()
    self.window.add_accel_group(accel_group)

    file_menu_open = gtk.ImageMenuItem('_Open...')
    file_menu_open.connect("activate", self.open_xbm,'open')
    file_menu_open.add_accelerator("activate",accel_group,ord('o'),gtk.gdk.CONTROL_MASK,gtk.ACCEL_VISIBLE)
    file_menu_open.set_image(gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_MENU))

    file_menu_save = gtk.ImageMenuItem('_Save')
    file_menu_save.connect("activate", self.save_xbm,'save')
    file_menu_save.add_accelerator("activate",accel_group,ord('s'),gtk.gdk.CONTROL_MASK,gtk.ACCEL_VISIBLE)
    file_menu_save.set_image(gtk.image_new_from_stock(gtk.STOCK_SAVE, gtk.ICON_SIZE_MENU))

    file_menu_save_as = gtk.ImageMenuItem('Save _As...')
    file_menu_save_as.connect("activate", self.save_xbm,'save as')
    file_menu_save_as.add_accelerator("activate",accel_group,ord('s'),(gtk.gdk.CONTROL_MASK|gtk.gdk.SHIFT_MASK),gtk.ACCEL_VISIBLE)
    file_menu_save_as.set_image(gtk.image_new_from_stock(gtk.STOCK_SAVE_AS, gtk.ICON_SIZE_MENU))

    file_menu_separator = gtk.SeparatorMenuItem()

    file_menu_quit = gtk.ImageMenuItem("_Quit")
    file_menu_quit.connect("activate", self.destroy)
    file_menu_quit.add_accelerator("activate",accel_group,ord('q'),gtk.gdk.CONTROL_MASK,gtk.ACCEL_VISIBLE)
    file_menu_quit.set_image(gtk.image_new_from_stock(gtk.STOCK_QUIT, gtk.ICON_SIZE_MENU))

    file_submenu = gtk.Menu()
    file_submenu.append(file_menu_open)
    file_submenu.append(file_menu_save)
    file_submenu.append(file_menu_save_as)
    file_submenu.append(file_menu_separator)
    file_submenu.append(file_menu_quit)
    file_submenu.show_all()

    file_menu = gtk.ImageMenuItem('_File')
    file_menu.set_submenu(file_submenu)
    file_menu.show()

    edit_menu_settings = gtk.ImageMenuItem('_Settings...')
    edit_menu_settings.connect("activate", self.display_settings)

    edit_submenu = gtk.Menu()
    edit_submenu.append(edit_menu_settings)
    edit_submenu.show_all()

    edit_menu = gtk.ImageMenuItem('_Edit')
    edit_menu.set_submenu(edit_submenu)
    edit_menu.show()

    usage_menu = gtk.ImageMenuItem("_Info")
    usage_menu.connect("activate", self.display_usage)
    usage_menu.set_image(gtk.image_new_from_stock(gtk.STOCK_INFO, gtk.ICON_SIZE_MENU))

    info_menu = gtk.ImageMenuItem('_Info')
    info_menu.connect("activate", self.display_about)
    info_menu.add_accelerator("activate",accel_group,ord('h'),gtk.gdk.CONTROL_MASK,gtk.ACCEL_VISIBLE)
    info_menu.set_image(gtk.image_new_from_stock(gtk.STOCK_INFO, gtk.ICON_SIZE_MENU))

    about_menu = gtk.ImageMenuItem('_About')
    about_menu.connect("activate", self.display_about)
    #about_menu.add_accelerator("activate",accel_group,ord('h'),gtk.gdk.CONTROL_MASK,gtk.ACCEL_VISIBLE)
    about_menu.set_image(gtk.image_new_from_stock(gtk.STOCK_ABOUT, gtk.ICON_SIZE_MENU))

    help_submenu = gtk.Menu()
    #help_submenu.append(info_menu)
    help_submenu.append(usage_menu)
    help_submenu.append(about_menu)
    help_submenu.show_all()

    help_menu = gtk.ImageMenuItem("_Help")
    help_menu.set_submenu(help_submenu)
    help_menu.show()



    menu_bar = gtk.MenuBar()
    menu_bar.append(file_menu)
    menu_bar.append(edit_menu)
    menu_bar.append(help_menu)

    open_button = gtk.ToolButton(stock_id=gtk.STOCK_OPEN)
    open_button.connect("clicked", self.open_xbm,'open')
    open_button.set_tooltip_text("Open File")

    save_button = gtk.ToolButton(stock_id=gtk.STOCK_SAVE)
    save_button.connect("clicked", self.save_xbm,'save')
    save_button.set_tooltip_text("Save File")

    save_as_button = gtk.ToolButton(stock_id=gtk.STOCK_SAVE_AS)
    save_as_button.connect("clicked", self.save_xbm, 'save as')
    save_as_button.set_tooltip_text("Save File As")

    settings_button = gtk.ToolButton(stock_id=gtk.STOCK_PREFERENCES)
    settings_button.connect("clicked", self.display_settings)
    settings_button.set_tooltip_text("Set Width and Height")

    info_button = gtk.ToolButton(stock_id=gtk.STOCK_INFO)
    #info_button.connect("clicked", self.display_help)
    info_button.connect("clicked", self.display_info)
    info_button.set_tooltip_text("Usage Info")

    quit_button = gtk.ToolButton(stock_id=gtk.STOCK_QUIT)
    quit_button.connect("clicked", self.destroy)
    quit_button.set_tooltip_text("Quit")

    cp = gtk.ToolButton(stock_id=gtk.STOCK_ADD)
    cp.connect('clicked', self.col_plus)
    cp.set_tooltip_text("Add Column")

    cm = gtk.ToolButton(stock_id=gtk.STOCK_REMOVE)
    cm.connect('clicked',self.col_minus)
    cm.set_tooltip_text("Remove Column")

    rp = gtk.ToolButton(stock_id=gtk.STOCK_ADD)
    rp.connect('clicked', self.row_plus)
    rp.set_tooltip_text("Add Row")

    rm = gtk.ToolButton(stock_id=gtk.STOCK_REMOVE)
    rm.connect('clicked', self.row_minus)
    rm.set_tooltip_text("Remove Row")

    toolbar = gtk.Toolbar()
    toolbar.insert(open_button, 0)
    toolbar.insert(save_button, 1)
    toolbar.insert(save_as_button, 2)
    #toolbar.insert(gtk.SeparatorToolItem(), 3)
    #toolbar.insert(cp, 4)
    #toolbar.insert(cm, 5)
    #toolbar.insert(gtk.SeparatorToolItem(), 6)
    #toolbar.insert(rp, 7)
    #toolbar.insert(rm, 8)
    #toolbar.insert(gtk.SeparatorToolItem(), 9)
    #toolbar.insert(settings_button, 4)
    #toolbar.insert(info_button, 4)
    #toolbar.insert(gtk.SeparatorToolItem(), 6)
    #toolbar.insert(quit_button, 7)

    editor = XBMEditor()
    editor.callback = self.save_preview

    cm = gtk.Button(label='-')
    cm.connect('clicked',self.col_minus)
    cl = gtk.Label('cols')
    cp = gtk.Button(label='+')
    cp.connect('clicked',self.col_plus)
    rm = gtk.Button(label='-')
    rm.connect('clicked',self.row_minus)
    rl = gtk.Label('rows')
    rp = gtk.Button(label='+')
    rp.connect('clicked',self.row_plus)

    self.cl = cl
    self.rl = rl

    buttonbox = gtk.HBox(True,0)
    buttonbox.pack_start(cm,True,True,0)
    buttonbox.pack_start(cl,True,True,0)
    buttonbox.pack_start(cp,True,True,0)
    buttonbox.pack_start(rm,True,True,0)
    buttonbox.pack_start(rl,True,True,0)
    buttonbox.pack_start(rp,True,True,0)
    buttonbox.show_all()

    combobox = gtk.combo_box_new_text()
    combobox.append_text('')
    combobox.set_active(0)
    imagebutton_list = imageButtons.keys()
    imagebutton_list.sort()
    for key in imagebutton_list:
      combobox.append_text(key)
    combobox.connect('changed', self.load_imagebutton)
    self.combobox = combobox

    default_button = gtk.Button('default')
    default_button.connect("clicked", self.remove_image)

    hbox = gtk.HBox(False,0)
    hbox.pack_start(combobox,True,True,0)
    hbox.pack_start(default_button,False,False,0)
    hbox.show_all()


    infopanel = gtk.ScrolledWindow()
    infopanel.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
    self.info = gtk.TextView()
    self.info.set_wrap_mode(gtk.WRAP_WORD)
    self.info.set_left_margin(5)
    self.info.set_right_margin(5)
    self.info.set_size_request(200,40)
    self.info.set_editable(False)
    infopanel.add(self.info)

    box = gtk.VBox(False,0)
    box.pack_start(menu_bar,False,False,0)
    box.pack_start(toolbar, False, False, 0)
    box.pack_start(editor,True,True,0)
    #box.pack_start(hbox,False,False,0)
    #box.pack_start(infopanel,False,False,0)
    #box.pack_start(buttonbox,False,False,0)
    box.show_all()
    self.window.add(box)
    self.window.show_all()
    self.window.show()
    self.editor = editor
    self.set_labels()

  def destroy(self, widget, data=None):
    #pass
    gtk.main_quit()

  def get_default(self,name):
    fpath = '/usr/share/doc/openbox/xbm/' + name + '.xbm'
    if os.path.exists(fpath):
      int_default = fpath
    else:
      int_default = None
    for default in imageButtons[name]['default']:
      if default != None:
        fpath = self.theme_dir + '/' + default + '.xbm'
        if os.path.exists(fpath):
          return fpath
        else:
          fpath = '/usr/share/doc/openbox/xbm/' + default + '.xbm'
          if os.path.exists(fpath) and int_default == None:
            int_default = fpath
    return int_default

  def load_imagebutton(self,combobox):
    name = combobox.get_active_text()
    if name == '':
      self.file_name = None
      self.info.get_buffer().set_text('')
      return
    self.info.get_buffer().set_text(imageButtons[name]['info'])
    fpath = self.theme_dir + '/' + name + '.xbm'
    if not os.path.exists(fpath):
      fpath = self.get_default(name)
    if fpath != None:
      if self.editor.load_xbm(fpath):
        self.set_labels()
        self.file_name = fpath
      else:
        sys.stderr.write("Error: unable to open %s\n" % fpath)
    else:
      sys.stderr.write("Error: no default could be found for %s.xbm\n" % name)

  def remove_image(self,*args):
    name = self.combobox.get_active_text()
    if name == '':
      self.editor.clear()
    else:
      fpath = self.theme_dir + '/' + name + '.xbm'
      if os.path.exists(fpath):
        os.remove(fpath)
        self.load_imagebutton(self.combobox)

  def save_preview(self):
    self.unsaved = False
    name = self.combobox.get_active_text()
    if name != '':
      fpath = self.theme_dir + '/' + name + '.xbm'
      self.editor.save_xbm(fpath)
    if self.callback:
      self.callback()

  def set_labels(self):
    w,h = self.editor.get_dim()
    self.cl.set_text("cols(%d)" % (w))
    self.rl.set_text("rows(%d)" % (h))
    self.editor.draw_xbm()

  def col_minus(self,widget):
    w = self.editor.width
    if w > 1:
      self.editor.set_width(w-1)
      self.set_labels()

  def col_plus(self,widget):
    w = self.editor.width
    self.editor.set_width(w+1)
    self.set_labels()

  def row_minus(self,widget):
    h = self.editor.height
    if h > 1:
      self.editor.set_height(h-1)
      self.set_labels()

  def row_plus(self,widget):
    h = self.editor.height
    self.editor.set_height(h+1)
    self.set_labels()

  def open_xbm(self,widget,arg=None,*args):
    filter_all = gtk.FileFilter()
    filter_all.set_name("All files")
    filter_all.add_pattern("*")

    filter_xpm = gtk.FileFilter()
    filter_xpm.set_name("XBM")
    filter_xpm.add_pattern("*.xbm")
    name = self.file_name
    dialog = gtk.FileChooserDialog('Select an XBM file',None,gtk.FILE_CHOOSER_ACTION_OPEN,
     (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    dialog.set_icon_from_file("./xlogo32.pbm")
    dialog.add_filter(filter_xpm)
    dialog.add_filter(filter_all)
    dialog.set_default_response(gtk.RESPONSE_OK)
    if name != None:
      dialog.set_current_folder(os.path.dirname(name))
    response = dialog.run()
    if response == gtk.RESPONSE_OK:
      name = dialog.get_filename()
    else:
      name = None
    dialog.destroy()
    if name != None:
      if self.editor.load_xbm(name):
        self.set_labels()
        self.file_name = name
        model = self.combobox.get_model()
        name = os.path.basename(name)
        self.combobox.set_active(0)
        for i in range(len(model)):
          if model[i][0] == name:
            self.combobox.set_active(i)
            break
      else:
        sys.stderr.write("Error: unable to open %s\n" % name)

  def save_xbm(self,widget=None,arg=None,*args):
    name = self.file_name
    if name == None or arg == 'save as':
      if arg == 'save as':
        button = gtk.STOCK_SAVE
      else:
        button = gtk.STOCK_SAVE
      dialog = gtk.FileChooserDialog('Select an XBM file',None,gtk.FILE_CHOOSER_ACTION_SAVE,
       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, button, gtk.RESPONSE_OK))
      dialog.set_icon_from_file("./xlogo32.pbm")
      filter_all = gtk.FileFilter()
      filter_all.set_name("All files")
      filter_all.add_pattern("*")

      filter_xpm = gtk.FileFilter()
      filter_xpm.set_name("XBM")
      filter_xpm.add_pattern("*.xbm")
      dialog.add_filter(filter_xpm)
      dialog.add_filter(filter_all)
      if name != None:
        dialog.set_current_folder(os.path.dirname(name))
        dialog.set_current_name(os.path.basename(name))
      dialog.set_default_response(gtk.RESPONSE_OK)
      response = dialog.run()
      if response == gtk.RESPONSE_OK:
        name = dialog.get_filename()
      dialog.destroy()
    if name != None:
      self.file_name = name
      if self.editor.save_xbm(name):
        self.unsaved = False
        self.file_name = name
      else:
        self.save_xbm(None,'save as')


  def main(self):
    gtk.main()














if __name__ == "__main__":
#  obt = ObTheme()
#  fusedir = obt.preview_themerc_dir
#  if not obt.preview_dir_is_mounted():
#    if os.fork() == 0:
#      fs = SimpleDir()
#      if not os.path.exists(fusedir):
#        os.makedirs(fusedir)
#      clear_dir(fusedir)
#      fs.main([sys.argv[0],fusedir])
#    else:
#      obt.main()
#  else:
#    obt.main()
  xbm = XBMWindow()
  xbm.main()
