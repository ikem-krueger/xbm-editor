#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import gtk
import os
import re
import sys

def str_to_color(string):
    return gtk.gdk.color_parse(string)

def read_file(path):
    f = open(path, 'r')
    contents = f.read()
    f.close()
    return contents

def write_file(path, contents):
    try:
        f = open(path, 'w')
    except IOError:
        return False
    else:
        f.write(contents)
        f.close()
        return True

class XBMEditor(gtk.Frame):
    def xbm_data_to_bool_array(self, data, width):
        bin_str = ''
        i = 0
        for byte in data:
            if byte[:2] == '0x':
                dec = int(byte[2:], 16)
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

    def open_xbm(self, path):
        data = read_file(path)
        m = self.re_width.search(data)
        if m:
            width = int(m.group(1))
        else:
            sys.stderr.write("Error: unable to detect XBM width in %s\n" % path)
            return None, None, None
        m = self.re_height.search(data)
        if m:
            height = int(m.group(1))
        else:
            sys.stderr.write("Error: unable to detect XBM height in %s\n" % path)
            return None, None, None
        m = self.re_data.search(data)
        if m:
            bool_arr = self.xbm_data_to_bool_array(self.re_split.split(m.group(1)), width)
        else:
            sys.stderr.write("Error: unable to detect XBM mask in %s\n" % path)
            return None, None, None
        return width, height, bool_arr

    def load_xbm(self, path):
        width, height, bool_arr = self.open_xbm(path)
        if width != None:
            self.width = width
            self.height = height
            self.bool_arr = bool_arr
            self.set_size()
            self.draw_xbm()
            return True
        else:
            return False

    def bool_array_to_xbm_data(self, bool_arr):
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
                hex_str += "0x%02x" % int(bin_str[::-1], 2)
                bin_str = ''
        hex_str.strip()
        hex_str.strip(', ')
        return hex_str

    def format_xbm(self, w, h, name, seq):
        xbm = '#define '+name+'_width '+str(w)+"\n"
        xbm += '#define '+name+'_height '+str(h)+"\n"
        xbm += 'static unsigned char '+name+"_bits[] = {\n"
        xbm += seq
        xbm += " };\n"
        return    xbm

    def save_xbm(self, path):
        w = self.width
        h = self.height
        name = os.path.basename(path)
        if name[-4:].lower() == '.xbm':
            name = name[:-4]
        seq = self.bool_array_to_xbm_data(self.bool_arr)
        data = self.format_xbm(w, h, name, seq)
        return write_file(path, data)

    def set_size(self):
        l = self.width * self. height
        self.size = l
        if self.bool_arr == None:
            self.bool_arr = []
        self.bool_arr = self.bool_arr[:l]
        while len(self.bool_arr) < l:
            self.bool_arr.append(False)

    def clear(self):
        self.bool_arr = []
        self.set_size()

    def get_dim(self):
        return self.width, self.height

    def set_width(self, w):
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

    def set_height(self, h):
        self.height = h
        self.set_size()

    def __init__(self, *args):
        # TODO: What does it do? Why is it needed?
        gtk.Container.__init__(self, *args)

        self.bool_arr = None
        self.on = None
        self.off = None
        self.width = 1
        self.height = 1
        self.set_size()
        self.callback = None

        self.re_width = re.compile(r'^\s*#define\s+\S+_width\s+(\d+)\s*$', re.M)
        self.re_height = re.compile(r'^\s*#define\s+\S+_height\s+(\d+)\s*$', re.M)
        self.re_data = re.compile(r'_bits\[\]\s*=\s*\{\s*(.*?)\s*\};', re.S)
        self.re_split = re.compile(r'\s*, \s*', re.S)

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
        
        self.area = builder.get_object("drawingarea1")
        self.area.show()
        self.area.connect("expose_event", self.draw_xbm)
        self.area.connect("button_press_event", self.button_press)
        self.area.connect("motion_notify_event", self.motion_notify)
        '''
        self.area.set_events(gtk.gdk.EXPOSURE_MASK
                                                        | gtk.gdk.BUTTON_PRESS_MASK
                                                        | gtk.gdk.LEAVE_NOTIFY_MASK
                                                        | gtk.gdk.POINTER_MOTION_MASK
                                                        | gtk.gdk.POINTER_MOTION_HINT_MASK)
        '''
        self.area.set_size_request(240, 240)

        self.show_all()

    def get_pixel_dim(self, *args):
        x, y, w, h = self.area.get_allocation()
        pw = int(w/self.width)
        ph = int(h/self.height)
        return pw, ph

    def is_within_area(self, px, py):
        x, y, w, h = self.area.get_allocation()
        return px > 0 and px < w and py > 0 and py < h

    def draw_xbm(self, *args):
        if not self.bool_arr:
            return False
        if not self.on:
            self.on = self.area.window.new_gc()
            self.on.set_rgb_fg_color(str_to_color('#000000'))
        if not self.off:
            self.off = self.area.window.new_gc()
            self.off.set_rgb_fg_color(str_to_color('#eeeeee'))
        pw, ph = self.get_pixel_dim()
        x, y, w, h = self.area.get_allocation()
        ew = pw * self.width
        eh = ph * self.height
        if ew < w:
            self.draw_swatch(ew, 0, w, h, self.off)
        if eh < h:
            self.draw_swatch(0, eh, w, h, self.off)
        l = self.size
        for i in range(l):
            y, x = divmod(i, self.width)
            if self.bool_arr[i]:
                gc = self.on
            else:
                gc = self.off
            self.draw_swatch(pw*x, ph*y, pw, ph, gc)
        return True

    def draw_swatch(self, x, y, w, h, gc):
        self.area.window.draw_rectangle(gc, True, x, y, w, h)
        return

    def get_index(self, ex, ey):
        pw, ph = self.get_pixel_dim()
        i = int(ex/pw)
        j = int(ey/ph)
        if i == self.width:
            i -= 1
        return j * self.width + i

    def button_press(self, area, event):
        i = self.get_index(event.x, event.y)
        if i in range(self.size) and self.is_within_area(event.x, event.y):
            if event.button == 1:
                self.bool_arr[i] = True
            elif event.button == 3:
                self.bool_arr[i] = False
            self.draw_xbm()
            if self.callback:
                self.callback()
        return True

    def motion_notify(self, widget, event):
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state
        i = self.get_index(x, y)
        if i in range(self.size) and self.is_within_area(x, y):
            if state & gtk.gdk.BUTTON1_MASK:
                self.bool_arr[i] = True
            elif state & gtk.gdk.BUTTON3_MASK:
                self.bool_arr[i] = False
            self.draw_xbm()
            if self.callback:
                self.callback()
        return True

