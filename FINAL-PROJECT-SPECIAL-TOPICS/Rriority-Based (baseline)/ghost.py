# ghost.py
import pygame
import random
from config import *

class Ghost:
    def __init__(self, ghost_id, color, start_row, start_col, maze):
        self.ghost_id = ghost_id
        self.color = color
        self.start_row = start_row
        self.start_col = start_col
        self.row = start_row
        self.col = start_col
        self.maze = maze
        self.move_timer = 0
        self.is_active = True
        self.direction = (0, 0)
        self._respawn_cooldown = 0

    def get_pixel_coords(self):
        center_x = self.col * CELL_SIZE + CELL_SIZE // 2
        center_y = self.row * CELL_SIZE + CELL_SIZE // 2
        return center_x, center_y

    def decide_next_move(self, agents):
        if self._respawn_cooldown > 0:
            self._respawn_cooldown -= 1
            if self._respawn_cooldown == 0:
                self.is_active = True
            return

        self.move_timer += 1
        if self.move_timer < GHOST_SPEED:
            return
        self.move_timer = 0

        active_agents = [a for a in agents if a.is_active]
        target_pos = None

        if active_agents:
            active_agents.sort(key=lambda a: abs(a.row - self.row) + abs(a.col - self.col))
            nearest_agent = active_agents[0]
            target_pos = (nearest_agent.row, nearest_agent.col)

        valid_moves = []
        possible_directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for dr, dc in possible_directions:
            nr, nc = self.row + dr, self.col + dc
            if not self.maze.is_wall(nr, nc):
                valid_moves.append((dr, dc))

        if not valid_moves:
            return

        best_move = random.choice(valid_moves)

        if target_pos:
            min_dist = float('inf')
            tr, tc = target_pos
            random.shuffle(valid_moves)
            for dr, dc in valid_moves:
                nr, nc = self.row + dr, self.col + dc
                dist = abs(nr - tr) + abs(nc - tc)
                if dist < min_dist:
                    min_dist = dist
                    best_move = (dr, dc)

        self.direction = best_move
        self.row += best_move[0]
        self.col += best_move[1]

    def respawn(self):
        self.row = self.start_row
        self.col = self.start_col
        self.move_timer = 0
        self.is_active = False
        self._respawn_cooldown = 12

    def draw(self, screen):
        center_x = self.col * CELL_SIZE + CELL_SIZE // 2
        center_y = self.row * CELL_SIZE + CELL_SIZE // 2
        radius = CELL_SIZE // 2 - 3

        pygame.draw.circle(screen, self.color, (center_x, center_y), radius)

        eye_offset_x = self.direction[1] * 4
        eye_offset_y = self.direction[0] * 4
        eye_radius = 4
        pygame.draw.circle(screen, (255, 255, 0),
                           (center_x - 6 + eye_offset_x, center_y - 6 + eye_offset_y), eye_radius)
        pygame.draw.circle(screen, (255, 255, 0),
                           (center_x + 6 + eye_offset_x, center_y - 6 + eye_offset_y), eye_radius)