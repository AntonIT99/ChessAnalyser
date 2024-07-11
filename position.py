class Position:
    def __init__(self, row, column):
        self.row = row
        self.column = column

    def __eq__(self, other):
        if isinstance(other, Position):
            return self.row == other.row and self.column == other.column
        return False

    def __hash__(self):
        return hash((self.row, self.column))

    @classmethod
    def copy(cls, other):
        return cls(row=other.row, column=other.column)