class XBMWindow:
    def __init__(self):
        global builder
        
        builder = gtk.Builder()
        builder.add_from_file("xbm-editor.glade")
        
        self.dialog = builder.get_object("aboutdialog1")

        self.window = builder.get_object("window1")
        self.window.connect("destroy", self.destroy)
        self.window.show_all()

        self.file_name = None
        self.unsaved = False
        self.theme_dir = os.getenv('HOME')+'/.themes/obtheme/openbox-3'
        self.callback = None

        accel_group = gtk.AccelGroup()
        self.window.add_accel_group(accel_group)

        self.file_menu_new = builder.get_object("imagemenuitem1")
        self.file_menu_new.connect("activate", self.new_xbm)

        self.file_menu_open = builder.get_object("imagemenuitem2")
        self.file_menu_open.connect("activate", self.open_xbm,'open')

        self.file_menu_save = builder.get_object("imagemenuitem3")
        self.file_menu_save.connect("activate", self.save_xbm,'save')

        self.file_menu_save_as = builder.get_object("imagemenuitem4")
        self.file_menu_save_as.connect("activate", self.save_xbm,'save as')

        self.file_menu_quit = builder.get_object("imagemenuitem5")
        self.file_menu_quit.connect("activate", self.destroy)
     
        self.about_menu = builder.get_object("imagemenuitem10")
        self.about_menu.connect("activate", self.display_about)
     
        self.new_button = builder.get_object("toolbutton1")
        self.new_button.connect("clicked", self.new_xbm)

        self.open_button = builder.get_object("toolbutton2")
        self.open_button.connect("clicked", self.open_xbm,'open')

        self.save_button = builder.get_object("toolbutton4")
        self.save_button.connect("clicked", self.save_xbm,'save')

        self.save_as_button = builder.get_object("toolbutton5")
        self.save_as_button.connect("clicked", self.save_xbm, 'save as')

        self.editor = XBMEditor()
        #self.editor.load_xbm("new.xbm")

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def new_xbm(self, *args):
        self.load_xbm("new.xbm")

    def open_xbm(self, widget, arg=None, *args):
        filter_all = gtk.FileFilter()
        filter_all.set_name("All files")
        filter_all.add_pattern("*")

        filter_xpm = gtk.FileFilter()
        filter_xpm.set_name("XBM")
        filter_xpm.add_pattern("*.xbm")
        name = self.file_name
        dialog = gtk.FileChooserDialog('Select an XBM file', None, gtk.FILE_CHOOSER_ACTION_OPEN,
         (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.add_filter(filter_xpm)
        dialog.add_filter(filter_all)
        dialog.set_default_response(gtk.RESPONSE_OK)
        if name != None:
            dialog.set_current_folder(os.path.dirname(name))

        if dialog.run() == gtk.RESPONSE_OK:
            name = dialog.get_filename()
        else:
            name = None
        dialog.destroy()
        if name != None:
            self.editor.load_xbm(name)
        else:
            sys.stderr.write("Error: unable to open %s\n" % name)

    def load_xbm(self, name):
        self.editor.load_xbm(name)

    def save_xbm(self, widget=None, arg=None, *args):
        name = self.file_name
        if name == None or arg == 'save as':
            if arg == 'save as':
                button = gtk.STOCK_SAVE_AS
            else:
                button = gtk.STOCK_SAVE
            dialog = gtk.FileChooserDialog('Select an XBM file', None, gtk.FILE_CHOOSER_ACTION_SAVE,
             (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, button, gtk.RESPONSE_OK))
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

            if dialog.run() == gtk.RESPONSE_OK:
                name = dialog.get_filename()
            dialog.destroy()
        if name != None:
            self.file_name = name
            if self.editor.save_xbm(name):
                self.unsaved = False
                self.file_name = name
            else:
                self.save_xbm(None, 'save as')

    def display_about(self,*args):
        self.dialog.run()
        self.dialog.hide()

    def main(self):
        gtk.main()

if __name__ == "__main__":
    xbm = XBMWindow()
    xbm.main()
