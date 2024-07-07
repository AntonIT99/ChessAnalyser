import os

import pygame
import sys

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
                render_piece_on(piece, pos.column, pos.row, font, screen, SQUARE_SIZE)
    if selected_piece_position is not None:
        mouse = pygame.Vector2(pygame.mouse.get_pos())
        selected_piece = board.get(selected_piece_position)
        render_piece_centered(selected_piece, mouse.x, mouse.y, font, screen)


def draw_moves(selected_piece_position):
    if selected_piece_position is not None:
        selected_piece = board.get(selected_piece_position)
        for move, capture_move in selected_piece.get_moves(board, selected_piece_position):
            if capture_move:
                draw_outline_on_square(move.column, move.row, Color.GREEN, screen, SQUARE_SIZE)
            else:
                draw_outline_on_square(move.column, move.row, Color.BLUE, screen, SQUARE_SIZE)


def draw_move_warnings(selected_piece_position):
    if selected_piece_position is not None:
        selected_piece = board.get(selected_piece_position)
        for warning_pos in selected_piece.get_move_warnings(board, selected_piece_position):
            draw_outline_on_square(warning_pos.column, warning_pos.row, Color.RED, screen, SQUARE_SIZE)


def draw_position_warnings():
    for pos in board.positions:
        if board.get(pos) is not None:
            for capture_move_pos in board.get(pos).get_capture_moves(board, pos):
                draw_outline_on_square(capture_move_pos.column, capture_move_pos.row, Color.ORANGE, screen, SQUARE_SIZE)


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
    INIT_BOARD = [
        [Rook(Color.WHITE), Knight(Color.WHITE), Bishop(Color.WHITE), Queen(Color.WHITE), King(Color.WHITE), Bishop(Color.WHITE), Knight(Color.WHITE), Rook(Color.WHITE)],
        [Pawn(Color.WHITE)] * COLUMNS,
        [None] * COLUMNS,
        [None] * COLUMNS,
        [None] * COLUMNS,
        [None] * COLUMNS,
        [Pawn(Color.BLACK)] * COLUMNS,
        [Rook(Color.BLACK), Knight(Color.BLACK), Bishop(Color.BLACK), Queen(Color.BLACK), King(Color.BLACK), Bishop(Color.BLACK), Knight(Color.BLACK), Rook(Color.BLACK)]
    ]
    board = Board(INIT_BOARD)

    # Font
    font = pygame.font.Font(os.path.join("assets", "fonts", "seguisym.ttf"), int(0.75 * SQUARE_SIZE))

    # Main loop
    selected_piece_pos = None
    running = True
    while running:
        draw_board()
        draw_pieces(selected_piece_pos)
        draw_position_warnings()
        draw_moves(selected_piece_pos)
        draw_move_warnings(selected_piece_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                mouse_pos = get_square_under_mouse(board.rows, board.columns, SQUARE_SIZE)
                if event.type == pygame.MOUSEBUTTONDOWN and board.get(mouse_pos) is not None:
                    selected_piece_pos = Position.copy(mouse_pos)
                elif event.type == pygame.MOUSEBUTTONUP and selected_piece_pos is not None:
                    # if the origin of the move is not the same as the destination
                    if mouse_pos != selected_piece_pos:
                        # if the destination is not occupied or is occupied by a piece of the opposite color
                        if board.get(mouse_pos) is None or board.get(selected_piece_pos).color != board.get(mouse_pos).color:
                            board.do_move(origin=selected_piece_pos, destination=mouse_pos)
                    selected_piece_pos = None

        pygame.display.flip()

    # Exit
    pygame.quit()
    sys.exit()
