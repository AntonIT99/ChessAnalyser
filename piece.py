from abc import ABC, abstractmethod
from typing import Tuple, Optional

from position import Position
from color import Color


class Piece(ABC):
    def __init__(self, color, symbol, value):
        self.color = color
        self.symbol = symbol
        self.has_moved = False
        self.value = value

    def render(self, font):
        return font.render(self.symbol, True, self.color.value)

    @abstractmethod
    def get_moves_ignore_illegal(self, board, pos: Position):
        """
        Function to return a list of squares that a piece can move to.

        Parameters:
        - board: 2D list representing the chess board.
        - row: Current row of the piece.
        - col: Current column of the piece.

        Returns:
        - List of tuples representing squares the piece can move to and if the move is a capture or not (move: Postion, is_capture_move: bool).
        """
        pass

    def get_moves(self, board, pos):
        """
        Returns:
        - List of tuples representing squares the piece can move to (only legal moves) and if the move is a capture or not (move: Postion, is_capture_move: bool).
        """
        return self.only_legal_moves(board, pos, self.get_moves_ignore_illegal(board, pos))

    def only_legal_moves(self, board, pos: Position, moves):
        """
        Returns:
        - List of tuples representing squares the piece can move to (only legal moves) and if the move is a capture or not (move: Postion, is_capture_move: bool).
         """
        legal_moves = []

        for move, is_capture_move in moves:
            future_board = board.simulate_future_board(move_origin=pos, move_destination=move)
            king_pos = self.get_own_king_position(future_board)
            if king_pos is not None and not future_board.get(king_pos).is_currently_threatened(future_board, king_pos):
                legal_moves.append((move, is_capture_move))

        return legal_moves

    def get_capture_moves(self, board, pos: Position):
        """
        Returns:
        - List of Position representing capture moves only.
        """
        return [move for move, is_capture_move in self.get_moves(board, pos) if is_capture_move]

    def get_unsafe_moves(self, board, pos: Position):
        """
        Returns:
        - List of Tuples (location_of_move_warning: Position, origin_of_threat: Position, destination_of_threat: Position) representing unsafe moves.
        """
        unsafe_moves = []

        # Unsafe moves are forbidden for Kings
        if not isinstance(self, King):
            for move, is_capture_move in self.get_moves(board, pos):
                warning_found = False
                future_board = board.simulate_future_board(move_origin=pos, move_destination=move)
                for opponent_pos in self.__get_opponent_positions(future_board):
                    opponent_piece = future_board.get(opponent_pos)
                    for opponent_move in opponent_piece.get_capture_moves(future_board, opponent_pos):
                        is_en_passant, captured_position = en_passant(future_board, opponent_pos, opponent_move)
                        if move == opponent_move or (is_en_passant and move == captured_position):
                            unsafe_moves.append((move, opponent_pos, opponent_move))
                            warning_found = True
                            break
                    if warning_found:
                        break
                if warning_found:
                    continue

        return unsafe_moves

    def get_safe_moves(self, board, pos: Position):
        """
        Returns:
        - List of Positions representing safe moves.
        """
        safe_moves = []

        for move, is_capture_move in self.get_moves(board, pos):
            warning_found = False
            future_board = board.simulate_future_board(move_origin=pos, move_destination=move)
            for opponent_pos in self.__get_opponent_positions(future_board):
                opponent_piece = future_board.get(opponent_pos)
                for opponent_move in opponent_piece.get_capture_moves(future_board, opponent_pos):
                    is_en_passant, captured_position = en_passant(future_board, opponent_pos, opponent_move)
                    if move == opponent_move or (is_en_passant and move == captured_position):
                        warning_found = True
                        break
                if warning_found:
                    break
            if not warning_found:
                safe_moves.append(move)

        return safe_moves

    def can_move_to_position(self, board, origin: Position, destination: Position):
        for move, is_capture_move in self.get_moves(board, origin):
            if move == destination:
                return True
        return False

    def is_currently_threatened(self, board, pos: Position):
        for threat_position in board.positions:
            if threat_position != pos and board.get(threat_position) is not None and board.get(threat_position).color != self.color:
                opponent_piece = board.get(threat_position)
                for capture_move in opponent_piece.get_capture_moves(board, threat_position):
                    is_en_passant, captured_position = en_passant(board, threat_position, capture_move)
                    if (is_en_passant and captured_position == pos) or (not is_en_passant and capture_move == pos):
                        return True
        return False

    """
    Returns:
    - List of Tuples (threat_origin, threat destination)
    """
    def get_threats(self, board, pos: Position):
        threats_positions = []
        for threat_position in board.positions:
            opponent_piece = board.get(threat_position)
            if threat_position != pos and opponent_piece is not None and opponent_piece.color != self.color:
                for capture_move in opponent_piece.get_capture_moves(board, threat_position):
                    is_en_passant, captured_position = en_passant(board, threat_position, capture_move)
                    if (is_en_passant and captured_position == pos) or (not is_en_passant and capture_move == pos):
                        threats_positions.append((threat_position, capture_move))
        return threats_positions

    """
    Returns:
    - Tuple (threat_origin, threat destination)
    """
    def get_threat_with_smallest_value(self, board, pos: Position) -> Optional[Tuple[Position, Position]]:
        threats = self.get_threats(board, pos)
        if len(threats) > 0:
            return min(threats, key=lambda threat: board.get(threat[0]).value)
        else:
            return None

    def get_own_king_position(self, board):
        king_pos = None
        for pos in board.positions:
            if isinstance(board.get(pos), King) and board.get(pos).color == self.color:
                king_pos = pos
        return king_pos

    def __get_opponent_positions(self, board):
        positions = []
        for pos in board.positions:
            if board.get(pos) is not None and board.get(pos).color != self.color:
                positions.append(pos)
        return positions


