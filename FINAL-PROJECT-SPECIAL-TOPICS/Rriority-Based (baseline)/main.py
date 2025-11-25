# main.py
import pygame
import random
import os
import csv
from config import *
from maze import Maze
from agent import Agent
from ghost import Ghost
from conflict_manager import ConflictManager

# --- Global logs ---
CONFLICT_LOGS = []        
EPISODE_SUMMARIES = []    

MAZE_ROWS = len(MAZE_LAYOUT)
MAZE_COLS = len(MAZE_LAYOUT[0])
MAZE_WIDTH = MAZE_COLS * CELL_SIZE
SCREEN_HEIGHT = MAZE_ROWS * CELL_SIZE
BLANK_SPACE_WIDTH = 450
SCREEN_WIDTH = MAZE_WIDTH + BLANK_SPACE_WIDTH

def draw_scoreboard(screen, font, agents, ghosts, manager, episode_idx, episodes_total, batch_done):
    panel_x_start = MAZE_WIDTH + 30

    title_text = font.render("MULTI-AGENT CHALLENGE", True, TEXT_COLOR)
    screen.blit(
        title_text,
        (MAZE_WIDTH + (BLANK_SPACE_WIDTH / 2) - (title_text.get_width() / 2), 20)
    )

    episode_text = font.render(f"Episode {episode_idx}/{episodes_total}", True, (150, 150, 255))
    screen.blit(episode_text, (panel_x_start, 40))

    y_offset = 60

    if batch_done:
        status_message = "BATCH DONE - Press S to save CSV, ENTER for new batch"
        status_color = HIGHLIGHT_COLOR
        status_text = font.render(status_message, True, status_color)
        screen.blit(status_text, (panel_x_start, y_offset))
        return

    if manager.is_paused:
        status_message = "Press ENTER/SPACE to start batch"
        status_color = (255, 150, 150)
    else:
        status_message = "SIMULATION ACTIVE"
        status_color = (150, 255, 150)

    status_text = font.render(status_message, True, status_color)
    screen.blit(status_text, (panel_x_start, y_offset))

    y_offset = 90

    for agent in agents:
        status_color = agent.color if agent.is_active else (50, 50, 50)

        score_text = font.render(
            f"Agent {agent.agent_id} ({'A' if agent.is_active else 'D'}):",
            True, status_color
        )
        stats_text = font.render(
            f"Score:{agent.score} | Energy:{int(agent.energy)} | St:{agent.state}",
            True, TEXT_COLOR
        )
        screen.blit(score_text, (panel_x_start, y_offset))
        screen.blit(stats_text, (panel_x_start, y_offset + 20))

        bar_x = panel_x_start
        bar_y = y_offset + 40
        energy_ratio = agent.energy / MAX_ENERGY
        current_bar_width = int(BAR_WIDTH * energy_ratio)

        if energy_ratio > 0.6:
            bar_fill_color = BAR_GOOD_COLOR
        elif energy_ratio > 0.3:
            bar_fill_color = BAR_WARN_COLOR
        else:
            bar_fill_color = BAR_DANGER_COLOR

        pygame.draw.rect(screen, BAR_BG_COLOR, (bar_x, bar_y, BAR_WIDTH, BAR_HEIGHT))
        pygame.draw.rect(screen, bar_fill_color, (bar_x, bar_y, current_bar_width, BAR_HEIGHT))

        y_offset += 65

    y_offset += 20
    metrics_title = font.render("LIVE METRICS:", True, (150, 150, 255))
    screen.blit(metrics_title, (panel_x_start, y_offset))
    y_offset += 30

    conflict_text = font.render(f"Post-move Conflicts: {manager.conflict_count}", True, TEXT_COLOR)
    success_text = font.render(f"Negotiations (pre-move): {manager.negotiation_success}", True, TEXT_COLOR)
    lock_conflict_text = font.render(f"Lock Conflicts: {manager.lock_conflict_events}", True, TEXT_COLOR)
    predicted_conflict_text = font.render(f"Predicted Conflicts: {manager.predicted_conflict_events}", True, TEXT_COLOR)

    screen.blit(conflict_text, (panel_x_start, y_offset))
    screen.blit(success_text, (panel_x_start, y_offset + 20))
    screen.blit(lock_conflict_text, (panel_x_start, y_offset + 40))
    screen.blit(predicted_conflict_text, (panel_x_start, y_offset + 60))


def reset_game(screen, episode_id, log_list):
    random.seed(pygame.time.get_ticks())
    maze = Maze(screen)
    agents_list = [
        Agent(1, AGENT_COLORS[0], START_POSITIONS[0][0], START_POSITIONS[0][1], maze, None),
        Agent(2, AGENT_COLORS[1], START_POSITIONS[1][0], START_POSITIONS[1][1], maze, None),
        Agent(3, AGENT_COLORS[2], START_POSITIONS[2][0], START_POSITIONS[2][1], maze, None)
    ]
    ghosts_list = [
        Ghost(1, GHOST_COLORS[0], GHOST_START_POSITIONS[0][0], GHOST_START_POSITIONS[0][1], maze),
        Ghost(2, GHOST_COLORS[1], GHOST_START_POSITIONS[1][0], GHOST_START_POSITIONS[1][1], maze)
    ]
    conflict_manager = ConflictManager(maze, agents_list, ghosts_list, episode_id, log_list)
    conflict_manager.is_paused = True

    for agent in agents_list:
        agent.manager = conflict_manager
        if (agent.row, agent.col) in maze.shared_route_cells:
            conflict_manager.lock(agent, (agent.row, agent.col))

    print(f"--- EPISODE {episode_id} READY ---")
    return maze, agents_list, ghosts_list, conflict_manager


