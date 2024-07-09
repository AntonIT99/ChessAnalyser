from abc import ABC, abstractmethod

from board import Position
from color import Color


class Piece(ABC):
    def __init__(self, color, symbol):
        self.color = color
        self.symbol = symbol

    def render(self, font):
        return font.render(self.symbol, True, self.color.value)

    @abstractmethod
    def get_moves(self, board, pos: Position):
        """
        Function to return a list of squares that a piece can move to.

        Parameters:
        - board: 2D list representing the chess board.
        - row: Current row of the piece.
        - col: Current column of the piece.

        Returns:
        - List of tuples representing valid squares the piece can move to and if the move is a capture or not (move: Postion, is_capture_move: bool).
        """
        pass

    def get_capture_moves(self, board, pos: Position):
        """
        Returns:
        - List of Position representing capture moves only.
        """
        return [move for move, is_capture_move in self.get_moves(board, pos) if is_capture_move]

    def get_move_warnings(self, board, pos: Position):
        """
        Returns:
        - List of Tuples (location_of_move_warning: Position, origin_of_threat: Position) representing move warnings.
        """
        warnings = []

        for move, is_capture_move in self.get_moves(board, pos):
            warning_found = False
            future_board = board.simulate_future_board(move_origin=pos, move_destination=move)
            for opponent_pos in self.__get_opponent_positions(future_board):
                opponent_piece = future_board.get(opponent_pos)
                for opponent_move in opponent_piece.get_capture_moves(future_board, opponent_pos):
                    if move == opponent_move:
                        warnings.append((move, opponent_pos))
                        warning_found = True
                        break
                if warning_found:
                    break
            if warning_found:
                continue

        return warnings

    def is_currently_threatened(self, board, pos: Position):
        for position in board.positions:
            if position != pos and board.get(position) is not None and board.get(position).color != self.color:
                opponent_piece = board.get(position)
                for capture_move in opponent_piece.get_capture_moves(board, position):
                    if capture_move == pos:
                        return True
        return False

    def __get_opponent_positions(self, board):
        positions = []
        for pos in board.positions:
            if board.get(pos) is not None and board.get(pos).color != self.color:
                positions.append(pos)
        return positions


class King(Piece):
    def __init__(self, color):
        super().__init__(color, "♚")

    def get_moves(self, board, pos):
        moves = []
        row = pos.row
        col = pos.column

        king_moves = [
            (row - 1, col - 1), (row - 1, col), (row - 1, col + 1),
            (row, col - 1), (row, col + 1),
            (row + 1, col - 1), (row + 1, col), (row + 1, col + 1)
        ]

        for r, c in king_moves:
            if 0 <= r <= board.last_row and 0 <= c <= board.last_column:
                if board.get(Position(row=r, column=c)) is None:
                    moves.append((Position(row=r, column=c), False))
                elif board.get(Position(row=r, column=c)).color != self.color:
                    moves.append((Position(row=r, column=c), True))

        return moves


class Queen(Piece):
    def __init__(self, color):
        super().__init__(color, "♛")

    def get_moves(self, board, pos):
        moves = []
        row = pos.row
        col = pos.column

        # Directions for queen: up, down, left, right, diagonals (up-right), (up-left), (down-right), (down-left)
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),  # Vertical and horizontal
            (-1, 1), (-1, -1), (1, 1), (1, -1)  # Diagonals
        ]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r <= board.last_row and 0 <= c <= board.last_column:
                if board.get(Position(row=r, column=c)) is None:
                    moves.append((Position(row=r, column=c), False))
                    r += dr
                    c += dc
                else:
                    # If there's a piece blocking, stop in that direction
                    # Capture move if the piece is of the opposite color
                    if board.get(Position(row=r, column=c)).color != self.color:
                        moves.append((Position(row=r, column=c), True))
                    break

        return moves


