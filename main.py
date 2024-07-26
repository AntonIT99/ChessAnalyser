import argparse
import concurrent
import os
import sys

import pygame
from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, QUIT, K_BACKSPACE, K_RETURN, K_LSHIFT, MOUSEBUTTONUP

from board import Board
from color import Color
from helper import render_piece_on, render_piece_centered, draw_square, get_square_under_mouse, draw_outline_on_square, get_square_size, do_foreach_multithreaded
from piece import Rook, Knight, Bishop, Pawn, Queen, King, en_passant
from position import Position


def draw_board():
    for pos in board.positions:
        draw_square(pos.column, pos.row, Color.LIGHT_BROWN if (pos.row + pos.column) % 2 == 0 else Color.DARK_BROWN, screen, SQUARE_SIZE)


def draw_pieces():
    for pos in board.positions:
        if selected_piece_pos is None or pos != selected_piece_pos:
            piece = board.get(pos)
            if piece is not None:
                render_piece_on(piece, pos.column, pos.row, font, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)
    if selected_piece_pos is not None:
        mouse = pygame.Vector2(pygame.mouse.get_pos())
        selected_piece = board.get(selected_piece_pos)
        render_piece_centered(selected_piece, mouse.x, mouse.y, font, screen)


def calculate_moves():
    safe_moves.clear()
    recommended_moves.clear()
    safe_capture_moves.clear()
    unsafe_moves.clear()
    unsafe_moves_with_relation_possibility.clear()
    checkmate_moves.clear()
    stalemate_moves.clear()

    if selected_piece_pos is not None:
        # use a deep copy of the selected position since it can be changed by the main thread
        selected_piece_position = Position.copy(selected_piece_pos)
        selected_piece = board.get(selected_piece_position)
        selected_piece_moves = selected_piece.get_moves(board, selected_piece_position)
        selected_piece_unsafe_moves = selected_piece.get_unsafe_moves(board, selected_piece_position)

        for move, is_capture_move in selected_piece_moves:
            checkmate, stalemate = check_checkmate_and_stalemate(selected_piece_position, move)
            if checkmate:
                checkmate_moves.add(move)
            elif stalemate:
                stalemate_moves.add(move)
            elif is_capture_move:
                safe_capture_moves.add(move)
            elif move not in [unsafe_move for unsafe_move, opponent_origin in selected_piece_unsafe_moves]:
                if is_recommended_move(board, selected_piece_position, move):
                    recommended_moves.add(move)
                else:
                    safe_moves.add(move)

        # Unsafe moves are forbidden for Kings
        if not isinstance(selected_piece, King):
            for unsafe_move, opponent_origin in selected_piece_unsafe_moves:
                # Simulate the dangerous move
                future_board = board.simulate_future_board(move_origin=selected_piece_position, move_destination=unsafe_move)
                # Simulate the opponent capturing the moved piece
                future_board = future_board.simulate_future_board(move_origin=opponent_origin, move_destination=unsafe_move)
                opponent_piece = future_board.get(unsafe_move)
                # Opponent would be exposed to a retaliation
                if opponent_piece.is_currently_threatened(future_board, unsafe_move):
                    unsafe_moves_with_relation_possibility.add(unsafe_move)
                # Opponent could capture safely
                else:
                    unsafe_moves.add(unsafe_move)

    do_foreach_multithreaded(add_interesting_moves, [pos for pos in board.positions if board.get(pos) is not None])


def calculate_positions():
    threatened_positions.clear()
    threatened_positions_with_favorable_relation_possibility.clear()
    threatened_positions_with_neutral_relation_possibility.clear()
    threatened_positions_with_unfavorable_relation_possibility.clear()
    do_foreach_multithreaded(add_position_warnings, [pos for pos in board.positions if board.get(pos) is not None])


def add_position_warnings(pos):
    def process_capture_move(capture_move):
        is_en_passant, captured_piece_position = en_passant(board, pos, capture_move)
        warning = captured_piece_position if is_en_passant else capture_move
        if capture_move_has_retaliation_possibility(board, pos, capture_move):
            white_threatened_value, black_threatened_value = calculate_retaliation(warning, board)
            if board.get(warning) is not None:
                color_defender = board.get(warning).color
                if (color_defender == Color.WHITE and white_threatened_value < black_threatened_value) or (color_defender == Color.BLACK and black_threatened_value <= white_threatened_value):
                    threatened_positions_with_favorable_relation_possibility.add(warning)
                elif (color_defender == Color.WHITE and white_threatened_value > black_threatened_value) or (color_defender == Color.BLACK and black_threatened_value > white_threatened_value):
                    threatened_positions_with_unfavorable_relation_possibility.add(warning)
                elif (color_defender == Color.WHITE and white_threatened_value == black_threatened_value) or (color_defender == Color.BLACK and black_threatened_value == white_threatened_value):
                    threatened_positions_with_neutral_relation_possibility.add(warning)
        else:
            threatened_positions.add(warning)

    piece = board.get(pos)
    if piece is not None:
        do_foreach_multithreaded(process_capture_move, piece.get_capture_moves(board, pos))


