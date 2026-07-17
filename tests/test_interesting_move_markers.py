import unittest
from unittest.mock import patch

import main
from position import Position


class FakePiece:
    def __init__(self, moves):
        self.moves = moves

    def get_moves(self, board, pos):
        return [(move, False) for move in self.moves]


class FakeBoard:
    def __init__(self, piece):
        self.piece = piece

    def get(self, pos):
        return self.piece


class InterestingMoveMarkerTest(unittest.TestCase):
    def test_checkmate_marker_replaces_an_earlier_stalemate_marker(self):
        piece_pos = Position(0, 0)
        stalemate_move = Position(1, 0)
        checkmate_move = Position(2, 0)
        main.board = FakeBoard(FakePiece([stalemate_move, checkmate_move]))
        main.selected_piece_pos = None
        main.checkmate_positions = set()
        main.stalemate_positions = set()

        outcomes = {
            stalemate_move: (False, True),
            checkmate_move: (True, False),
        }
        with patch.object(
            main,
            "check_checkmate_and_stalemate",
            side_effect=lambda position, move: outcomes[move],
        ):
            main.add_interesting_moves(piece_pos)

        self.assertIn(piece_pos, main.checkmate_positions)
        self.assertNotIn(piece_pos, main.stalemate_positions)


if __name__ == "__main__":
    unittest.main()