class Bishop(Piece):
    def __init__(self, color):
        super().__init__(color, "♝")

    def get_moves(self, board, pos):
        moves = []
        row = pos.row
        col = pos.column

        # Directions for diagonals: (up-right), (up-left), (down-right), (down-left)
        directions = [(-1, 1), (-1, -1), (1, 1), (1, -1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r <= board.last_row and 0 <= c <= board.last_column:
                if board.get(Position(row=r, column=c)) is None:
                    moves.append((Position(row=r, column=c), False))
                    r += dr
                    c += dc
                else:
                    # If there's a piece blocking, stop in that direction
                    # Capture move if the piece is of the opposite color
                    if board.get(Position(row=r, column=c)).color != self.color:
                        moves.append((Position(row=r, column=c), True))
                    break

        return moves


class Knight(Piece):
    def __init__(self, color):
        super().__init__(color, "♞")

    def get_moves(self, board, pos):
        moves = []
        row = pos.row
        col = pos.column

        knight_moves = [
            (row - 2, col - 1), (row - 2, col + 1),
            (row - 1, col - 2), (row - 1, col + 2),
            (row + 1, col - 2), (row + 1, col + 2),
            (row + 2, col - 1), (row + 2, col + 1)
        ]

        for r, c in knight_moves:
            if 0 <= r <= board.last_row and 0 <= c <= board.last_column:
                if board.get(Position(row=r, column=c)) is None:
                    moves.append((Position(row=r, column=c), False))
                elif board.get(Position(row=r, column=c)).color != self.color:
                    moves.append((Position(row=r, column=c), True))

        return moves


class Rook(Piece):
    def __init__(self, color):
        super().__init__(color, "♜")

    def get_moves(self, board, pos):
        moves = []
        row = pos.row
        col = pos.column

        # Directions: up, down, left, right
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r <= board.last_row and 0 <= c <= board.last_column:
                if board.get(Position(row=r, column=c)) is None:
                    moves.append((Position(row=r, column=c), False))
                    r += dr
                    c += dc
                else:
                    # If there's a piece blocking, stop in that direction
                    # Capture move if the piece is of the opposite color
                    if board.get(Position(row=r, column=c)).color != self.color:
                        moves.append((Position(row=r, column=c), True))
                    break

        return moves


class Pawn(Piece):
    def __init__(self, color):
        super().__init__(color, "♟")

    @classmethod
    def promote(cls, board, position, new_type: str):
        color = board.get(position).color
        if new_type == "r":
            board.set(position, Rook(color))
        elif new_type == "b":
            board.set(position, Bishop(color))
        elif new_type == "k":
            board.set(position, Knight(color))
        else:
            board.set(position, Queen(color))

    def get_moves(self, board, pos):
        moves = []
        row = pos.row
        col = pos.column

        if self.color == Color.BLACK:
            # White pawn moves downward (increasing row number)
            # Normal move (one square forward)
            if row < board.last_row and board.get(Position(row=row + 1, column=col)) is None:
                moves.append((Position(row=row + 1, column=col), False))

            # Initial double move (two squares forward)
            if row == 1 and board.get(Position(row=row + 1, column=col)) is None and board.get(Position(row=row + 2, column=col)) is None:
                moves.append((Position(row=row + 2, column=col), False))

            # Capture moves (diagonally forward)
            if row < board.last_row and col > 0 and board.get(Position(row=row + 1, column=col - 1)) is not None and board.get(Position(row=row + 1, column=col - 1)).color != self.color:
                moves.append((Position(row=row + 1, column=col - 1), True))
            if row < board.last_row and col < board.last_column and board.get(Position(row=row + 1, column=col + 1)) is not None and board.get(
                    Position(row=row + 1, column=col + 1)).color != self.color:
                moves.append((Position(row=row + 1, column=col + 1), True))

        elif self.color == Color.WHITE:
            # Black pawn moves upward (decreasing row number)
            # Normal move (one square forward)
            if row > 0 and board.get(Position(row=row - 1, column=col)) is None:
                moves.append((Position(row=row - 1, column=col), False))

            # Initial double move (two squares forward)
            if row == board.last_row - 1 and board.get(Position(row=row - 1, column=col)) is None and board.get(Position(row=row - 2, column=col)) is None:
                moves.append((Position(row=row - 2, column=col), False))

            # Capture moves (diagonally forward)
            if row > 0 and col > 0 and board.get(Position(row=row - 1, column=col - 1)) is not None and board.get(Position(row=row - 1, column=col - 1)).color != self.color:
                moves.append((Position(row=row - 1, column=col - 1), True))
            if row > 0 and col < board.last_column and board.get(Position(row=row - 1, column=col + 1)) is not None and board.get(Position(row=row - 1, column=col + 1)).color != self.color:
                moves.append((Position(row=row - 1, column=col + 1), True))

        return moves
