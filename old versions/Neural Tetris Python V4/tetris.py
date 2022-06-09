import numpy as np
from PIL import Image
import cv2
import torch
import random


class Tetris:
    piece_colors = [
        (0, 0, 0),
        (255, 255, 0),
        (147, 88, 254),
        (54, 175, 144),
        (255, 0, 0),
        (102, 217, 238),
        (254, 151, 32),
        (0, 0, 255)
    ]

    pieces = [
        [[1, 1],
         [1, 1]],

        [[0, 2, 0],
         [2, 2, 2]],

        [[0, 3, 3],
         [3, 3, 0]],

        [[4, 4, 0],
         [0, 4, 4]],

        [[5, 5, 5, 5]],

        [[0, 0, 6],
         [6, 6, 6]],

        [[7, 0, 0],
         [7, 7, 7]]
    ]

    def __init__(self):
        self.BoardHeight = 20
        self.BoardWidth = 10
        self.BlockSize = 40
        self.reset()

    def reset(self):
        self.board = [[0] * self.BoardWidth for _ in range(self.BoardHeight)]
        self.ClearedLines = 0
        self.bag = list(range(len(self.pieces)))
        random.shuffle(self.bag)
        self.ind = self.bag.pop()
        self.piece = [row[:] for row in self.pieces[self.ind]]
        self.CurrentPos = {"x": self.BoardWidth // 2 - len(self.piece[0]) // 2, "y": 0}
        self.GameOver = False
        return self.get_state_properties(self.board)

    def rotate(self, piece):
        numRowsOrig = ColsNew = len(piece)
        RowsNew = len(piece[0])
        rotated_array = []

        for i in range(RowsNew):
            new_row = [0] * ColsNew
            for j in range(ColsNew):
                new_row[j] = piece[(numRowsOrig - 1) - j][i]
            rotated_array.append(new_row)
        return rotated_array

    def get_state_properties(self, board):
        lines_cleared, board = self.check_cleared_rows(board)
        holes = self.get_holes(board)
        bumpiness, height = self.get_bumpiness_and_height(board)

        return torch.FloatTensor([lines_cleared, holes, bumpiness, height])

    def get_holes(self, board):
        num_holes = 0
        for col in zip(*board):
            row = 0
            while row < self.BoardHeight and col[row] == 0:
                row += 1
            num_holes += len([x for x in col[row + 1:] if x == 0])
        return num_holes

    def get_bumpiness_and_height(self, board):
        board = np.array(board)
        mask = board != 0
        invert_heights = np.where(mask.any(axis=0), np.argmax(mask, axis=0), self.BoardHeight)
        heights = self.BoardHeight - invert_heights
        total_height = np.sum(heights)
        currs = heights[:-1]
        nexts = heights[1:]
        diffs = np.abs(currs - nexts)
        total_bumpiness = np.sum(diffs)
        return total_bumpiness, total_height

    def get_next_states(self):
        states = {}
        piece_id = self.ind
        curr_piece = [row[:] for row in self.piece]
        if piece_id == 0:  # O piece
            num_rotations = 1
        elif piece_id == 2 or piece_id == 3 or piece_id == 4:
            num_rotations = 2
        else:
            num_rotations = 4

        for i in range(num_rotations):
            valid_xs = self.BoardWidth - len(curr_piece[0])
            for x in range(valid_xs + 1):
                piece = [row[:] for row in curr_piece]
                pos = {"x": x, "y": 0}
                while not self.check_collision(piece, pos):
                    pos["y"] += 1
                self.truncate(piece, pos)
                board = self.store(piece, pos)
                states[(x, i)] = self.get_state_properties(board)
            curr_piece = self.rotate(curr_piece)
        return states

    def get_current_board_state(self):
        board = [x[:] for x in self.board]
        for y in range(len(self.piece)):
            for x in range(len(self.piece[y])):
                board[y + self.CurrentPos["y"]][x + self.CurrentPos["x"]] = self.piece[y][x]
        return board

    def new_piece(self):
        if not len(self.bag):
            self.bag = list(range(len(self.pieces)))
            random.shuffle(self.bag)
        self.ind = self.bag.pop()
        self.piece = [row[:] for row in self.pieces[self.ind]]
        self.CurrentPos = {"x": self.BoardWidth // 2 - len(self.piece[0]) // 2,
                           "y": 0
                           }
        if self.check_collision(self.piece, self.CurrentPos):
            self.GameOver = True

    def check_collision(self, piece, pos):
        future_y = pos["y"] + 1
        for y in range(len(piece)):
            for x in range(len(piece[y])):
                if future_y + y > self.BoardHeight - 1 or self.board[future_y + y][pos["x"] + x] and piece[y][x]:
                    return True
        return False

    def truncate(self, piece, pos):
        gameover = False
        last_collision_row = -1
        for y in range(len(piece)):
            for x in range(len(piece[y])):
                if self.board[pos["y"] + y][pos["x"] + x] and piece[y][x]:
                    if y > last_collision_row:
                        last_collision_row = y

        if pos["y"] - (len(piece) - last_collision_row) < 0 and last_collision_row > -1:
            while last_collision_row >= 0 and len(piece) > 1:
                gameover = True
                last_collision_row = -1
                del piece[0]
                for y in range(len(piece)):
                    for x in range(len(piece[y])):
                        if self.board[pos["y"] + y][pos["x"] + x] and piece[y][x] and y > last_collision_row:
                            last_collision_row = y
        return gameover

    def store(self, piece, pos):
        board = [x[:] for x in self.board]
        for y in range(len(piece)):
            for x in range(len(piece[y])):
                if piece[y][x] and not board[y + pos["y"]][x + pos["x"]]:
                    board[y + pos["y"]][x + pos["x"]] = piece[y][x]
        return board

    def check_cleared_rows(self, board):
        to_delete = []
        for i, row in enumerate(board[::-1]):
            if 0 not in row:
                to_delete.append(len(board) - 1 - i)
        if len(to_delete) > 0:
            board = self.remove_row(board, to_delete)
        return len(to_delete), board

    def remove_row(self, board, indices):
        for i in indices[::-1]:
            del board[i]
            board = [[0 for _ in range(self.BoardWidth)]] + board
        return board

    def step(self, action, render=None):
        x, numRotations = action
        self.CurrentPos = {"x": x, "y": 0}
        for _ in range(numRotations):
            self.piece = self.rotate(self.piece)

        while not self.check_collision(self.piece, self.CurrentPos):
            self.CurrentPos["y"] += 1
            if render:
                self.render()

        overflow = self.truncate(self.piece, self.CurrentPos)
        if overflow:
            self.GameOver = True

        self.board = self.store(self.piece, self.CurrentPos)

        lines_cleared, self.board = self.check_cleared_rows(self.board)
        self.ClearedLines += lines_cleared
        if not self.GameOver:
            self.new_piece()

        return self.ClearedLines, self.GameOver

    def render(self):
        if not self.GameOver:
            img = [self.piece_colors[p] for row in self.get_current_board_state() for p in row]
        else:
            img = [self.piece_colors[p] for row in self.board for p in row]
        img = np.array(img).reshape((self.BoardHeight, self.BoardWidth, 3)).astype(np.uint8)
        img = img[..., ::-1]
        img = Image.fromarray(img, "RGB")

        img = img.resize((self.BoardWidth * self.BlockSize, self.BoardHeight * self.BlockSize))
        img = np.array(img)

        cv2.imshow("Neural Tetris CDV", img)
        cv2.waitKey(1)
