import unittest

from board import Board
from color import Color
import main
from piece import Bishop, King, Knight, Pawn, Rook
from position import Position


def build_en_passant_check_board():
    state = [[None for _ in range(8)] for _ in range(8)]
    state[2][5] = Rook(Color.WHITE)
    state[3][6] = Bishop(Color.BLACK)
    state[3][7] = King(Color.BLACK)
    state[4][4] = King(Color.WHITE)
    state[4][5] = Pawn(Color.BLACK)
    state[4][7] = Pawn(Color.BLACK)
    state[5][5] = Pawn(Color.WHITE)
    state[6][6] = Pawn(Color.WHITE)
    state[6][7] = Pawn(Color.WHITE)
    state[7][4] = Knight(Color.BLACK)
    return Board(state)


class EnPassantTest(unittest.TestCase):
    def test_en_passant_response_prevents_false_checkmate(self):
        board = build_en_passant_check_board()
        main.board = board

        self.assertEqual(
            (False, False),
            main.check_checkmate_and_stalemate(Position(6, 6), Position(4, 6)),
        )

    def test_simulated_en_passant_keeps_last_move_history(self):
        board = build_en_passant_check_board()
        future_board = board.simulate_future_board(Position(6, 6), Position(4, 6))

        self.assertIn(
            (Position(5, 6), True),
            future_board.get(Position(4, 7)).get_moves(future_board, Position(4, 7)),
        )

    def test_black_pawn_can_en_passant_to_the_right(self):
        board = build_en_passant_check_board()
        future_board = board.simulate_future_board(Position(6, 6), Position(4, 6))

        self.assertIn(
            (Position(5, 6), True),
            future_board.get(Position(4, 5)).get_moves(future_board, Position(4, 5)),
        )

    def test_en_passant_requires_adjacent_square_to_have_been_empty_before_last_move(self):
        state = [[None for _ in range(8)] for _ in range(8)]
        state[0][0] = King(Color.BLACK)
        state[7][7] = King(Color.WHITE)
        state[4][5] = Pawn(Color.BLACK)
        state[4][6] = Pawn(Color.WHITE)

        previous_state = [[None for _ in range(8)] for _ in range(8)]
        previous_state[0][0] = King(Color.BLACK)
        previous_state[7][7] = King(Color.WHITE)
        previous_state[4][5] = Pawn(Color.BLACK)
        previous_state[4][6] = Pawn(Color.WHITE)
        previous_state[6][6] = Pawn(Color.WHITE)

        board = Board(state)
        board.undo_stack = [previous_state]

        self.assertNotIn(
            (Position(5, 6), True),
            board.get(Position(4, 5)).get_moves(board, Position(4, 5)),
        )


if __name__ == "__main__":
    unittest.main()