class King(Piece):
    def __init__(self, color):
        super().__init__(color, "♚", 1000)

    def is_currently_threatened(self, board, pos: Position):
        for threat_position in board.positions:
            if threat_position != pos and board.get(threat_position) is not None and board.get(threat_position).color != self.color:
                opponent_piece = board.get(threat_position)
                for move, is_capture_move in opponent_piece.get_moves_ignore_illegal(board, threat_position):
                    if move == pos:
                        return True
        return False

    def get_moves_ignore_illegal(self, board, pos):
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
                move = Position(row=r, column=c)
                is_capture_move = board.get(move) is not None
                if board.get(move) is None or board.get(move).color != self.color:
                    moves.append((move, is_capture_move))

        return moves

    @classmethod
    def get_castling_move(cls, board, position1: Position, position2: Position) -> Position:
        king_position = position1 if isinstance(board.get(position1), King) else position2
        rook_position = position2 if isinstance(board.get(position1), King) else position1
        return Position(row=king_position.row, column=king_position.column + get_castling_direction(king_position, rook_position) * 2)

    def get_moves(self, board, pos):
        legal_moves = []

        for move, is_capture_move in self.get_moves_ignore_illegal(board, pos):
            future_board = board.simulate_future_board(move_origin=pos, move_destination=move)
            if not future_board.get(move).is_currently_threatened(future_board, move):
                legal_moves.append((move, is_capture_move))

        for position in board.positions:
            if isinstance(board.get(position), Rook) and board.get(position).color == self.color:
                if can_castle(board, pos, position):
                    legal_moves.append((King.get_castling_move(board, pos, position), False))

        return legal_moves


class Queen(Piece):
    def __init__(self, color):
        super().__init__(color, "♛", 9)

    def get_moves_ignore_illegal(self, board, pos):
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
        super().__init__(color, "♝", 3)

    def get_moves_ignore_illegal(self, board, pos):
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
        super().__init__(color, "♞", 3)

    def get_moves_ignore_illegal(self, board, pos):
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
        super().__init__(color, "♜", 5)

    def get_moves_ignore_illegal(self, board, pos):
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

    @classmethod
    def get_castling_move(cls, board, position1: Position, position2: Position) -> Position:
        rook_position = position1 if isinstance(board.get(position1), Rook) else position2
        king_position = position2 if isinstance(board.get(position1), Rook) else position1
        direction = get_castling_direction(king_position, rook_position)
        return Position(row=rook_position.row, column=rook_position.column - direction * (2 if direction > 0 else 3))


class Pawn(Piece):
    def __init__(self, color):
        super().__init__(color, "♟", 1)

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

    def get_en_passant_moves(self, board, pos):
        moves = []
        if board.has_previous_state():

            row = pos.row
            col = pos.column

            if self.color == Color.BLACK and row == board.last_row - 3:
                if col > 0:
                    opponent_pawn = board.get(Position(row=row, column=col - 1))
                    opponent_pawn_previous_state = board.get_previous_state(Position(row=row + 2, column=col - 1))
                    if isinstance(opponent_pawn, Pawn) and opponent_pawn.color != self.color and isinstance(opponent_pawn_previous_state, Pawn) and opponent_pawn_previous_state.color != self.color:
                        moves.append(Position(row=row + 1, column=col - 1))
                elif col < board.last_column:
                    opponent_pawn = board.get(Position(row=row, column=col + 1))
                    opponent_pawn_previous_state = board.get_previous_state(Position(row=row + 2, column=col + 1))
                    if isinstance(opponent_pawn, Pawn) and opponent_pawn.color != self.color and isinstance(opponent_pawn_previous_state, Pawn) and opponent_pawn_previous_state.color != self.color:
                        moves.append(Position(row=row + 1, column=col + 1))

            elif self.color == Color.WHITE and row == 3:
                if col > 0:
                    opponent_pawn = board.get(Position(row=row, column=col - 1))
                    opponent_pawn_previous_state = board.get_previous_state(Position(row=row - 2, column=col - 1))
                    if isinstance(opponent_pawn, Pawn) and opponent_pawn.color != self.color and isinstance(opponent_pawn_previous_state, Pawn) and opponent_pawn_previous_state.color != self.color:
                        moves.append(Position(row=row - 1, column=col - 1))
                if col < board.last_column:
                    opponent_pawn = board.get(Position(row=row, column=col + 1))
                    opponent_pawn_previous_state = board.get_previous_state(Position(row=row - 2, column=col + 1))
                    if isinstance(opponent_pawn, Pawn) and opponent_pawn.color != self.color and isinstance(opponent_pawn_previous_state, Pawn) and opponent_pawn_previous_state.color != self.color:
                        moves.append(Position(row=row - 1, column=col + 1))

        return moves

    def get_moves_ignore_illegal(self, board, pos):
        moves = []
        row = pos.row
        col = pos.column

        if self.color == Color.BLACK:
            # Black pawn moves downward (increasing row number)
            # Normal move (one square forward)
            if row < board.last_row and board.get(Position(row=row + 1, column=col)) is None:
                moves.append((Position(row=row + 1, column=col), False))

            # Initial double move (two squares forward)
            if row == 1 and board.get(Position(row=row + 1, column=col)) is None and board.get(Position(row=row + 2, column=col)) is None:
                moves.append((Position(row=row + 2, column=col), False))

            # Capture moves (diagonally forward)
            if row < board.last_row and col > 0 and board.get(Position(row=row + 1, column=col - 1)) is not None and board.get(Position(row=row + 1, column=col - 1)).color != self.color:
                moves.append((Position(row=row + 1, column=col - 1), True))
            if row < board.last_row and col < board.last_column and board.get(Position(row=row + 1, column=col + 1)) is not None and board.get(Position(row=row + 1, column=col + 1)).color != self.color:
                moves.append((Position(row=row + 1, column=col + 1), True))

        elif self.color == Color.WHITE:
            # White pawn moves upward (decreasing row number)
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

        for move in self.get_en_passant_moves(board, pos):
            moves.append((move, True))

        return moves