def add_interesting_moves(pos):
    def process_interesting_move(move):
        checkmate, stalemate = check_checkmate_and_stalemate(pos, move)
        if checkmate:
            checkmate_moves.add(pos)
        elif stalemate:
            stalemate_moves.add(pos)

    piece = board.get(pos)
    if piece is not None and not selected_piece_pos:
        # Show which pieces can do interesting moves, if no piece is selected
        do_foreach_multithreaded(process_interesting_move, [move for move, capture_move in piece.get_moves(board, pos)])


def calculate_retaliation(pos, current_board, lost_pieces_value_white=0, lost_pieces_value_black=0):
    threatened_piece = current_board.get(pos)
    if threatened_piece is not None:
        threats = threatened_piece.get_threats_positions(current_board, pos)
        if len(threats) > 0:
            if threatened_piece.color == Color.WHITE:
                lost_pieces_value_white += threatened_piece.value
            else:
                lost_pieces_value_black += threatened_piece.value
        for threat_pos in threats:
            future_board = current_board.simulate_future_board(move_origin=threat_pos, move_destination=pos)
            lost_pieces_value_white, lost_pieces_value_black = calculate_retaliation(pos, future_board, lost_pieces_value_white, lost_pieces_value_black)
        return lost_pieces_value_white, lost_pieces_value_black
    return 0, 0


def capture_move_has_retaliation_possibility(current_board, pos, capture_move):
    future_board = current_board.simulate_future_board(move_origin=pos, move_destination=capture_move)
    captured_piece = current_board.get(capture_move)
    opponent_piece = future_board.get(capture_move)
    # Opponent would be exposed to a retaliation only if the captured piece is not a King otherwise it ends there
    return not isinstance(captured_piece, King) and opponent_piece.is_currently_threatened(future_board, capture_move)


def is_recommended_move(current_board, pos, safe_move):
    future_board = current_board.simulate_future_board(move_origin=pos, move_destination=safe_move)
    future_piece = future_board.get(safe_move)
    if future_piece is not None:
        for capture_move in future_piece.get_capture_moves(future_board, safe_move):
            if not capture_move_has_retaliation_possibility(future_board, safe_move, capture_move):
                return True
    return False


def draw_positions_and_moves():
    for warning in threatened_positions:
        draw_outline_on_square(warning.column, warning.row, Color.ORANGE, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)
    for warning in threatened_positions_with_favorable_relation_possibility:
        draw_outline_on_square(warning.column, warning.row, Color.GREEN_YELLOW, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)
    for warning in threatened_positions_with_neutral_relation_possibility:
        draw_outline_on_square(warning.column, warning.row, Color.YELLOW, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)
    for warning in threatened_positions_with_unfavorable_relation_possibility:
        draw_outline_on_square(warning.column, warning.row, Color.ORANGE_YELLOW, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)

    for move in safe_moves:
        draw_outline_on_square(move.column, move.row, Color.BLUE, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)
    for move in recommended_moves:
        draw_outline_on_square(move.column, move.row, Color.CYAN, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)
    for move in safe_capture_moves:
        draw_outline_on_square(move.column, move.row, Color.GREEN, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)
    for move in unsafe_moves:
        draw_outline_on_square(move.column, move.row, Color.RED, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)
    for move in unsafe_moves_with_relation_possibility:
        draw_outline_on_square(move.column, move.row, Color.MAGENTA, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)
    for move in stalemate_moves:
        draw_outline_on_square(move.column, move.row, Color.BLACK, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)
    for move in checkmate_moves:
        draw_outline_on_square(move.column, move.row, Color.WHITE, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)


def check_checkmate_and_stalemate(position, move):
    future_board = board.simulate_future_board(move_origin=position, move_destination=move)
    has_legal_move = False
    adversary_king_pos = None
    is_check = False

    for pos in future_board.positions:
        if isinstance(future_board.get(pos), King) and board.get(position) is not None and future_board.get(pos).color != board.get(position).color:
            adversary_king_pos = pos

    if adversary_king_pos is None:
        return False, False

    if future_board.get(adversary_king_pos) is not None:
        is_check = future_board.get(adversary_king_pos).is_currently_threatened(future_board, adversary_king_pos)

    for pos in future_board.positions:
        if future_board.get(pos) is not None and board.get(position) is not None and future_board.get(pos).color != board.get(position).color:
            if len(future_board.get(pos).get_moves(future_board, pos)) > 0:
                has_legal_move = True
                break

    is_checkmate = is_check and not has_legal_move
    is_stalemate = not is_check and not has_legal_move
    return is_checkmate, is_stalemate


