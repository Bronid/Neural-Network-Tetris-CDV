

    def __init__(self, parent):
        super().__init__(parent)

        self.clear_board()
        self.rows_to_remove = None
        self.cur_piece = None
        self.timer = QBasicTimer()
        self.isWaitingAfterLine = False

        self.curX = 0
        self.curY = 0
        self.score = 0
        self.game_over = False

        self.setFocusPolicy(Qt.StrongFocus)
        self.isStarted = False
        self.isPaused = False

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

        if self.cur_piece.pieceShape != 'NoShape':
            for _ in self.cur_piece.coords:
                x, y = self.curX + _[0], self.curY - _[1]
                self.draw_square(painter, rect.left() + x * self.square_width(),
                                 board_top + (Board.BoardHeight-y-1) * self.square_height(),
                                 self.cur_piece.pieceShape)

    def keyPressEvent(self, event):
        """
        Handles key presses
        :param event:
        """
        if not self.isStarted or self.cur_piece.pieceShape == 'NoShape':
            super(Board, self).keyPressEvent(event)
            return

        key = event.key()

        params = {
            Qt.Key_Left: (self.cur_piece, self.curX - 1, self.curY),
            Qt.Key_Right: (self.cur_piece, self.curX + 1, self.curY),
            Qt.Key_Up: (self.cur_piece.rotate_right(), self.curX, self.curY)
        }
        if key in params.keys():
            if not self.check_collision(*params[key]):
                self.move_shape(*params[key])
        else:
            super(Board, self).keyPressEvent(event)

    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            if self.isWaitingAfterLine:
                self.isWaitingAfterLine = False
                self.make_new_piece()
            else:
                self.one_line_down()
        else:
            super(Board, self).timerEvent(event)

    def reset(self):
        """
        Reset the board
        """
        if self.isPaused:
            return

        self.isStarted = True
        self.isWaitingAfterLine = False

        self.clear_board()
        self.game_over = False
        self.score = 0

        self.make_new_piece()
        self.timer.start(Board.Speed, self)

        return self.get_state_properties()

    def clear_board(self):
        """
        Clears the board
        """
        self.board = [['NoShape']*self.BoardWidth for _ in range(self.BoardHeight)]

    def one_line_down(self):
        """
        Moves shape down once per time. Also checks whether piece reached a bottom border of board
        """
        params = (self.cur_piece, self.curX, self.curY - 1)
        self.move_shape(*params) if not self.check_collision(*params) else self.piece_dropped()

    def piece_dropped(self):
        """
        When piece is at bottom border clears full lines and makes new piece on the board
        """
        for _ in self.cur_piece.coords:
            x, y = self.curX + _[0], self.curY - _[1]
            self.board[y][x] = self.cur_piece.pieceShape

        if self.check_lines():
            self.remove_full_lines()

        if not self.isWaitingAfterLine:
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
            self.isStarted = False

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

        self.isWaitingAfterLine = True
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

    def get_holes(self):
        """
        Get number of holes on the board
        :return: num_holes: int
        """
        num_holes = sum([len([_ for _ in row if _ == 'NoShape']) for row in self.board[:-1]])

        return num_holes

    def get_bumpiness_and_height(self):
        """
        Get bumpiness and height
        :return: total_bumpiness, total_height: tuple
        """
        board = np.array(self.board)
        mask = board != 'NoShape'
        invert_heights = np.where(mask.any(axis=0), np.argmax(mask, axis=0), self.BoardHeight)
        heights = self.BoardHeight - invert_heights
        total_height = np.sum(heights)

        currs = heights[:-1]
        nexts = heights[1:]
        diffs = np.abs(currs - nexts)
        total_bumpiness = np.sum(diffs)

        return total_bumpiness, total_height

    def get_state_properties(self):
        """
        Get general info about state
        :return: info: FloatTensor
        """
        lines_cleared = self.check_lines()
        holes = self.get_holes()
        bumpiness, height = self.get_bumpiness_and_height()

        return torch.FloatTensor([lines_cleared, holes, bumpiness, height])

    def get_next_states(self):
        """
        Get info about all possible states
        :return: states: dict
        """
        states = {}
        cur_piece = self.cur_piece

        for i in range(cur_piece.num_rotations):
            len_shape = sum([abs(_[0]) for _ in cur_piece.coords])
            valid_xs = self.BoardWidth - len_shape

            for x in range(valid_xs + 1):
                piece = cur_piece
                pos = {"x": x, "y": 0}
                while not self.check_collision(piece, *list(pos.values())):
                    pos["y"] += 1
                states[(x, i)] = self.get_state_properties()

            if i > 0:
                cur_piece = cur_piece.rotate_right()
        return states

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

        '''while not self.check_collision(self.cur_piece, self.curX, self.curY-1):
            self.one_line_down()'''

        if self.game_over:
            self.score -= 2

        return self.score, self.game_over


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
              'ZShape': Tetrominoe(1, ((0, -1), (0, 0), (-1, 0), (-1, 1)), 4),
              'SShape': Tetrominoe(2, ((0, -1), (0, 0), (1, 0), (1, 1)), 4),
              'LineShape': Tetrominoe(3, ((-1, 0), (0, 0), (1, 0), (2, 0)), 2),
              'TShape': Tetrominoe(4, ((-1, 0), (0, 0), (1, 0), (0, 1)), 4),
              'SquareShape': Tetrominoe(5, ((0, 0), (1, 0), (0, 1), (1, 1)), 1),
              'LShape': Tetrominoe(6, ((-1, -1), (0, -1), (0, 0), (0, 1)), 4),
              'MirroredLShape': Tetrominoe(7, ((1, -1), (0, -1), (0, 0), (0, 1)), 4)}

    def __init__(self):
        self.num_rotations = None
        self.pieceShape = None
        self.coords = np.array(self.shapes['NoShape'].coords)
        self.set_shape('NoShape')

    def set_shape(self, shape):
        """
        Sets the shape attributes
        :param shape: Tetrominoe
        """
        self.coords = np.array(self.shapes[shape].coords)
        self.pieceShape = shape
        self.num_rotations = self.shapes[shape].num_rotations
        print(self.pieceShape, self.num_rotations)

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
        result.pieceShape = self.pieceShape

        result.coords = [[-i[1], i[0]] for i in self.coords]

        return result


if __name__ == '__main__':
    app = QApplication([])
    tetris = Tetris()
    sys.exit(app.exec_())
