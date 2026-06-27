import unittest

from board import Board
from color import Color
import main
from piece import Bishop, King, Knight, Pawn, Rook
from position import Position


def build_problem_board():
    state = [[None for _ in range(8)] for _ in range(8)]
    state[0][2] = Rook(Color.BLACK)
    state[1][1] = Bishop(Color.BLACK)
    state[1][5] = Bishop(Color.BLACK)
    state[1][6] = King(Color.BLACK)
    state[1][7] = Bishop(Color.BLACK)
    state[2][0] = Bishop(Color.BLACK)
    state[2][2] = Rook(Color.BLACK)
    state[2][5] = Pawn(Color.BLACK)
    state[3][3] = Knight(Color.WHITE)
    state[4][1] = Bishop(Color.WHITE)
    state[4][6] = Bishop(Color.WHITE)
    state[5][0] = Rook(Color.WHITE)
    state[5][2] = Bishop(Color.WHITE)
    state[5][5] = Bishop(Color.WHITE)
    state[6][5] = King(Color.WHITE)
    state[6][7] = Bishop(Color.WHITE)
    return Board(state)


class RetaliationTest(unittest.TestCase):
    def test_king_recapture_keeps_problem_pawn_trade_neutral(self):
        board = build_problem_board()
        pawn_pos = Position(2, 5)
        knight_pos = Position(3, 3)

        future_board = board.simulate_future_board(knight_pos, pawn_pos)

        self.assertEqual(
            (6, 6),
            main.calculate_retaliation_with_capture(pawn_pos, future_board, board.get(pawn_pos)),
        )

    def test_problem_pawn_is_marked_neutral_not_unfavorable(self):
        main.board = build_problem_board()
        main.threatened_positions = set()
        main.threatened_positions_with_favorable_relation_possibility = set()
        main.threatened_positions_with_neutral_relation_possibility = set()
        main.threatened_positions_with_unfavorable_relation_possibility = set()
        main.capture_move_positions = set()

        main.add_position_warnings(Position(3, 3))
        main.add_position_warnings(Position(5, 2))

        pawn_pos = Position(2, 5)
        self.assertIn(pawn_pos, main.threatened_positions_with_neutral_relation_possibility)
        self.assertNotIn(pawn_pos, main.threatened_positions_with_unfavorable_relation_possibility)


if __name__ == "__main__":
    unittest.main()