def can_castle(board, king_position, rook_position) -> bool | int:
    king = board.get(king_position)
    rook = board.get(rook_position)
    if king is not None and rook is not None:
        if king.color == rook.color and not king.has_moved and not rook.has_moved and king_position.row == rook_position.row:
            for col in range(min(king_position.column + 1, rook_position.column + 1), max(king_position.column, rook_position.column)):
                if board.get(Position(row=king_position.row, column=col)) is not None:
                    return False
            direction = get_castling_direction(king_position, rook_position)
            for col in range(king_position.column, king_position.column + direction * 3, direction):
                if king.is_currently_threatened(board, Position(row=king_position.row, column=col)):
                    return False
            return True
    return False


def get_castling_direction(king_position, rook_position):
    return int((rook_position.column - king_position.column) / abs(rook_position.column - king_position.column))


def castling(board, move_origin: Position, move_destination: Position) -> (bool, Position):
    piece = board.get(move_origin)
    if isinstance(piece, King):
        for position in board.positions:
            if isinstance(board.get(position), Rook) and board.get(position).color == piece.color and can_castle(board, move_origin, position):
                if abs(move_destination.column - move_origin.column) == 2 and move_destination.row == move_origin.row:
                    direction = int((move_destination.column - move_origin.column) / abs(move_destination.column - move_origin.column))
                    if (position.column == 0 and direction < 0) or (position.column == board.last_column and direction > 0):
                        return True, position
    return False, None


def en_passant(board, move_origin: Position, move_destination: Position) -> (bool, Position):
    """
    Returns:
        - if a move is en_passant or not
        - Position of the captured pawn
    """
    if board.has_previous_state() and abs(move_destination.column - move_origin.column) == 1:
        own_pawn = board.get(move_origin)
        captured_pawn_position = Position(row=move_origin.row, column=move_destination.column)
        captured_pawn = board.get(captured_pawn_position)
        if isinstance(own_pawn, Pawn) and isinstance(captured_pawn, Pawn) and own_pawn.color != captured_pawn.color:
            if own_pawn.color == Color.BLACK and move_origin.row == board.last_row - 3 and move_destination.row == move_origin.row + 1:
                captured_pawn_prev = board.get_previous_state(Position(row=board.last_row - 1, column=move_destination.column))
                if isinstance(captured_pawn_prev, Pawn) and own_pawn.color != captured_pawn_prev.color:
                    return True, captured_pawn_position
            elif own_pawn.color == Color.WHITE and move_origin.row == 3 and move_destination.row == move_origin.row - 1:
                captured_pawn_prev = board.get_previous_state(Position(row=1, column=move_destination.column))
                if isinstance(captured_pawn_prev, Pawn) and own_pawn.color != captured_pawn_prev.color:
                    return True, captured_pawn_position
    return False, None


def get_captured_piece_position(board, capture_move_origin: Position, capture_move_destination: Position):
    captured_piece_position = capture_move_destination
    is_en_passant, captured_piece_pos = en_passant(board, capture_move_origin, capture_move_destination)
    if is_en_passant:
        captured_piece_position = captured_piece_pos
    return captured_piece_position


def get_captured_piece(board, capture_move_origin: Position, capture_move_destination: Position):
    return board.get(get_captured_piece_position(board, capture_move_origin, capture_move_destination))