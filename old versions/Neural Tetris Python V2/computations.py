import numpy as np
import torch

from main import Board


class Computations(Board):

    def __init__(self, parent, data):
        super().__init__(parent)
        self.set_params(data)

    def set_params(self, *data):
        self.board = data[0][0]
        self.BoardWidth = data[0][1]
        self.BoardHeight = data[0][2]
        self.cur_piece = data[0][3]

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
            
            CoordsNotRotated = {
                'ZShape': (2, 7),
                'SShape': (0, 9),
                'LineShape': (2, 7),
                'TShape': (1, 8),
                'SquareShape': (0, 8),
                'LShape': (0, 9),
                'MirroredLShape': (0, 9)
            }

            CoordsRotated = {
                'ZShape': (2, 7),
                'SShape': (0, 9),
                'LineShape': (0, 9),
                'TShape': (1, 8),
                'SquareShape': (0, 8),
                'LShape': (0, 9),
                'MirroredLShape': (0, 9)
            }

            for x in range(3, 7):
                piece = cur_piece
                pos = {"x": x, "y": 0}
                while not self.check_collision(piece, *list(pos.values())):
                    pos["y"] += 1
                states[(x, i)] = self.get_state_properties()

            if i > 0:
                cur_piece = cur_piece.rotate_right()

        return states