def save_logs_to_csv(logs, filename="priority_conflicts_log.csv"):
    # Per-conflict logs (pre-move only)
    if not logs:
        print("No conflict logs to save.")
    else:
        fieldnames = [
            "episode", "time_step", "strategy", "conflict_type",
            "winner_id", "loser_id", "loser_wait_turns",
            "negotiation_rounds", "final_outcome",
            "corridor_row", "corridor_col"
        ]
        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in logs:
                writer.writerow(row)
        print(f"Saved {len(logs)} conflict records to {filename}")

    # Per-episode summaries
    if not EPISODE_SUMMARIES:
        print("No episode summaries to save.")
    else:
        ep_fieldnames = [
            "episode",
            "post_move_conflicts",
            "pre_move_conflicts",
            "negotiations",
            "predicted_conflicts",
            "lock_conflicts",
            "avg_loser_wait",
            "agent1_score",
            "agent2_score",
            "agent3_score"
        ]
        with open("priority_episode_summary.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=ep_fieldnames)
            writer.writeheader()
            for row in EPISODE_SUMMARIES:
                writer.writerow(row)
        print(f"Saved {len(EPISODE_SUMMARIES)} episode summaries to priority_episode_summary.csv")


def main():
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init()
    try:
        font = pygame.font.Font(None, FONT_SIZE)
    except pygame.error:
        print("Warning: Pygame font initialization failed.")
        font = None
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Multi-Agent Pac-Men (Priority Baseline)")

    episodes_completed = 1
    maze, agents_list, ghosts_list, conflict_manager = reset_game(
        screen, episodes_completed, CONFLICT_LOGS
    )
    conflict_manager.is_paused = True
    running_simulation = False
    batch_done = False

    print("--- Press ENTER/SPACE once to run 50 episodes ---")

    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if batch_done:
                        batch_done = False
                        episodes_completed = 1
                        CONFLICT_LOGS.clear()
                        EPISODE_SUMMARIES.clear()
                        maze, agents_list, ghosts_list, conflict_manager = reset_game(
                            screen, episodes_completed, CONFLICT_LOGS
                        )
                        conflict_manager.is_paused = False
                        running_simulation = True
                        print("--- New batch started ---")
                    else:
                        conflict_manager.is_paused = False
                        running_simulation = True
                        print("--- Batch running ---")
                if event.key == pygame.K_s:
                    save_logs_to_csv(CONFLICT_LOGS)

        if running_simulation and not conflict_manager.is_paused and not batch_done:
            conflict_manager.time_step += 1

            for ghost in ghosts_list:
                ghost.decide_next_move(agents_list)
            conflict_manager.update_ghost_positions()
            for agent in agents_list:
                agent.decide_next_move()
            conflict_manager.resolve_path_conflicts(agents_list)
            conflict_manager.check_ghost_collisions(agents_list)

            active_agents = [a for a in agents_list if a.is_active]
            game_over = False

            if len(active_agents) == 1:
                survivor = active_agents[0]
                dead_count = len(agents_list) - 1
                threshold = dead_count * SCORE_PER_DEAD_AGENT_THRESHOLD
                if survivor.score >= threshold:
                    game_over = True
            if not maze.pellets:
                game_over = True
            if not active_agents:
                game_over = True

            if game_over:
                # --- Build per-episode summary before resetting ---
                current_episode = episodes_completed

                if conflict_manager.total_conflicts_with_wait > 0:
                    avg_loser_wait = (
                        conflict_manager.total_loser_wait_time /
                        conflict_manager.total_conflicts_with_wait
                    )
                else:
                    avg_loser_wait = 0.0

                summary_row = {
                    "episode": current_episode,
                    "post_move_conflicts": conflict_manager.conflict_count,
                    "pre_move_conflicts": conflict_manager.total_conflicts_with_wait,
                    "negotiations": conflict_manager.negotiation_success,
                    "predicted_conflicts": conflict_manager.predicted_conflict_events,
                    "lock_conflicts": conflict_manager.lock_conflict_events,
                    "avg_loser_wait": avg_loser_wait,
                    "agent1_score": agents_list[0].score,
                    "agent2_score": agents_list[1].score,
                    "agent3_score": agents_list[2].score
                }
                EPISODE_SUMMARIES.append(summary_row)

                print(f"Episode {current_episode} finished.")
                episodes_completed += 1

                if episodes_completed <= MAX_EPISODES:
                    maze, agents_list, ghosts_list, conflict_manager = reset_game(
                        screen, episodes_completed, CONFLICT_LOGS
                    )
                    conflict_manager.is_paused = False
                else:
                    batch_done = True
                    running_simulation = False
                    conflict_manager.is_paused = True
                    print("=== Batch of 50 episodes completed. "
                          "Press 'S' to save CSV, ENTER for new batch. ===")

        screen.fill(BLACK)
        maze.draw_maze(conflict_manager)
        for ghost in ghosts_list:
            ghost.draw(screen)
        for agent in agents_list:
            agent.draw(screen)

        if font:
            draw_scoreboard(screen, font, agents_list, ghosts_list, conflict_manager,
                            min(episodes_completed, MAX_EPISODES), MAX_EPISODES, batch_done)

        pygame.draw.line(screen, (50, 50, 50), (MAZE_WIDTH, 0), (MAZE_WIDTH, SCREEN_HEIGHT), 2)
        pygame.display.flip()

        if running_simulation and not conflict_manager.is_paused and not batch_done:
            clock.tick(60)
        else:
            pygame.time.wait(10)

    pygame.quit()

if __name__ == "__main__":
    main()