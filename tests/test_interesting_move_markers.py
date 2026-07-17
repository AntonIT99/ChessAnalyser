import unittest
from unittest.mock import patch

from board import Board
from color import Color
import main
from piece import Bishop, King, Pawn, Queen
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
    def setUp(self):
        main.selected_piece_pos = None
        main.checkmate_positions = set()
        main.stalemate_positions = set()

    def test_checkmate_marker_replaces_an_earlier_stalemate_marker(self):
        piece_pos = Position(0, 0)
        stalemate_move = Position(1, 0)
        checkmate_move = Position(2, 0)
        main.board = FakeBoard(FakePiece([stalemate_move, checkmate_move]))
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

    def test_queen_from_reported_position_gets_checkmate_marker(self):
        state = [[None for _ in range(8)] for _ in range(8)]
        state[0][4] = King(Color.BLACK)
        state[3][0] = Pawn(Color.BLACK)
        state[4][0] = Pawn(Color.WHITE)
        state[4][2] = Bishop(Color.BLACK)
        state[5][0] = King(Color.WHITE)
        state[6][3] = Queen(Color.BLACK)
        main.board = Board(state)
        queen_pos = Position(6, 3)

        main.add_interesting_moves(queen_pos)

        self.assertIn(queen_pos, main.checkmate_positions)
        self.assertNotIn(queen_pos, main.stalemate_positions)


if __name__ == "__main__":
    unittest.main()
