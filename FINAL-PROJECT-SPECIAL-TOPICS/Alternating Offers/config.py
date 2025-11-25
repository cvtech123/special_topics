
CELL_SIZE = 30
PELLET_POINT = 1
SHARED_ROUTE_PENALTY = 8
AGENT_SPEED = 10
MAX_ENERGY = 80

GHOST_SPEED = 10
LOTTERY_FAIL_CHANCE = 0.8
ENERGY_LOSS_PER_MOVE = 0.5
GHOST_CATCH_PENALTY = 10
GHOST_AVOIDANCE_RADIUS = 2

PELLET_SPAWN_RATIO = 0.3
SCORE_PER_DEAD_AGENT_THRESHOLD = 1
FONT_SIZE = 18

# Sensing / anticipation
SENSING_RADIUS = 4
LOOKAHEAD_STEPS = 2

# --- STRATEGY 2: Alternating Offers (MODIFIED) ---
NEGOTIATION_MODE = "alternating_offers"
MAX_NEGOTIATION_ROUNDS = 3

# === MENTOR FIX: INCREASED WAIT TIMES ===
LOSER_WAIT_TURNS_SUCCESS = 3      
FALLBACK_WAIT_TURNS = 5           

LOSER_PENALTY_SUCCESS = 3         # mild score loss on success
FALLBACK_PENALTY_BOTH = 15        # heavy penalty on timeout/fallback

# Batch config
MAX_EPISODES = 20

# Colors
BLACK = (0, 0, 0)
WALL_COLOR = (40, 40, 50)
CORRIDOR_FLOOR_COLOR = (60, 60, 80)
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT_COLOR = (255, 255, 0)

BAR_WIDTH = 250
BAR_HEIGHT = 10
BAR_BG_COLOR = (30, 30, 30)
BAR_GOOD_COLOR = (0, 180, 0)
BAR_WARN_COLOR = (255, 165, 0)
BAR_DANGER_COLOR = (255, 0, 0)

AGENT_COLORS = [(255, 50, 50), (50, 255, 50), (50, 100, 255)]
GHOST_COLORS = [(255, 150, 150), (150, 255, 150), (150, 150, 255)]

# --- Maze layout ---
MAZE_LAYOUT = [
    "###############################",
    "#.............................#",
    "###########.###.###############",
    "#.#........##.#.#.......#.#...#",
    "#.#.#.#####.#.....###.#.#.###.#",
    "#.#.#.......#.#.##....#.#.....#",
    "#.###.#######.#.#####.###.#####",
    "#...........#.#.#.........#...#",
    "#######.###.#.#.###.#######.#.#",
    "#......#....#.#.#...........#.#",
    "#.#####.###...#.###########.#.#",
    "#...........#.C.C.........#...#",
    "#.###########.#.#.###########C#",
    "#.#.#.........#.#.....#.#.....#",
    "#.#.#.#########.###.#.#.#.###.#",
    "#.....#.....#.#.#...#.....#...#",
    "#.#########.#.#.#.#############",
    "#.............#.#.............#",
    "#C###############.#############",
    "#.............................#",
    "###############################"
]

START_POSITIONS = [(1, 1), (1, 29), (17, 15)]
GHOST_START_POSITIONS = [(9, 1), (9, 29)]

RED_LINE_EXCLUSION = set([
    (r, 15) for r in range(1, 18)
]).union(set([
    (1, c) for c in range(1, 30)
]))