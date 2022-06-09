import random
import copy

import numpy as np
from PyQt5.QtCore import Qt, QBasicTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QMainWindow, QFrame, QDesktopWidget, QApplication
from PyQt5.QtTest import QTest


class Tetris(QMainWindow):

    def __init__(self):
        super().__init__()

        self.tboard = Board(self)
        self.setCentralWidget(self.tboard)

        self.statusbar = self.statusBar()
        self.tboard.msg2Statusbar[str].connect(self.statusbar.showMessage)

        self.tboard.reset()

        self.resize(380, 760)
        self.center()
        self.setWindowTitle('Neural Tetris')
        self.show()

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2,
                  (screen.height() - size.height()) // 2)


class Board(QFrame):
    msg2Statusbar = pyqtSignal(str)
    BoardWidth = 10
    BoardHeight = 20
    Speed = 50
    board = None

    def __init__(self, parent):
        super().__init__(parent)

        self.timer = QBasicTimer()
        self.reset()
        self.setFocusPolicy(Qt.StrongFocus)

    def square_width(self):
        return self.contentsRect().width() // Board.BoardWidth

    def square_height(self):
        return self.contentsRect().height() // Board.BoardHeight

    def draw_square(self, painter, x, y, shape):
        color_table = [0x000000, 0xCC6666, 0x66CC66, 0x6666CC,
                       0xCCCC66, 0xCC66CC, 0x66CCCC, 0xDAAA00]

        color = QColor(color_table[Shape.shapes[shape].color])
        painter.fillRect(x + 1, y + 1, self.square_width() - 2,
                         self.square_height() - 2, color)

        painter.setPen(color.lighter())
        painter.drawLine(x, y + self.square_height() - 1, x, y)
        painter.drawLine(x, y, x + self.square_width() - 1, y)

        painter.setPen(color.darker())
        painter.drawLine(x + 1, y + self.square_height() - 1,
                         x + self.square_width() - 1, y + self.square_height() - 1)
        painter.drawLine(x + self.square_width() - 1,
                         y + self.square_height() - 1, x + self.square_width() - 1, y + 1)

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.contentsRect()

        board_top = rect.bottom() - Board.BoardHeight * self.square_height()

        for i in range(Board.BoardHeight):
            for j in range(Board.BoardWidth):
                shape = self.board[Board.BoardHeight-i-1][j]

                if shape != 'NoShape':
                    self.draw_square(painter,
                                     rect.left() + j * self.square_width(),
                                     board_top + i * self.square_height(), shape)

        if self.cur_piece.piece_shape != 'NoShape':
            for _ in self.cur_piece.coords:
                x, y = self.curX + _[0], self.curY - _[1]
                self.draw_square(painter, rect.left() + x * self.square_width(),
                                 board_top + (Board.BoardHeight-y-1) * self.square_height(),
                                 self.cur_piece.piece_shape)

    def reset(self):
        """
        Reset the board
        """
        self.clear_board()
        self.rows_to_remove = None
        self.cur_piece = None
        self.curX = 0
        self.curY = 0
        self.game_over = False
        self.score = 0

        self.make_new_piece()
        self.timer.start(Board.Speed, self)

    def clear_board(self):
        """
        Clears the board
        """
        self.board = [['NoShape']*self.BoardWidth for _ in range(self.BoardHeight)]

    def piece_dropped(self):
        """
        When piece is at bottom border clears full lines and makes new piece on the board
        """
        for _ in self.cur_piece.coords:
            x, y = self.curX + _[0], self.curY - _[1]
            self.board[y][x] = self.cur_piece.piece_shape

        if self.check_lines():
            self.remove_full_lines()

        self.make_new_piece()

    def make_new_piece(self):
        """
        Produces new piece on board
        """
        self.cur_piece = Shape()
        self.cur_piece.set_random_shape()
        self.curX = random.randint(2, Board.BoardWidth - 2)
        self.curY = Board.BoardHeight - 1 + np.min(self.cur_piece.coords[:, 1])

        if self.check_collision(self.cur_piece, self.curX, self.curY):
            self.cur_piece.set_shape('NoShape')
            self.timer.stop()

    def check_lines(self):
        """
        Checks board lines for being filled
        """
        self.rows_to_remove = []
        for i in range(self.BoardHeight):
            if self.board[i].count('NoShape') == 0:
                self.rows_to_remove.append(i)

        return len(self.rows_to_remove)

    def remove_full_lines(self):
        """
        Removes filled lines when shape reaches bottom border of board
        """
        self.rows_to_remove.reverse()

        for m in self.rows_to_remove:
            for k in range(m, Board.BoardHeight - 1):
                for _ in range(Board.BoardWidth):
                    self.board[k][_] = self.board[k+1][_]

        self.score += len(self.rows_to_remove)
        self.cur_piece.set_shape('NoShape')
        self.update()

    def move_shape(self, new_piece, new_x, new_y):
        """
        Moves shape to new position
        :param new_piece: Tetrominoe
        :param new_x: int
        :param new_y: int
        """
        self.cur_piece = new_piece
        self.curX = new_x
        self.curY = new_y
        self.update()

    def check_point(self, x, y):
        """
        Checks whether point touches border or not
        :param x: int
        :param y: int
        :return: collision: bool
        """
        cond = [x < 0, x >= Board.BoardWidth, y < 0, y >= Board.BoardHeight]
        try:
            cond.append(self.board[y][x] != 'NoShape')
        except IndexError:
            cond.append(True)

        return any(cond)

    def check_collision(self, piece, new_x, new_y):
        """
        Checks whether shape touches border or not
        :param piece: Tetrominoe
        :param new_x: int
        :param new_y: int
        :return: collision: bool
        """
        collision = False
        for _ in piece.coords:
            x, y = new_x + _[0], new_y - _[1]

            if self.check_point(x, y):
                collision = True
                break

        return collision

    def step(self, action):
        """
        Do step
        :param action
        :return: score, game_over
        """

        x, num_rotations = action

        self.move_shape(self.cur_piece, x, self.curY)

        for _ in range(num_rotations):
            self.move_shape(self.cur_piece.rotate_right(), self.curX, self.curY)

        while not self.check_collision(self.cur_piece, self.curX, self.curY - 1):
            self.move_shape(self.cur_piece, self.curX, self.curY - 1)
            QTest.qWait(self.Speed)

        self.piece_dropped()

        if self.game_over:
            self.score -= 2

        return self.score, self.game_over

    def get_params(self):
        """
        Get params of board
        """
        board = copy.copy(self.board)
        board_width = copy.copy(self.BoardWidth)
        board_height = copy.copy(self.BoardHeight)
        cur_piece = copy.copy(self.cur_piece)

        return board, board_width, board_height, cur_piece


