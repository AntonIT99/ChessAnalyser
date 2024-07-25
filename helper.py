import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import pygame

from board import Position


def get_square_size(width, columns):
    return width // columns


def draw_square(col, row, color, screen, square_size):
    pygame.draw.rect(screen, color.value, (col * square_size, row * square_size, square_size, square_size))


# Draw an outline for the specified column/row
def draw_outline_on_square(col, row, color, screen, square_size, columns, rows, rotated):
    if rotated:
        col = columns - 1 - col
        row = rows - 1 - row
    pygame.draw.rect(screen, color.value, (col * square_size, row * square_size, square_size, square_size), int(0.05 * square_size))


# Render a piece by positioning its center
def render_piece_centered(piece, pos_x, pos_y, font, screen):
    render = piece.render(font)
    screen.blit(render, (pos_x - render.get_rect().centerx, pos_y - render.get_rect().centery))


# Render a piece to a specified column/row
def render_piece_on(piece, col, row, font, screen, square_size, columns, rows, rotated):
    if rotated:
        col = columns - 1 - col
        row = rows - 1 - row
    render_piece_centered(piece, col * square_size + square_size / 2, row * square_size + square_size / 2, font, screen)


# returns the column/row under which the mouse cursor is
def get_square_under_mouse(rows, columns, square_size, rotated) -> Position:
    mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
    col, row = [int(v // square_size) for v in mouse_pos]
    if rotated:
        col = columns - 1 - col
        row = rows - 1 - row
    return Position(column=clamp(col, 0, columns - 1), row=clamp(row, 0, rows - 1))


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def process_multithreading(function, for_each_list):
    with ThreadPoolExecutor(max_workers=4*os.cpu_count()) as executor:
        futures = [executor.submit(function, element) for element in for_each_list]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f'Function {function.__name__} generated an exception: {exc}')
