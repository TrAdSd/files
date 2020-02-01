#!/usr/bin/python
# -*- coding: utf-8 -*-


try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

from libs.utils import distance
import sys

import os
import re
from difflib import SequenceMatcher
import struct
import imghdr
from PyQt5.QtWidgets import QApplication


app_a = QApplication(sys.argv)
screen_a = app_a.screens()[0]
screen_dpi = screen_a.physicalDotsPerInch()
size_a = screen_a.size()
screen_width = size_a.width()
screen_height = size_a.height()
app_a.quit()



DEFAULT_LINE_COLOR = QColor(0, 255, 0, 128)
DEFAULT_FILL_COLOR = QColor(255, 0, 0, 128)
DEFAULT_SELECT_LINE_COLOR = QColor(255, 255, 255)
DEFAULT_SELECT_FILL_COLOR = QColor(0, 128, 255, 155)
DEFAULT_VERTEX_FILL_COLOR = QColor(0, 255, 0, 255)
DEFAULT_HVERTEX_FILL_COLOR = QColor(255, 0, 0)
MIN_Y_LABEL = 10


dir = os.path.dirname(__file__)
filename_for_settings_log_global = os.path.join(dir, 'settings_log.txt')


def read_line(filepath):
    with open(filepath, 'rt', encoding='utf-8-sig', newline='') as file:
        lines = file.read()
    return lines.splitlines()



def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def max_similarity_in_list(input_list):
    inp_list=list(input_list)
    maxx=0
    while len(inp_list)>1:
        item=inp_list[0]
        inp_list.pop(0)
        for item_from_loop in inp_list:
            sim=similar(item,item_from_loop)
            if sim>maxx:
                max_similarity_item_one=item
                max_similarity_item_two=item_from_loop
                maxx=sim
    return (maxx, max_similarity_item_one, max_similarity_item_two)

def remove_non_initial_vowels(string):
    if len(string)>3:
        v_less_str=re.sub('(?<!^)[aeiouwy]', '', string, flags=re.I)
        return string if len(v_less_str)<3 else v_less_str
    return string



dir = os.path.dirname(os.path.dirname(__file__))
dir = os.path.join(dir, 'data')
filename_predefined_classes = os.path.join(dir, 'predefined_classes.txt')


with open(filename_predefined_classes) as res_file:
    fullfile = res_file.read().strip()

class_list = fullfile.splitlines()
class_list_after_vowel_removed = list(map(remove_non_initial_vowels, class_list))
max_list_similarity_after_vowel_removed = max_similarity_in_list(class_list_after_vowel_removed)[0]



