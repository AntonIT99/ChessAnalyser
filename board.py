import copy

from piece import castling, en_passant
from position import Position


class Board:

    def __init__(self, state):
        self.__state = state
        self.rows = len(state)
        self.columns = len(state[0])
        self.last_row = self.rows - 1
        self.last_column = self.columns - 1
        self.undo_stack = []
        self.redo_stack = []
        self.positions = []
        for row in range(self.rows):
            for column in range(self.columns):
                self.positions.append(Position(row=row, column=column))

    def get(self, pos: Position):
        return self.__state[pos.row][pos.column]

    def has_previous_state(self) -> bool:
        return len(self.undo_stack) > 0

    def get_previous_state(self, pos: Position):
        if len(self.undo_stack) > 0:
            return self.undo_stack[-1][pos.row][pos.column]
        return None

    def set(self, pos: Position, value):
        # Save the current state to the undo stack before changing it
        self.undo_stack.append(copy.deepcopy(self.__state))
        # Update the state
        self.__state[pos.row][pos.column] = value
        # Clear the redo stack because we have a new state
        self.redo_stack.clear()

    def do_move(self, origin: Position, destination: Position):
        is_en_passant, captured_position = en_passant(self, origin, destination)
        is_castling, other_origin = castling(self, origin, destination)

        # if the destination is not the origin and the destination is not occupied or is occupied by a piece of the opposite color
        if origin != destination and (self.get(origin) is not None or self.get(origin).color != self.get(destination).color):

            # Save the current state to the undo stack before changing it
            self.undo_stack.append(copy.deepcopy(self.__state))

            # Update the state by doing the move
            if is_castling:
                other = self.get(other_origin)
                other_destination = other.get_castling_move(self, origin, other_origin)
                self.__state[other_destination.row][other_destination.column] = other
                self.__state[other_origin.row][other_origin.column] = None
                other.has_moved = True
            if is_en_passant:
                self.__state[captured_position.row][captured_position.column] = None
            piece = self.get(origin)
            self.__state[destination.row][destination.column] = piece
            self.__state[origin.row][origin.column] = None
            piece.has_moved = True

            # Clear the redo stack because we have a new state
            self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            # No actions to undo
            return
        # Move the current state to the redo stack
        self.redo_stack.append(copy.deepcopy(self.__state))
        # Pop the last state from the undo stack and set it as the current state
        self.__state = self.undo_stack.pop()

    def redo(self):
        if not self.redo_stack:
            # No actions to undo
            return
        # Move the current state to the undo stack
        self.undo_stack.append(copy.deepcopy(self.__state))
        # Pop the last state from the redo stack and set it as the current state
        self.__state = self.redo_stack.pop()

    def simulate_future_board(self, move_origin: Position, move_destination: Position):
        future_board = Board(copy.deepcopy(self.__state))
        future_board.do_move(origin=move_origin, destination=move_destination)
        return future_board