class Tetrominoe:
    """
    Class for assigning a shape
    """
    def __init__(self, color, coords, num_rotations):
        self.color = color
        self.coords = coords
        self.num_rotations = num_rotations


class Shape:
    """
    Class for manipulating with shape
    """
    shapes = {'NoShape': Tetrominoe(0, ((0, -1), (0, 0), (-1, 0), (-1, 1)), 0),
              'ZShape': Tetrominoe(1, ((0, -1), (0, 0), (-1, 0), (-1, 1)), 2),
              'SShape': Tetrominoe(2, ((0, -1), (0, 0), (1, 0), (1, 1)), 2),
              'LineShape': Tetrominoe(3, ((-1, 0), (0, 0), (1, 0), (2, 0)), 2),
              'TShape': Tetrominoe(4, ((-1, 0), (0, 0), (1, 0), (0, 1)), 4),
              'SquareShape': Tetrominoe(5, ((0, 0), (1, 0), (0, 1), (1, 1)), 1),
              'LShape': Tetrominoe(6, ((-1, -1), (0, -1), (0, 0), (0, 1)), 4),
              'MirroredLShape': Tetrominoe(7, ((1, -1), (0, -1), (0, 0), (0, 1)), 4)}

    def __init__(self):
        self.num_rotations = None
        self.piece_shape = None
        self.coords = np.array(self.shapes['NoShape'].coords)
        self.set_shape('NoShape')

    def set_shape(self, shape):
        """
        Sets the shape attributes
        :param shape: Tetrominoe
        """
        self.coords = np.array(self.shapes[shape].coords)
        self.piece_shape = shape
        self.num_rotations = self.shapes[shape].num_rotations

    def set_random_shape(self):
        """
        Produces new shape
        :return: random shape
        """
        values = list(self.shapes.keys())
        values.remove('NoShape')
        self.set_shape(random.choice(values))

    def rotate_right(self):
        """
        Rotates the shape at 90 degrees to right
        """
        result = Shape()
        result.piece_shape = self.piece_shape

        if result.piece_shape != 'SquareShape':
            result.coords = [[-i[1], i[0]] for i in self.coords]

        return result
