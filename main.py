import os

import pygame
import sys

from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, QUIT, K_BACKSPACE, K_RETURN, K_LSHIFT

from board import Position, Board
from color import Color
from helper import render_piece_on, render_piece_centered, draw_square, get_square_under_mouse, draw_outline_on_square, get_square_size
from piece import Rook, Knight, Bishop, Pawn, Queen, King


def draw_board():
    for pos in board.positions:
        draw_square(pos.column, pos.row, Color.LIGHT_BROWN if (pos.row + pos.column) % 2 == 0 else Color.DARK_BROWN, screen, SQUARE_SIZE)


def draw_pieces(selected_piece_position):
    for pos in board.positions:
        if selected_piece_position is None or pos != selected_piece_position:
            piece = board.get(pos)
            if piece is not None:
                render_piece_on(piece, pos.column, pos.row, font, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)
    if selected_piece_position is not None:
        mouse = pygame.Vector2(pygame.mouse.get_pos())
        selected_piece = board.get(selected_piece_position)
        render_piece_centered(selected_piece, mouse.x, mouse.y, font, screen)


def draw_moves(selected_piece_position):
    safe_moves = set()
    safe_capture_moves = set()
    unsafe_moves = set()
    unsafe_moves_with_relation_possibility = set()
    checkmate_moves = set()
    stalemate_moves = set()
    if selected_piece_position is not None:
        selected_piece = board.get(selected_piece_position)
        for move, is_capture_move in selected_piece.get_moves(board, selected_piece_position):
            checkmate, stalemate = check_checkmate_and_stalemate(selected_piece_position, move)
            if checkmate:
                checkmate_moves.add(move)
            elif stalemate:
                stalemate_moves.add(move)
            elif is_capture_move:
                safe_capture_moves.add(move)
            else:
                safe_moves.add(move)

        for warning, opponent_origin in selected_piece.get_move_warnings(board, selected_piece_position):
            # Simulate the dangerous move
            future_board = board.simulate_future_board(move_origin=selected_piece_position, move_destination=warning)
            # Simulate the opponent capturing the moved piece
            future_board = future_board.simulate_future_board(move_origin=opponent_origin, move_destination=warning)
            opponent_piece = future_board.get(warning)
            # Opponent would be exposed to a retaliation
            if opponent_piece.is_currently_threatened(future_board, warning):
                unsafe_moves_with_relation_possibility.add(warning)
            # Opponent could capture safely
            else:
                unsafe_moves.add(warning)
    for move in safe_moves:
        draw_outline_on_square(move.column, move.row, Color.BLUE, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)
    for move in safe_capture_moves:
        draw_outline_on_square(move.column, move.row, Color.GREEN, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)
    for move in unsafe_moves:
        draw_outline_on_square(move.column, move.row, Color.RED, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)
    for move in unsafe_moves_with_relation_possibility:
        draw_outline_on_square(move.column, move.row, Color.MAGENTA, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)
    for move in checkmate_moves:
        draw_outline_on_square(move.column, move.row, Color.WHITE, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)
    for move in stalemate_moves:
        draw_outline_on_square(move.column, move.row, Color.BLACK, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)


def check_checkmate_and_stalemate(selected_piece_position, move):
    future_board = board.simulate_future_board(move_origin=selected_piece_position, move_destination=move)
    has_legal_king_move = False
    has_other_piece_move = False
    adversary_king_pos = None

    for pos in future_board.positions:
        if isinstance(future_board.get(pos), King) and future_board.get(pos).color != board.get(selected_piece_position).color:
            adversary_king_pos = pos

    if adversary_king_pos is None:
        return False, False

    is_check = future_board.get(adversary_king_pos).is_currently_threatened(future_board, adversary_king_pos)

    if not is_check:
        for pos in future_board.positions:
            if pos != adversary_king_pos and future_board.get(pos) is not None and future_board.get(pos).color != board.get(selected_piece_position).color:
                if len(future_board.get(pos).get_moves(future_board, pos)) > 0:
                    has_other_piece_move = True
                    break

    for king_move, is_capture_move in future_board.get(adversary_king_pos).get_moves(future_board, adversary_king_pos):
        escape_try = future_board.simulate_future_board(move_origin=adversary_king_pos, move_destination=king_move)
        if not escape_try.get(king_move).is_currently_threatened(escape_try, king_move):
            has_legal_king_move = True
            break

    is_checkmate = is_check and not has_legal_king_move
    is_stalemate = not is_check and not has_legal_king_move and not has_other_piece_move
    return is_checkmate, is_stalemate


def draw_position_warnings():
    for pos in board.positions:
        if board.get(pos) is not None:
            for warning in board.get(pos).get_capture_moves(board, pos):
                future_board = board.simulate_future_board(move_origin=pos, move_destination=warning)
                opponent_piece = future_board.get(warning)
                # Opponent would be exposed to a retaliation
                if opponent_piece.is_currently_threatened(future_board, warning):
                    draw_outline_on_square(warning.column, warning.row, Color.YELLOW, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)
                # Opponent could capture safely
                else:
                    draw_outline_on_square(warning.column, warning.row, Color.ORANGE, screen, SQUARE_SIZE, COLUMNS, ROWS, rotated)


def check_promotion(selected_piece_position):
    piece = board.get(selected_piece_position)
    if isinstance(piece, Pawn):
        if (piece.color == Color.BLACK and selected_piece_position.row == PROMOTION_ROW_BLACK) or (piece.color == Color.WHITE and selected_piece_position.row == PROMOTION_ROW_WHITE):
            Pawn.promote(board, selected_piece_position, input("Promotion of a Pawn:\nEnter q for queen, r for rook, b for bishop, k for knight.\n"))


if __name__ == '__main__':
    # Initialize Pygame
    pygame.init()

    # Initialize screen
    WIDTH, HEIGHT = 800, 800
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
    while running:
        draw_board()
        draw_pieces(selected_piece_pos)
        draw_position_warnings()
        draw_moves(selected_piece_pos)

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
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
                elif event.type == pygame.MOUSEBUTTONUP and selected_piece_pos is not None:
                    board.do_move(origin=selected_piece_pos, destination=mouse_pos)
                    check_promotion(mouse_pos)
                    selected_piece_pos = None

        pygame.display.flip()

    # Exit
    pygame.quit()
    sys.exit()
