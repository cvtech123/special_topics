Multi-Agent Pac-Man Simulation: Negotiation Strategies
This project simulates a multi-agent environment where cooperative agents (Pac-Men) must collect pellets while avoiding adversarial agents (Ghosts). 
The core focus is on comparing two distinct conflict resolution strategies—how agents negotiate passage when their paths cross in narrow corridors.


/MultiAgent_Simulation
│
├── /Priority-based       # (S1) Priority-based Baseline
│   ├── main.py
│   ├── config.py
│   ├── conflict_manager.py
│   ├── agent.py
│   ├── ghost.py
│   └── maze.py
│
└── /Alternating offers    # (S2) Alternating Offers Negotiation
    ├── main.py
    ├── config.py             # Contains specific S2 constants
    ├── conflict_manager.py   # Contains offer/counter-offer logic
    ├── agent.py
    ├── ghost.py
    └── maze.py