def check_promotion(new_position):
    piece = board.get(new_position)
    if isinstance(piece, Pawn):
        if (piece.color == Color.BLACK and new_position.row == PROMOTION_ROW_BLACK) or (piece.color == Color.WHITE and new_position.row == PROMOTION_ROW_WHITE):
            Pawn.promote(board, new_position, input("Promotion of a Pawn:\nEnter q for queen, r for rook, b for bishop, k for knight.\n"))


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-res', '--resolution', type=int,
                        help='Set the resolution WIDTH/HEIGHT e.g. -res 1000')
    args = parser.parse_args()

    # Initialize Pygame
    pygame.init()

    # Initialize screen
    WIDTH, HEIGHT = 800, 800
    if args.resolution:
        WIDTH, HEIGHT = int(args.resolution), int(args.resolution)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Chess')

    # Initialize Board
    ROWS, COLUMNS = 8, 8
    SQUARE_SIZE = get_square_size(WIDTH, COLUMNS)
    PROMOTION_ROW_WHITE = 0
    PROMOTION_ROW_BLACK = ROWS - 1
    INIT_BOARD = [
        [Rook(Color.BLACK), Knight(Color.BLACK), Bishop(Color.BLACK), Queen(Color.BLACK), King(Color.BLACK), Bishop(Color.BLACK), Knight(Color.BLACK), Rook(Color.BLACK)],
        [Pawn(Color.BLACK)] * COLUMNS,
        [None] * COLUMNS,
        [None] * COLUMNS,
        [None] * COLUMNS,
        [None] * COLUMNS,
        [Pawn(Color.WHITE)] * COLUMNS,
        [Rook(Color.WHITE), Knight(Color.WHITE), Bishop(Color.WHITE), Queen(Color.WHITE), King(Color.WHITE), Bishop(Color.WHITE), Knight(Color.WHITE), Rook(Color.WHITE)]
    ]
    board = Board(INIT_BOARD)

    # Font
    font = pygame.font.Font(os.path.join("assets", "fonts", "seguisym.ttf"), int(0.75 * SQUARE_SIZE))

    # Main loop
    selected_piece_pos = None
    rotated = False
    running = True
    future_calc_positions = None
    future_calc_moves = None
    has_moved = False

    threatened_positions = set()
    threatened_positions_with_favorable_relation_possibility = set()
    threatened_positions_with_neutral_relation_possibility = set()
    threatened_positions_with_unfavorable_relation_possibility = set()
    safe_moves = set()
    recommended_moves = set()
    safe_capture_moves = set()
    unsafe_moves = set()
    unsafe_moves_with_relation_possibility = set()
    checkmate_moves = set()
    stalemate_moves = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        while running:

            draw_board()
            draw_pieces()
            draw_positions_and_moves()

            for event in pygame.event.get():

                if event.type == QUIT:
                    running = False
                # Key events
                elif event.type == KEYDOWN:
                    if event.key == K_BACKSPACE:
                        board.undo()
                    elif event.key == K_RETURN:
                        board.redo()
                    elif event.key == K_LSHIFT:
                        rotated = not rotated
                # Mouse events
                else:
                    mouse_pos = get_square_under_mouse(board.rows, board.columns, SQUARE_SIZE, rotated)
                    if event.type == MOUSEBUTTONDOWN and board.get(mouse_pos) is not None:
                        selected_piece_pos = Position.copy(mouse_pos)
                    elif event.type == MOUSEBUTTONUP and selected_piece_pos is not None:
                        has_moved = selected_piece_pos != mouse_pos
                        if has_moved:
                            board.do_move(origin=selected_piece_pos, destination=mouse_pos)
                            check_promotion(mouse_pos)
                        selected_piece_pos = None

                # For key press event and mouse button events -> recalculate moves
                if event.type == KEYDOWN or event.type == MOUSEBUTTONUP or event.type == MOUSEBUTTONDOWN:
                    if future_calc_moves is not None:
                        future_calc_moves.result()
                    future_calc_moves = executor.submit(calculate_moves)

                # For key press event and mouse button release events with an actual move -> recalculate positions
                if event.type == KEYDOWN or (event.type == MOUSEBUTTONUP and has_moved):
                    if future_calc_positions is not None:
                        future_calc_positions.result()
                    future_calc_positions = executor.submit(calculate_positions)

            pygame.display.flip()

    # Exit
    pygame.quit()
    sys.exit()
