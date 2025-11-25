# conflict_manager.py
import random
from config import *

class ConflictManager:
    def __init__(self, maze, agents, ghosts, episode_id, log_list):
        self.maze = maze
        self.conflict_count = 0              # post-move cell conflicts
        self.negotiation_success = 0         # number of successful negotiations (ACCEPT)
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

        self.predicted_conflict_events = 0   # how many negotiations were started

        # Active negotiation sessions: key = (min_id, max_id, corridor_cell)
        self.negotiations = {}

        # Episode-level wait stats (for avg loser waiting time)
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

    # ---- Alternating Offers Negotiation ----

    def _priority_for_proposer(self, agent):
        # Lower score => proposer (the "weaker" agent starts)
        return agent.score

    def start_negotiation(self, agent_a, agent_b, corridor_cell):
        """Create a negotiation session if one doesn't already exist."""
        if agent_a.in_conflict or agent_b.in_conflict:
            return

        key = (min(agent_a.agent_id, agent_b.agent_id),
               max(agent_a.agent_id, agent_b.agent_id),
               corridor_cell)
        if key in self.negotiations:
            return

        self.predicted_conflict_events += 1

        # Decide initial proposer: lower priority (lower score) starts
        if self._priority_for_proposer(agent_a) <= self._priority_for_proposer(agent_b):
            proposer_id = agent_a.agent_id
            respondent_id = agent_b.agent_id
        else:
            proposer_id = agent_b.agent_id
            respondent_id = agent_a.agent_id

        session = {
            "agents": (agent_a.agent_id, agent_b.agent_id),
            "corridor": corridor_cell,
            "round": 0,
            "proposer_id": proposer_id,
            "respondent_id": respondent_id,
            "messages": [],        # list of dicts (sender, receiver, performative, content)
        }
        self.negotiations[key] = session

        # Put both agents into NEGOTIATING state
        for ag in (agent_a, agent_b):
            ag.in_conflict = True
            ag.conflict_partner_id = (agent_b.agent_id if ag is agent_a else agent_a.agent_id)
            ag.conflict_corridor = corridor_cell
            ag.state = "NEGOTIATING"

    def _utility_wait(self, agent, wait_turns):
        """Simple utility: higher is better. More waiting = lower utility."""
        return -(wait_turns + 0.1 * agent.score)

    def process_negotiations(self):
        """Run at most one round per active negotiation per time step."""
        to_remove = []

        for key, sess in list(self.negotiations.items()):
            a_id, b_id = sess["agents"]
            corridor_cell = sess["corridor"]
            round_idx = sess["round"]
            proposer_id = sess["proposer_id"]
            respondent_id = sess["respondent_id"]
            proposer = self.agents.get(proposer_id)
            respondent = self.agents.get(respondent_id)

            if proposer is None or respondent is None:
                to_remove.append(key)
                continue

            # Check max rounds (timeout => fallback)
            if round_idx >= MAX_NEGOTIATION_ROUNDS:
                winner, loser = random.sample([proposer, respondent], 2)
                winner_id = winner.agent_id
                loser_id = loser.agent_id

                winner.score = max(0, winner.score - FALLBACK_PENALTY_BOTH)
                loser.score = max(0, loser.score - FALLBACK_PENALTY_BOTH)
                loser.wait_turns_remaining = max(loser.wait_turns_remaining, FALLBACK_WAIT_TURNS)

                # update wait stats
                self.total_loser_wait_time += FALLBACK_WAIT_TURNS
                self.total_conflicts_with_wait += 1

                for ag in (proposer, respondent):
                    ag.in_conflict = False
                    ag.conflict_partner_id = None
                    ag.conflict_corridor = None
                    if ag.is_active:
                        ag.state = "ACTIVE"

                log_entry = {
                    "episode": self.episode_id,
                    "time_step": self.time_step,
                    "strategy": NEGOTIATION_MODE,
                    "conflict_type": "pre_move",
                    "winner_id": winner_id,
                    "loser_id": loser_id,
                    "loser_wait_turns": FALLBACK_WAIT_TURNS,
                    "negotiation_rounds": round_idx,
                    "final_outcome": "fallback",
                    "corridor_row": corridor_cell[0],
                    "corridor_col": corridor_cell[1]
                }
                self.log_list.append(log_entry)
                to_remove.append(key)
                continue

            # One round of alternating offers
            sess["round"] += 1

            # Proposer sends an offer: I go first, you wait k turns
            proposed_wait = LOSER_WAIT_TURNS_SUCCESS
            msg = {
                "sender_id": proposer_id,
                "receiver_id": respondent_id,
                "performative": "PROPOSE",
                "content": {
                    "proposer_first": True,
                    "respondent_wait": proposed_wait
                }
            }
            sess["messages"].append(msg)

            # Respondent evaluates proposal
            accept_utility = self._utility_wait(respondent, proposed_wait)
            fallback_utility = self._utility_wait(respondent, FALLBACK_WAIT_TURNS) - FALLBACK_PENALTY_BOTH

            if accept_utility >= fallback_utility:
                # ACCEPT
                accept_msg = {
                    "sender_id": respondent_id,
                    "receiver_id": proposer_id,
                    "performative": "ACCEPT",
                    "content": {"accepted_wait": proposed_wait}
                }
                sess["messages"].append(accept_msg)

                winner = proposer
                loser = respondent
                winner_id = winner.agent_id
                loser_id = loser.agent_id

                loser.wait_turns_remaining = max(loser.wait_turns_remaining, proposed_wait)
                loser.score = max(0, loser.score - LOSER_PENALTY_SUCCESS)

                # update wait stats
                self.total_loser_wait_time += proposed_wait
                self.total_conflicts_with_wait += 1

                for ag in (proposer, respondent):
                    ag.in_conflict = False
                    ag.conflict_partner_id = None
                    ag.conflict_corridor = None
                    if ag.is_active:
                        ag.state = "ACTIVE"

                log_entry = {
                    "episode": self.episode_id,
                    "time_step": self.time_step,
                    "strategy": NEGOTIATION_MODE,
                    "conflict_type": "pre_move",
                    "winner_id": winner_id,
                    "loser_id": loser_id,
                    "loser_wait_turns": proposed_wait,
                    "negotiation_rounds": sess["round"],
                    "final_outcome": "success",
                    "corridor_row": corridor_cell[0],
                    "corridor_col": corridor_cell[1]
                }
                self.log_list.append(log_entry)
                self.negotiation_success += 1
                to_remove.append(key)
            else:
                # REJECT -> counter-offer next round
                reject_msg = {
                    "sender_id": respondent_id,
                    "receiver_id": proposer_id,
                    "performative": "REJECT",
                    "content": {}
                }
                sess["messages"].append(reject_msg)
                sess["proposer_id"], sess["respondent_id"] = respondent_id, proposer_id

        for key in to_remove:
            self.negotiations.pop(key, None)

    # ----- Post-move conflict resolution with logging -----

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
            if not agent.is_active or agent.in_conflict:
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
                    for _a in contenders:
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

            # Post-move conflict
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

            # --- LOG POST-MOVE CONFLICT(S) HERE ---
            for loser in contenders:
                if loser is winner:
                    continue
                log_entry = {
                    "episode": self.episode_id,
                    "time_step": self.time_step,
                    "strategy": NEGOTIATION_MODE,
                    "conflict_type": "post_move",
                    "winner_id": winner.agent_id,
                    "loser_id": loser.agent_id,
                    "loser_wait_turns": 0,
                    "negotiation_rounds": 1,
                    "final_outcome": "success",
                    "corridor_row": cell[0],
                    "corridor_col": cell[1]
                }
                self.log_list.append(log_entry)

            if self.is_shared_route(cell):
                if not self.lock(winner, cell):
                    continue

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
        for agent in agents:
            if not agent.is_active:
                continue
            for ghost in self.ghosts:
                if not ghost.is_active:
                    continue
                if (agent.row, agent.col) == (ghost.row, ghost.col):
                    print(f"[!!!] AGENT {agent.agent_id} CAUGHT BY GHOST {ghost.ghost_id}!")
                    agent.energy -= GHOST_CATCH_PENALTY
                    agent.score = max(0, agent.score - 5)

                    if self.is_shared_route((agent.row, agent.col)):
                        self.unlock(agent, (agent.row, agent.col))

                    # Respawn agent at start
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