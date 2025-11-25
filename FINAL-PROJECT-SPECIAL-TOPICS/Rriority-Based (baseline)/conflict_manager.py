# conflict_manager.py
import random
from config import *

class ConflictManager:
    def __init__(self, maze, agents, ghosts, episode_id, log_list):
        self.maze = maze
        self.conflict_count = 0              # post-move conflicts
        self.negotiation_success = 0         # pre-move priority resolutions only
        self.agents = {agent.agent_id: agent for agent in agents}
        self.ghosts = ghosts
        self.is_paused = False
        self.ghost_positions_cache = []
        self.game_result = None

        self.shared_route_locks = {cell: None for cell in self.maze.shared_route_cells}
        self.shared_route_last_unlock = {cell: None for cell in self.maze.shared_route_cells}
        self.lock_conflict_events = 0

        self.time_step = 0
        self.episode_id = episode_id
        self.log_list = log_list

        self.predicted_conflict_events = 0   # number of pre-move predicted conflicts

        # For average loser waiting time (per episode)
        self.total_loser_wait_time = 0.0
        self.total_conflicts_with_wait = 0

    def update_ghost_positions(self):
        self.ghost_positions_cache = [(g.row, g.col) for g in self.ghosts if g.is_active]

    def is_shared_route(self, cell):
        return cell in self.maze.shared_route_cells

    def lock(self, agent, cell):
        if not self.is_shared_route(cell):
            return True
        holder = self.shared_route_locks.get(cell)
        if holder is None or holder == agent.agent_id:
            self.shared_route_locks[cell] = agent.agent_id
            return True
        self.lock_conflict_events += 1
        return False

    def unlock(self, agent, cell):
        if not self.is_shared_route(cell):
            return
        holder = self.shared_route_locks.get(cell)
        if holder == agent.agent_id:
            self.shared_route_locks[cell] = None
            self.shared_route_last_unlock[cell] = agent.agent_id

    # --- Strategy 1: Priority-based pre-move conflicts ---

    def priority_metric(self, agent):
        if PRIORITY_RULE == "highest_score":
            return agent.score
        elif PRIORITY_RULE == "lowest_energy":
            return -agent.energy
        return agent.score

    def handle_priority_conflict(self, agent_a, agent_b, corridor_cell):
        # Called when a pre-move corridor conflict is predicted
        self.predicted_conflict_events += 1

        m_a = self.priority_metric(agent_a)
        m_b = self.priority_metric(agent_b)

        if m_a > m_b:
            winner, loser = agent_a, agent_b
        elif m_b > m_a:
            winner, loser = agent_b, agent_a
        else:
            winner, loser = random.sample([agent_a, agent_b], 2)

        loser.wait_turns_remaining = max(loser.wait_turns_remaining, BASELINE_WAIT_TURNS)
        loser.score = max(0, loser.score - BASELINE_LOSER_PENALTY)

        # Update episode-level wait-time stats
        self.total_loser_wait_time += BASELINE_WAIT_TURNS
        self.total_conflicts_with_wait += 1

        # Count as a successful negotiation (pre-move)
        self.negotiation_success += 1

        # Log this pre-move conflict (one row per event)
        log_entry = {
            "episode": self.episode_id,
            "time_step": self.time_step,
            "strategy": NEGOTIATION_MODE,
            "conflict_type": "pre_move",
            "winner_id": winner.agent_id,
            "loser_id": loser.agent_id,
            "loser_wait_turns": BASELINE_WAIT_TURNS,
            "negotiation_rounds": 1,
            "final_outcome": "success",
            "corridor_row": corridor_cell[0],
            "corridor_col": corridor_cell[1]
        }
        self.log_list.append(log_entry)
        return winner

    def _apply_fallback_rule(self, agent):
        if not agent.is_active:
            return
        agent.score = max(0, agent.score - 3)
        agent.energy -= SHARED_ROUTE_PENALTY // 2
        if agent.energy <= 0:
            agent.energy = 0
            agent.is_active = False

    def resolve_path_conflicts(self, agents):
        target_map = {}
        for agent in agents:
            if not agent.is_active:
                continue
            tr, tc = agent.next_row, agent.next_col
            if (tr, tc) != (agent.row, agent.col):
                target_map.setdefault((tr, tc), []).append(agent)

        final_positions = {agent.agent_id: (agent.row, agent.col) for agent in agents}
        moved_flags = {agent.agent_id: False for agent in agents}

        for cell, contenders in target_map.items():
            ghost_occupied = cell in self.ghost_positions_cache

            if self.is_shared_route(cell):
                current_holder = self.shared_route_locks.get(cell)
                if current_holder is not None and all(a.agent_id != current_holder for a in contenders):
                    for a in contenders:
                        self.lock_conflict_events += 1
                    continue

            if len(contenders) == 1 and not ghost_occupied:
                a = contenders[0]
                if self.is_shared_route(cell):
                    if not self.lock(a, cell):
                        continue
                final_positions[a.agent_id] = cell
                moved_flags[a.agent_id] = True
                continue

            # --- POST-MOVE CONFLICT ---
            self.conflict_count += 1

            if ghost_occupied:
                continue

            def priority(a):
                return a.score - (a.energy / MAX_ENERGY) * 0.5

            contenders_sorted = sorted(contenders, key=lambda a: priority(a))
            winner = contenders_sorted[0]

            if len(contenders_sorted) > 1 and abs(priority(contenders_sorted[0]) - priority(contenders_sorted[1])) < 0.15:
                if random.random() < 0.25:
                    winner = contenders_sorted[1]

            if self.is_shared_route(cell):
                if not self.lock(winner, cell):
                    continue

            # Note: post-move resolutions are NOT counted as "negotiation_success"
            final_positions[winner.agent_id] = cell
            moved_flags[winner.agent_id] = True
            winner.conflict_wins += 1

            equal_priorities = all(abs(priority(a) - priority(contenders_sorted[0])) < 1e-6 for a in contenders)
            if equal_priorities:
                if random.random() > LOTTERY_FAIL_CHANCE:
                    chosen = random.choice(contenders)
                    final_positions[chosen.agent_id] = cell
                    moved_flags[chosen.agent_id] = True
                    chosen.conflict_wins += 1
                else:
                    for a in contenders:
                        self._apply_fallback_rule(a)

        for agent in agents:
            if not agent.is_active:
                continue

            old_row, old_col = agent.row, agent.col
            fr, fc = final_positions[agent.agent_id]
            moved = moved_flags[agent.agent_id]

            if moved and self.is_shared_route((old_row, old_col)) and (old_row, old_col) != (fr, fc):
                self.unlock(agent, (old_row, old_col))

            agent.commit_final_position(fr, fc, moved)

    def check_ghost_collisions(self, agents):
        """On collision: apply penalties and respawn agent at its original start position."""
        for agent in agents:
            if not agent.is_active:
                continue
            for ghost in self.ghosts:
                if not ghost.is_active:
                    continue
                if (agent.row, agent.col) == (ghost.row, ghost.col):
                    print(f"[!!!] AGENT {agent.agent_id} CAUGHT BY GHOST {ghost.ghost_id}!")

                    # Penalties
                    agent.energy -= GHOST_CATCH_PENALTY
                    agent.score = max(0, agent.score - 5)

                    # Unlock corridor cell if collision happened there
                    if self.is_shared_route((agent.row, agent.col)):
                        self.unlock(agent, (agent.row, agent.col))

                    # Respawn agent at original start position
                    agent.row = agent.start_row
                    agent.col = agent.start_col
                    agent.next_row = agent.start_row
                    agent.next_col = agent.start_col
                    agent.path = []
                    agent.wait_turns_remaining = 0
                    agent.state = "ACTIVE"

                    if agent.energy <= 0:
                        agent.energy = 0
                        agent.is_active = True

                    ghost.respawn()