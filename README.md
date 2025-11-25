# Multi-Agent Pac-Man Simulation 👻ᗧ•••

This project simulates a multi-agent environment where cooperative agents (Pac-Men) must collect pellets while avoiding adversarial Ghosts. The project compares different conflict resolution strategies for pathfinding negotiation.

## 📂 Project Structure
Ensure your directories are organized as follows:

```text
/FINAL-PROJECT-SPECIAL-TOPICS
│
├── /Alternating Offers        # (S1) Alternating Offers Negotiation 
│   ├── main.py
│   ├── config.py
│   ├── conflict_manager.py
│   ├── agent.py
│   ├── ghost.py
│   └── maze.py
│
├── /Priority-Based (baseline)   # (S2) Priority-based Negotiation
│   ├── main.py
│   ├── config.py
│   ├── conflict_manager.py
│   ├── agent.py
│   ├── ghost.py
│   └── maze.py

```

## ⚙️ Prerequisites
Python 3.8+
Pygame library

## To install the dependencies:
pip install pygame

## 🚀How to Run 
Navigate to the directory FINAL-PROJECT-SPECIAL-TOPICS/Priority-Based (baseline) or /Alternating Offers test and run the main.py script.

## Simulation Workflow
Follow these simple steps to generate data:

Start: Run the command for your chosen strategy. The window will open in a PAUSED state.
Run Batch: Press ENTER or SPACE. The simulation will automatically run for 20 episodes.

Save Data: Once the batch is complete (or at any time), press S to save the raw CSV logs.

## 📊 Output Files
After pressing S, the following files will be generated.
