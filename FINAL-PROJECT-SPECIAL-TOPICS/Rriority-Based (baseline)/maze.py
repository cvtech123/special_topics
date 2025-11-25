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
        for row_idx, row in enumerate(MAZE_LAYOUT):
            for col_idx, cell in enumerate(row):
                rect = pygame.Rect(
                    col_idx * CELL_SIZE, row_idx * CELL_SIZE,
                    CELL_SIZE, CELL_SIZE
                )
                if cell == "#":
                    self.walls.append(rect)
                elif cell == ".":
                    all_walkable.append((row_idx, col_idx))
                elif cell == "C":
                    all_walkable.append((row_idx, col_idx))
                    self.corridors[(row_idx, col_idx)] = rect
                    self.shared_route_cells.add((row_idx, col_idx))

        available_pellet_spots = set(all_walkable)
        FIXED_EXCLUSIONS = set(START_POSITIONS + GHOST_START_POSITIONS)
        CUSTOM_EXCLUSIONS = set([
            (1, 29), (17, 15)
        ]).union(RED_LINE_EXCLUSION)
        all_exclusions = FIXED_EXCLUSIONS.union(CUSTOM_EXCLUSIONS)
        for pos in all_exclusions:
            if pos in available_pellet_spots:
                available_pellet_spots.remove(pos)
        num_pellets_to_place = max(0, int(len(available_pellet_spots) * PELLET_SPAWN_RATIO))
        if num_pellets_to_place > len(available_pellet_spots):
            num_pellets_to_place = len(available_pellet_spots)
        self.pellets = set(random.sample(list(available_pellet_spots), num_pellets_to_place)) if num_pellets_to_place else set()

    def is_wall(self, row, col):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            cell = self.layout[row][col]
            return cell == "#"
        return True

    def draw_maze(self, manager=None):
        for (r, c), rect in self.corridors.items():
            color = CORRIDOR_FLOOR_COLOR
            if manager is not None:
                lock_owner = manager.shared_route_locks.get((r, c), None)
                if lock_owner is None:
                    color = (0, 180, 0)
                else:
                    color = (200, 40, 40)
            pygame.draw.rect(self.screen, color, rect)

        for wall in self.walls:
            pygame.draw.rect(self.screen, WALL_COLOR, wall)

        for r, c in self.pellets:
            center_x = c * CELL_SIZE + CELL_SIZE // 2
            center_y = r * CELL_SIZE + CELL_SIZE // 2
            pygame.draw.circle(self.screen, (255, 255, 255), (center_x, center_y), 4)