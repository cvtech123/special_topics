# maze.py
import pygame
import random
from config import *

class Maze:
    def __init__(self, screen):
        self.screen = screen
        self.walls = []
        self.corridors = {}
        self.layout = MAZE_LAYOUT
        self.rows = len(MAZE_LAYOUT)
        self.cols = len(MAZE_LAYOUT[0])
        self.shared_route_cells = set()

        all_walkable = []
        for r_idx, row in enumerate(MAZE_LAYOUT):
            for c_idx, cell in enumerate(row):
                rect = pygame.Rect(c_idx * CELL_SIZE, r_idx * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                if cell == "#":
                    self.walls.append(rect)
                elif cell == ".":
                    all_walkable.append((r_idx, c_idx))
                elif cell == "C":
                    all_walkable.append((r_idx, c_idx))
                    self.corridors[(r_idx, c_idx)] = rect
                    self.shared_route_cells.add((r_idx, c_idx))

        available = set(all_walkable)
        FIXED_EXCLUSIONS = set(START_POSITIONS + GHOST_START_POSITIONS)
        CUSTOM_EXCLUSIONS = set([(1, 29), (17, 15)]).union(RED_LINE_EXCLUSION)
        for pos in FIXED_EXCLUSIONS.union(CUSTOM_EXCLUSIONS):
            if pos in available:
                available.remove(pos)
        n_pellets = max(0, int(len(available) * PELLET_SPAWN_RATIO))
        if n_pellets > len(available):
            n_pellets = len(available)
        self.pellets = set(random.sample(list(available), n_pellets)) if n_pellets else set()

    def is_wall(self, row, col):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.layout[row][col] == "#"
        return True

    def draw_maze(self, manager=None):
        for (r, c), rect in self.corridors.items():
            if manager is None:
                color = CORRIDOR_FLOOR_COLOR
            else:
                lock_owner = manager.shared_route_locks.get((r, c), None)
                color = (0, 180, 0) if lock_owner is None else (200, 40, 40)
            pygame.draw.rect(self.screen, color, rect)
        for wall in self.walls:
            pygame.draw.rect(self.screen, WALL_COLOR, wall)
        for r, c in self.pellets:
            cx = c * CELL_SIZE + CELL_SIZE // 2
            cy = r * CELL_SIZE + CELL_SIZE // 2
            pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), 4)