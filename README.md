# Multi-Agent Pac-Man Simulation 👻ᗧ•••

This project simulates a multi-agent environment where cooperative agents (Pac-Men) must collect pellets while avoiding adversarial Ghosts. The project compares different conflict resolution strategies for pathfinding negotiation.

## 📂 Project Structure

Ensure your directories are organized as follows:

```text
/MultiAgent_Simulation
│
├── /Strategy1_Priority        # (S1) Priority-based Negotiation
│   ├── main.py
│   ├── config.py
│   ├── conflict_manager.py
│   ├── agent.py
│   ├── ghost.py
│   └── maze.py
│
├── /Strategy2_Alternating     # (S2) Alternating Offers Negotiation
│   ├── main.py
│   ├── config.py
│   ├── conflict_manager.py
│   ├── agent.py
│   ├── ghost.py
│   └── maze.py
│
└── /Baseline_Ghost            # Aggressive Ghost Baseline
    ├── main.py
    ├── config.py
    ├── conflict_manager.py
    ├── agent.py
    ├── ghost.py
    └── maze.py
```

## ⚙️ Prerequisites
Python 3.8+
Pygame library

## To install the dependencies:
pip install pygame

🚀How to Run 
Navigate to the directory of the strategy you want to test and run the main.py script.

Simulation Workflow
Follow these simple steps to generate data:

Start: Run the command for your chosen strategy. The window will open in a PAUSED state.

Run Batch: Press ENTER or SPACE. The simulation will automatically run for 20 episodes.

Save Data: Once the batch is complete (or at any time), press S to save the raw CSV logs.

📊 Output Files
After pressing S, the following files will be generated in the strategy folder:

*_conflicts_log.csv: Detailed logs of every negotiation and conflict event.

*_episode_summary.csv: High-level summary stats (Score, Steps, Wait Time) for each episode.
