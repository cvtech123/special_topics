# agent.py
import pygame
import random
from collections import deque
from config import *

class Agent:
    def __init__(self, agent_id, color, start_row, start_col, maze, manager):
        self.agent_id = agent_id
        self.color = color
        self.maze = maze
        self.manager = manager

        # Store start position for respawn
        self.start_row = start_row
        self.start_col = start_col

        self.row = start_row
        self.col = start_col
        self.next_row = start_row
        self.next_col = start_col
        self.score = 0
        self.energy = MAX_ENERGY
        self.is_active = True
        self.state = 'ACTIVE'
        self.move_timer = 0
        self.steps_since_energy_loss = 0
        self.path = []
        self.waiting_ticks = 0
        self.total_move_attempts = 0
        self.conflict_wins = 0
        self.attempted_move = False
        self.last_path_time = 0
        self.path_ttl_ms = 700
        self.max_bfs_depth = 200
        self.blocked_retry_threshold = 3
        self.consecutive_blocks = 0

        self.wait_turns_remaining = 0

    def get_pixel_coords(self):
        center_x = self.col * CELL_SIZE + CELL_SIZE // 2
        center_y = self.row * CELL_SIZE + CELL_SIZE // 2
        return center_x, center_y

    def is_cell_dangerous(self, row, col):
        for gr, gc in self.manager.ghost_positions_cache:
            distance = abs(row - gr) + abs(col - gc)
            if distance <= GHOST_AVOIDANCE_RADIUS:
                return True
        return False

    def predict_next_move(self, look_ahead=LOOKAHEAD_STEPS):
        if not self.path:
            return None
        steps = min(look_ahead, len(self.path))
        for i in range(steps):
            cell = self.path[i]
            if cell in self.maze.shared_route_cells:
                return cell, i + 1
        return None

    def detect_potential_conflict(self, look_ahead=LOOKAHEAD_STEPS, sensing_radius=SENSING_RADIUS):
        if not self.is_active:
            return None

        my_prediction = self.predict_next_move(look_ahead)
        if my_prediction is None:
            return None
        my_corridor_cell, _ = my_prediction

        for other in self.manager.agents.values():
            if other.agent_id <= self.agent_id or not other.is_active:
                continue

            dist = abs(other.row - self.row) + abs(other.col - self.col)
            if dist > sensing_radius:
                continue

            if (other.row, other.col) == my_corridor_cell:
                return other, my_corridor_cell

            other_pred = other.predict_next_move(look_ahead)
            if other_pred is not None:
                other_corridor_cell, _ = other_pred
                if other_corridor_cell == my_corridor_cell:
                    return other, my_corridor_cell

        return None

    def bfs_find_path(self):
        start_pos = (self.row, self.col)
        queue = deque([(start_pos, [])])
        visited = {start_pos}
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        random.shuffle(directions)
        available_pellets = self.maze.pellets
        depth = 0

        while queue and depth < self.max_bfs_depth:
            current, path = queue.popleft()
            r, c = current
            if current in available_pellets and current != start_pos:
                return path
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.maze.rows and 0 <= nc < self.maze.cols:
                    if (not self.maze.is_wall(nr, nc) and
                            (nr, nc) not in visited and
                            not self.is_cell_dangerous(nr, nc)):
                        visited.add((nr, nc))
                        new_path = list(path)
                        new_path.append((nr, nc))
                        queue.append(((nr, nc), new_path))
            depth += 1
        return []

    def decide_next_move(self):
        if self.wait_turns_remaining > 0:
            self.state = 'WAIT'
            self.wait_turns_remaining -= 1
            self.next_row, self.next_col = self.row, self.col
            self.attempted_move = False
            self.waiting_ticks += 1
            return

        if not self.is_active:
            self.state = 'DROPPED_OUT'
            self.next_row, self.next_col = self.row, self.col
            self.attempted_move = False
            return

        if (self.row, self.col) in self.maze.pellets:
            self.score += PELLET_POINT
            self.maze.pellets.remove((self.row, self.col))
            self.energy = min(MAX_ENERGY, self.energy + 2)
            self.path = []

        self.move_timer += 1
        if self.move_timer < AGENT_SPEED:
            self.next_row, self.next_col = self.row, self.col
            self.attempted_move = False
            return
        self.move_timer = 0

        self.state = 'ACTIVE'

        if self.path:
            next_step = self.path[0]
            if self.is_cell_dangerous(next_step[0], next_step[1]):
                self.path = []

        curr_time = pygame.time.get_ticks()
        recalc_needed = False
        if not self.path:
            recalc_needed = True
        elif (self.path and self.path[-1] not in self.maze.pellets):
            recalc_needed = True
        elif curr_time - self.last_path_time > self.path_ttl_ms:
            recalc_needed = True

        if recalc_needed:
            new_path = self.bfs_find_path()
            self.last_path_time = curr_time
            if new_path:
                self.path = new_path

        # Pre-move detection: priority baseline negotiation
        potential = self.detect_potential_conflict()
        if potential is not None:
            other_agent, corridor_cell = potential
            winner = self.manager.handle_priority_conflict(self, other_agent, corridor_cell)
            if winner is not self:
                self.state = 'WAIT'
                self.next_row, self.next_col = self.row, self.col
                self.attempted_move = False
                return

        if self.path:
            self.next_row, self.next_col = self.path[0]
        else:
            self.next_row, self.next_col = self.row, self.col

        if (self.next_row, self.next_col) == (self.row, self.col):
            possible_moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            random.shuffle(possible_moves)
            self.next_row, self.next_col = self.row, self.col
            for dr, dc in possible_moves:
                nr, nc = self.row + dr, self.col + dc
                if not self.maze.is_wall(nr, nc) and not self.is_cell_dangerous(nr, nc):
                    self.next_row, self.next_col = nr, nc
                    self.state = 'WANDERING'
                    break
            if (self.next_row, self.next_col) == (self.row, self.col):
                self.state = 'IDLE'

        if (self.next_row, self.next_col) != (self.row, self.col):
            self.attempted_move = True
            self.total_move_attempts += 1
            self.energy -= ENERGY_LOSS_PER_MOVE * 0.1
            if self.energy <= 0:
                self.energy = 0
                self.is_active = False
        else:
            self.attempted_move = False

    def commit_final_position(self, new_row, new_col, moved):
        if not self.is_active:
            return
        self.row, self.col = new_row, new_col
        if moved:
            if self.path and (self.row, self.col) == self.path[0]:
                self.path.pop(0)
            self.energy -= ENERGY_LOSS_PER_MOVE
            if self.energy <= 0:
                self.energy = 0
                self.is_active = False
            self.consecutive_blocks = 0

    def draw(self, screen):
        center_x = self.col * CELL_SIZE + CELL_SIZE // 2
        center_y = self.row * CELL_SIZE + CELL_SIZE // 2
        radius = CELL_SIZE // 2 - 3
        draw_color = self.color
        if self.state == 'DROPPED_OUT' or not self.is_active:
            draw_color = (50, 50, 50)
        elif self.state == 'WAIT':
            draw_color = (self.color[0] // 2, self.color[1] // 2, self.color[2] // 2)
        elif self.is_active:
            pulse = int((pygame.time.get_ticks() % 500) / 500 * 50)
            c0, c1, c2 = self.color
            draw_color = (min(255, c0 + pulse),
                          min(255, c1 + pulse),
                          min(255, c2 + pulse))
        pygame.draw.circle(screen, draw_color, (center_x, center_y), radius)