class Shape(object):
    P_SQUARE, P_ROUND = range(2)

    MOVE_VERTEX, NEAR_VERTEX = range(2)

    # The following class variables influence the drawing
    # of _all_ shape objects.
    line_color = DEFAULT_LINE_COLOR
    fill_color = DEFAULT_FILL_COLOR
    select_line_color = DEFAULT_SELECT_LINE_COLOR
    select_fill_color = DEFAULT_SELECT_FILL_COLOR
    vertex_fill_color = DEFAULT_VERTEX_FILL_COLOR
    hvertex_fill_color = DEFAULT_HVERTEX_FILL_COLOR
    point_type = P_ROUND
    point_size = 8
    scale = 1.0

    def __init__(self, label=None, line_color=None, difficult=False, paintLabel=False):
        self.label = label
        self.points = []
        self.fill = False
        self.selected = False
        self.difficult = difficult
        self.paintLabel = paintLabel

        self._highlightIndex = None
        self._highlightMode = self.NEAR_VERTEX
        self._highlightSettings = {
            self.NEAR_VERTEX: (4, self.P_ROUND),
            self.MOVE_VERTEX: (1.5, self.P_SQUARE),
        }

        self._closed = False

        if line_color is not None:
            # Override the class line_color attribute
            # with an object attribute. Currently this
            # is used for drawing the pending line a different color.
            self.line_color = line_color

    def close(self):
        self._closed = True

    def reachMaxPoints(self):
        if len(self.points) >= 4:
            return True
        return False

    def addPoint(self, point):
        if not self.reachMaxPoints():
            self.points.append(point)

    def popPoint(self):
        if self.points:
            return self.points.pop()
        return None

    def isClosed(self):
        return self._closed

    def setOpen(self):
        self._closed = False

    def paint(self, painter):
        global screen_width
        global screen_height
        global screen_dpi
        global filename_for_settings_log_global
        if self.points:
            color = self.select_line_color if self.selected else self.line_color
            pen = QPen(color)
            
            # Size multiplier
            settings_log_info = read_line(filename_for_settings_log_global)
      
            zoom_adjuster_constant = (100*screen_width)/1920 if screen_width>screen_height else (100*screen_height)/1080
            screen_dpi_adjuster = 71.98897850121344/screen_dpi
            zoom_adjust = float(settings_log_info[0])

            SIZE_MULTIPLIER_TWO = float(settings_log_info[1])
            SIZE_MULTIPLIER = ((zoom_adjuster_constant*SIZE_MULTIPLIER_TWO)/zoom_adjust)*screen_dpi_adjuster

            # Try using integer sizes for smoother drawing(?)
            pen.setWidth(max(3*SIZE_MULTIPLIER, int(round(2.0 / self.scale))))
            pen.setColor(QColor(0,0,255,128))
            painter.setPen(pen)

            line_path = QPainterPath()
            vrtx_path = QPainterPath()

            line_path.moveTo(self.points[0])
            # Uncommenting the following line will draw 2 paths
            # for the 1st vertex, and make it non-filled, which
            # may be desirable.
            #self.drawVertex(vrtx_path, 0)

            for i, p in enumerate(self.points):
                line_path.lineTo(p)
                self.drawVertex(vrtx_path, i)
            if self.isClosed():
                line_path.lineTo(self.points[0])

            painter.drawPath(line_path)
            painter.drawPath(vrtx_path)
            painter.fillPath(vrtx_path, self.vertex_fill_color)

            # Draw text at the top-left
            if self.paintLabel:
                min_x = sys.maxsize
                min_y = sys.maxsize
                for point in self.points:
                    min_x = min(min_x, point.x())
                    min_y = min(min_y, point.y())
                if min_x != sys.maxsize and min_y != sys.maxsize:
                    font = QFont()
                    font.setFamily("Consolas")
                    font.setPointSize(20*SIZE_MULTIPLIER)
                    font.setBold(True)
                    painter.setFont(font)
                    pen.setColor(QColor(0,0,0,255))
                    painter.setPen(pen)
                    selected_class = str(self.label)
                    if selected_class in class_list:
                        if max_list_similarity_after_vowel_removed > 0.8:
                            label_to_show_on_screen = selected_class
                        else:
                            label_to_show_on_screen = remove_non_initial_vowels(selected_class)
                    else:
                        font.setPointSize(100*SIZE_MULTIPLIER)
                        painter.setFont(font)
                        label_to_show_on_screen = "[" + selected_class + "]"

                    if(self.label == None):
                        self.label = ""
                    if(min_y < MIN_Y_LABEL):
                        min_y += MIN_Y_LABEL                    

                    painter.drawText(min_x, min_y, label_to_show_on_screen)

                    font.setBold(False)
                    painter.setFont(font)
                    pen.setColor(QColor(255,0,0,255))
                    painter.setPen(pen)
                    painter.drawText(min_x, min_y, label_to_show_on_screen)



            if self.fill:
                color = self.select_fill_color if self.selected else self.fill_color
                painter.fillPath(line_path, color)

    def drawVertex(self, path, i):
        d = self.point_size / self.scale
        shape = self.point_type
        point = self.points[i]
        if i == self._highlightIndex:
            size, shape = self._highlightSettings[self._highlightMode]
            d *= size
        if self._highlightIndex is not None:
            self.vertex_fill_color = self.hvertex_fill_color
        else:
            self.vertex_fill_color = Shape.vertex_fill_color
        if shape == self.P_SQUARE:
            path.addRect(point.x() - d / 2, point.y() - d / 2, d, d)
        elif shape == self.P_ROUND:
            path.addEllipse(point, d / 2.0, d / 2.0)
        else:
            assert False, "unsupported vertex shape"

    def nearestVertex(self, point, epsilon):
        for i, p in enumerate(self.points):
            if distance(p - point) <= epsilon:
                return i
        return None

    def containsPoint(self, point):
        return self.makePath().contains(point)

    def makePath(self):
        path = QPainterPath(self.points[0])
        for p in self.points[1:]:
            path.lineTo(p)
        return path

    def boundingRect(self):
        return self.makePath().boundingRect()

    def moveBy(self, offset):
        self.points = [p + offset for p in self.points]

    def moveVertexBy(self, i, offset):
        self.points[i] = self.points[i] + offset

    def highlightVertex(self, i, action):
        self._highlightIndex = i
        self._highlightMode = action

    def highlightClear(self):
        self._highlightIndex = None

    def copy(self):
        shape = Shape("%s" % self.label)
        shape.points = [p for p in self.points]
        shape.fill = self.fill
        shape.selected = self.selected
        shape._closed = self._closed
        if self.line_color != Shape.line_color:
            shape.line_color = self.line_color
        if self.fill_color != Shape.fill_color:
            shape.fill_color = self.fill_color
        shape.difficult = self.difficult
        return shape

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value
