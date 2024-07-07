import copy


class Position:
    def __init__(self, row, column):
        self.row = row
        self.column = column

    def __eq__(self, other):
        if isinstance(other, Position):
            return self.row == other.row and self.column == other.column
        return False

    @classmethod
    def copy(cls, other):
        return cls(row=other.row, column=other.column)


class Board:

    def __init__(self, state):
        self.state = state
        self.rows = len(state)
        self.columns = len(state[0])
        self.last_row = self.rows - 1
        self.last_column = self.columns - 1
        self.positions = []
        for row in range(self.rows):
            for column in range(self.columns):
                self.positions.append(Position(row=row, column=column))

    def get(self, pos: Position):
        return self.state[pos.row][pos.column]

    def set(self, pos: Position, value):
        self.state[pos.row][pos.column] = value

    def do_move(self, origin: Position, destination: Position):
        if self.get(origin) is not None:
            self.set(destination, self.get(origin))
            self.set(origin, None)

    def simulate_future_board(self, move_origin: Position, move_destination: Position):
        future_board = Board(copy.deepcopy(self.state))
        future_board.do_move(origin=move_origin, destination=move_destination)
        return future_board
