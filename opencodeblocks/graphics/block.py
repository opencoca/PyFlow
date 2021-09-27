# OpenCodeBlock an open-source tool for modular visual programing in python
# Copyright (C) 2021 Mathïs FEDERICO <https://www.gnu.org/licenses/>

""" Module for the OCB Block visualization """

from typing import Optional, List, Tuple

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QPen, QColor, QFont, QPainter, QPainterPath
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsSceneMouseEvent, QGraphicsTextItem, \
    QStyleOptionGraphicsItem, QWidget, QApplication

from opencodeblocks.core.node import Node
from opencodeblocks.graphics.socket import OCBSocket

class OCBBlock(QGraphicsItem):
    def __init__(self, node:Node,
            title_color:str='white', title_font:str="Ubuntu", title_size:int=10, title_padding=4.0,
            parent: Optional['QGraphicsItem']=None) -> None:
        super().__init__(parent=parent)
        self.node = node
        self.sockets_in = []
        self.sockets_out = []

        self.width = 180
        self._min_width = 100
        self.height = 240
        self._min_height = 100
        self.edge_size = 10.0

        self.title_graphics = self.init_title_graphics(
            title_color, title_font, title_size, title_padding)
        self.title = self.node.title
        self.title_height = 3 * title_size

        self._pen_outline = QPen(QColor("#7F000000"))
        self._pen_outline_selected = QPen(QColor("#FFFFA637"))

        self._brush_title = QBrush(QColor("#FF313131"))
        self._brush_background = QBrush(QColor("#E3212121"))

        self.init_ui()

        self.resizing = False

    def init_ui(self):
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

    def get_socket_pos(self, socket:OCBSocket) -> Tuple[float]:
        x = 0 if socket.socket_type == 'input' else self.width
        y_offset = self.title_height + 2 * socket.radius

        n_sockets = self.get_n_sockets(socket.socket_type)
        if n_sockets < 2:
            y = y_offset
        else:
            side_lenght = self.height - y_offset - 2 * socket.radius - self.edge_size
            y = y_offset + side_lenght * socket.index / (n_sockets - 1)
        return x, y

    def get_n_sockets(self, socket_type='input'):
        return len(self.sockets_in) if socket_type == 'input' else len(self.sockets_out)

    def update_sockets(self, socket_type='input'):
        if socket_type == 'input':
            for socket in self.sockets_in:
                socket.setPos(*self.get_socket_pos(socket))
        else:
            for socket in self.sockets_out:
                socket.setPos(*self.get_socket_pos(socket))

    def add_socket(self, socket_type='input', *args, **kwargs):
        n_sockets = self.get_n_sockets(socket_type)
        socket = OCBSocket(block=self, socket_type=socket_type, index=n_sockets, *args, **kwargs)
        if socket_type == 'input':
            self.sockets_in.append(socket)
            self.update_sockets(socket_type='input')
        else:
            self.sockets_out.append(socket)
            self.update_sockets(socket_type='output')

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.width, self.height).normalized()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem,
            widget: Optional[QWidget]=None) -> None:
        # title
        path_title = QPainterPath()
        path_title.setFillRule(Qt.FillRule.WindingFill)
        path_title.addRoundedRect(0, 0, self.width, self.title_height,
            self.edge_size, self.edge_size)
        path_title.addRect(0, self.title_height - self.edge_size,
            self.edge_size, self.edge_size)
        path_title.addRect(self.width - self.edge_size, self.title_height - self.edge_size,
            self.edge_size, self.edge_size)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._brush_title)
        painter.drawPath(path_title.simplified())

        # content
        path_title = QPainterPath()
        path_title.setFillRule(Qt.FillRule.WindingFill)
        path_title.addRoundedRect(0, self.title_height, self.width, self.height - self.title_height,
            self.edge_size, self.edge_size)
        path_title.addRect(0, self.title_height, self.edge_size, self.edge_size)
        path_title.addRect(self.width - self.edge_size, self.title_height,
            self.edge_size, self.edge_size)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._brush_background)
        painter.drawPath(path_title.simplified())

        # outline
        path_outline = QPainterPath()
        path_outline.addRoundedRect(0, 0, self.width, self.height,
            self.edge_size, self.edge_size)
        painter.setPen(self._pen_outline_selected if self.isSelected() else self._pen_outline)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path_outline.simplified())

    def _is_in_resize_area(self, pos:QPointF):
        return self.width - pos.x() < 2 * self.edge_size \
            and self.height - pos.y() < 2 * self.edge_size

    def mousePressEvent(self, event:QGraphicsSceneMouseEvent):
        pos = event.pos()
        if self._is_in_resize_area(pos):
            self.resize_start = pos
            self.resizing = True
            QApplication.setOverrideCursor(Qt.CursorShape.SizeFDiagCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event:QGraphicsSceneMouseEvent):
        self.resizing = False
        QApplication.restoreOverrideCursor()
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event:QGraphicsSceneMouseEvent):
        if self.resizing:
            delta = event.pos() - self.resize_start
            self.width = max(self.width + delta.x(), self._min_width)
            self.height = max(self.height + delta.y(), self._min_height)
            self.resize_start = event.pos()
            self.update()
        else:
            super().mouseMoveEvent(event)

    def init_title_graphics(self, color:str, font:str, size:int,
            padding:float) -> QGraphicsTextItem:
        title = QGraphicsTextItem(self)
        title.setDefaultTextColor(QColor(color))
        title.setFont(QFont(font, size))
        title.setPos(padding, 0)
        title.setTextWidth(self.width - 2 * self.edge_size)
        return title

    @property
    def title(self):
        return self._title
    @title.setter
    def title(self, value:str):
        self._title = value
        self.title_graphics.setPlainText(self._title)

    @property
    def width(self):
        return self._width
    @width.setter
    def width(self, value:float):
        self._width = value
        if hasattr(self, 'title_graphics'):
            self.title_graphics.setTextWidth(self.width - 2 * self.edge_size)
        self.update_sockets('input')
        self.update_sockets('output')
