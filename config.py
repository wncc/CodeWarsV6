"""
PyTanks Game Configuration
All game parameters in one place for easy tuning and balancing
"""

# =============================================================================
# NETWORK SETTINGS
# =============================================================================
SERVER_PORT = 5555
SERVER_HOST = "10.51.19.103"  # Change to your server IP

# =============================================================================
# MAP SETTINGS
# =============================================================================
DEFAULT_MAP = "catacombs"
GRID_SIZE = 10  # Each grid cell is 10x10 pixels

# =============================================================================
# PLAYER/TANK SETTINGS
# =============================================================================
# Movement
TANK_SPEED = 3.0
TANK_ROTATION_SPEED = 0.04
TANK_VISUAL_RADIUS = 7.5
TANK_COLLISION_RADIUS = 6  # Smaller to prevent getting stuck

# Aiming
AIM_ROTATION_SPEED = 0.08  # Radians per frame

# Health
MAX_HEALTH = 200.0

# --- Local multi-client setup ---

# If True → first client is keyboard-controlled and rendered
# If False → only script bots run
ENABLE_KEYBOARD_PLAYER = True

# List of bot script filenames (without .py)
BOT_SCRIPTS = [
    "random_bot",
    "random_bot",
    "random_bot",
    "debug_bot",
    "debug_bot2"
]

# If no keyboard player, first script bot renders
RENDER_FIRST_BOT = True

# Colors
PLAYER_COLOR = (255, 0, 0)  # Red for other players
SELF_COLOR = (0, 0, 255)    # Blue for yourself

# =============================================================================
# PHYSICS SETTINGS
# =============================================================================
GRAVITY = 0.6

# Jetpack System
MAX_FUEL = 100.0
FUEL_CONSUMPTION = 0.5      # Fuel consumed per frame when active
FUEL_RECHARGE = 0.5         # Fuel recharged per frame when inactive
JETPACK_THRUST = 0.8        # Upward velocity applied

# =============================================================================
# BULLET SETTINGS
# =============================================================================
BULLET_SPEED = 10.0
MAX_BULLET_DISTANCE = 1200  # Max travel distance before deactivation
BULLET_VISUAL_RADIUS = 5

# =============================================================================
# GUN WEAPON STATS
# Structured dictionary for clarity and future expansion
# =============================================================================

WEAPON_STATS = {
    0: {
        "name": "AK47",
        "damage": 10,
        "accuracy": 4,
        "reload_time": 2.5,
        "melee": 30,
        "rpf": 1,
        "effective_range": 800,
        "dual_wielding": False,
        "rate_of_fire": 0.1,
        "magazine_capacity": 35,
        "ammo_given": 250,
        "sprite_file": "ak47.png",
        "bullet_speed": 60,
    },
    1: {
        "name": "Desert Eagle",
        "damage": 8,
        "accuracy": 2,
        "reload_time": 1.5,
        "melee": 15,
        "rpf": 1,
        "effective_range": 500,
        "dual_wielding": False,
        "rate_of_fire": 0.25,
        "magazine_capacity": 15,
        "ammo_given": 75,
        "sprite_file": "Minieagle.png",
        "bullet_speed": 70,
    },
    2: {
        "name": "Golden Deagle",
        "damage": 10,
        "accuracy": 2,
        "reload_time": 1.5,
        "melee": 25,
        "rpf": 1,
        "effective_range": 600,
        "dual_wielding": False,
        "rate_of_fire": 0.2,
        "magazine_capacity": 15,
        "ammo_given": 75,
        "sprite_file": "gdeagle.png",
        "bullet_speed": 70,
    },
    3: {
        "name": "M14",
        "damage": 36,
        "accuracy": 0,
        "reload_time": 3,
        "melee": 35,
        "rpf": 1,
        "effective_range": 1200,
        "dual_wielding": False,
        "rate_of_fire": 0.55,
        "magazine_capacity": 6,
        "ammo_given": 36,
        "sprite_file": "M14.png",
        "bullet_speed": 80,
    },
    4: {
        "name": "M4",
        "damage": 14,
        "accuracy": 2,
        "reload_time": 2.5,
        "melee": 30,
        "rpf": 1,
        "effective_range": 1000,
        "dual_wielding": False,
        "rate_of_fire": 0.5,
        "magazine_capacity": 24,
        "ammo_given": 300,
        "sprite_file": "M4.png",
        "bullet_speed": 75,
    },
    5: {
        "name": "M93BA Sniper",
        "damage": 75,
        "accuracy": 0,
        "reload_time": 3.5,
        "melee": 35,
        "rpf": 1,
        "effective_range": 1500,
        "dual_wielding": False,
        "rate_of_fire": 0.8,
        "magazine_capacity": 3,
        "ammo_given": 20,
        "sprite_file": "Sniper.png",
        "bullet_speed": 100,
    },
    6: {
        "name": "Magnum",
        "damage": 30,
        "accuracy": 1,
        "reload_time": 2.5,
        "melee": 25,
        "rpf": 1,
        "effective_range": 650,
        "dual_wielding": False,
        "rate_of_fire": 0.6,
        "magazine_capacity": 6,
        "ammo_given": 36,
        "sprite_file": "magnum.png",
        "bullet_speed": 75,
    },
    7: {
        "name": "MP5",
        "damage": 7,
        "accuracy": 5,
        "reload_time": 2,
        "melee": 30,
        "rpf": 1,
        "effective_range": 700,
        "dual_wielding": True,
        "rate_of_fire": 0.06,
        "magazine_capacity": 50,
        "ammo_given": 400,
        "sprite_file": "mp5.png",
        "bullet_speed": 65,
    },
    8: {
        "name": "UZI",
        "damage": 7,
        "accuracy": 6,
        "reload_time": 1.8,
        "melee": 20,
        "rpf": 1,
        "effective_range": 500,
        "dual_wielding": True,
        "rate_of_fire": 0.1,
        "magazine_capacity": 40,
        "ammo_given": 400,
        "sprite_file": "Uzi.png",
        "bullet_speed": 60,
    },
    9: {
        "name": "TEC9",
        "damage": 10,
        "accuracy": 4,
        "reload_time": 1.8,
        "melee": 25,
        "rpf": 1,
        "effective_range": 600,
        "dual_wielding": True,
        "rate_of_fire": 0.15,
        "magazine_capacity": 40,
        "ammo_given": 400,
        "sprite_file": "Tec-9.png",
        "bullet_speed": 65,
    },
    10: {
        "name": "SPAS-12",
        "damage": 25,
        "accuracy": 10,
        "reload_time": 3.5,
        "melee": 40,
        "rpf": 5,
        "effective_range": 325,
        "dual_wielding": False,
        "rate_of_fire": 0.75,
        "magazine_capacity": 5,
        "ammo_given": 24,
        "sprite_file": "Shotgun.png",
        "bullet_speed": 55,
    },
    11: {
        "name": "SAW",
        "damage": 100,
        "accuracy": 0,
        "reload_time": 5,
        "melee": 35,
        "rpf": 1,
        "effective_range": 1000,
        "dual_wielding": False,
        "rate_of_fire": 1.25,
        "magazine_capacity": 3,
        "ammo_given": 6,
        "sprite_file": "saw.png",
        "bullet_speed": 3.0,
    },
    12: {
        "name": "TAVOR",
        "damage": 9,
        "accuracy": 2,
        "reload_time": 2,
        "melee": 30,
        "rpf": 1,
        "effective_range": 750,
        "dual_wielding": False,
        "rate_of_fire": 0.12,
        "magazine_capacity": 35,
        "ammo_given": 200,
        "sprite_file": "tavor.png",
        "bullet_speed": 70,
    },
    13: {
        "name": "XM8",
        "damage": 8,
        "accuracy": 3.25,
        "reload_time": 2.2,
        "melee": 30,
        "rpf": 1,
        "effective_range": 875,
        "dual_wielding": False,
        "rate_of_fire": 0.085,
        "magazine_capacity": 30,
        "ammo_given": 200,
        "sprite_file": "XM8.png",
        "bullet_speed": 72,
    },
    14: {
        "name": "MINIGUN",
        "damage": 30,
        "accuracy": 7,
        "reload_time": 4.5,
        "melee": 35,
        "rpf": 1,
        "effective_range": 650,
        "dual_wielding": False,
        "rate_of_fire": 0.08,
        "magazine_capacity": 50,
        "ammo_given": 200,
        "sprite_file": "minigun.png",
        "bullet_speed": 68,
    },
    15: {
        "name": "ROCKET_LAUNCHER",
        "damage": 100,
        "accuracy": 10,
        "reload_time": 4,
        "melee": 40,
        "rpf": 1,
        "effective_range": 1200,
        "dual_wielding": False,
        "rate_of_fire": 0.5,
        "magazine_capacity": 3,
        "ammo_given": 12,
        "sprite_file": "rocket_launcher.png",
        "bullet_speed": 3.0,
    },
}

# =============================================================================
# GUN SPAWN SYSTEM
# =============================================================================
GUN_SPAWN_INTERVAL = 15.0    # Seconds before gun respawns
GUN_PICKUP_RADIUS = 20.0     # Distance to pick up gun
MAX_GUNS_PER_PLAYER = 2      # Inventory size
DEFAULT_STARTING_WEAPON = 1  # Desert Eagle

# =============================================================================
# GRENADE DATA
# =============================================================================
FRAG_GRENADE_COUNT = 2       # Number of frag grenades given on spawn
PROXY_GRENADE_COUNT = 1      # Number of proximity grenades given on spawn
GAS_GREANADE_COUNT = 1       # Number of gas grenades given on spawn

# Gun spawn locations per map
# Format: (x, y, weapon_id)
GUN_SPAWN_POINTS = {
    "catacombs": [
        # Left side spawns
        (100, 300, 1),   # Desert Eagle
        (150, 450, 8),   # UZI
        (200, 150, 7),   # MP5
        
        # Center spawns
        (400, 250, 0),   # AK47
        (450, 400, 10),  # Shotgun
        (500, 100, 4),   # M4
        
        # Right side spawns
        (700, 300, 5),   # Sniper
        (650, 450, 3),   # M14
        (750, 150, 11),  # SMAW
        
        # Additional spawns
        (300, 500, 6),   # Magnum
        (600, 500, 12),  # TAVOR
        (350, 50, 13),   # XM8
    ],
    
    # Add more maps here
    # "arena": [...],
    # "open": [...],
}

# =============================================================================
# RENDERING SETTINGS
# =============================================================================
GAME_FPS = 30              # Client FPS
SERVER_FPS = 60            # Server tick rate

# Background Colors
BACKGROUND_COLOR = (101, 67, 33)      # Brown background
OBSTACLE_COLOR = (210, 180, 140)      # Light brown/yellowish blocks
OBSTACLE_BORDER_COLOR = (160, 130, 90)

# Gun Spawn Visual
GUN_SPAWN_GLOW_COLOR = (255, 215, 0)  # Gold
GUN_SPAWN_SCALE = 25                   # Size of spawned gun (matching player size)

# =============================================================================
# INPUT INDICES
# =============================================================================
# Player input array indices
INPUT_JETPACK = 0
INPUT_MOVE_LEFT = 1
INPUT_MOVE_RIGHT = 2
INPUT_AIM_UP = 3
INPUT_AIM_DOWN = 4
INPUT_AIM_LEFT = 5
INPUT_AIM_RIGHT = 6
INPUT_SHOOT = 7
INPUT_RELOAD = 8
INPUT_SWITCH_GUN = 9

# =============================================================================
# WORLD DATA INDICES (for network protocol)
# =============================================================================
# Tank columns (rows 0-7)
WORLD_IS_ALIVE = 0
WORLD_X = 1
WORLD_Y = 2
WORLD_THETA = 3
WORLD_V = 4
WORLD_OMEGA = 5
WORLD_FUEL = 6
WORLD_HEALTH = 7
WORLD_SCORE = 8
WORLD_CURRENT_AMMO = 9
WORLD_TOTAL_AMMO = 10

# Bullet columns (rows 8-47)
# Uses same indices but some have different meanings:
# WORLD_V = bullet speed
# WORLD_OMEGA = distance traveled
# WORLD_HEALTH = damage
# WORLD_CURRENT_AMMO = owner id

# =============================================================================
# GAME MECHANICS
# =============================================================================
BULLET_HIT_RADIUS = 25      # Collision detection radius for bullets vs players

# SAW weapon settings
SAW_WEAPON_ID = 11
SAW_LIFETIME = 5                    # Seconds a saw projectile stays alive
SAW_EXPLOSION_RADIUS = 60.0         # Small frag-like blast on saw timeout
SAW_EXPLOSION_DAMAGE = 300.0
SAW_SELF_HIT_ARM_DISTANCE = 35.0    # Must travel this far before it can hurt the shooter

RESPAWN_WITH_FULL_FUEL = True
RESPAWN_WITH_FULL_HEALTH = True

# Rocket Launcher settings
ROCKET_LAUNCHER_ID = 15
ROCKET_EXPLOSION_RADIUS = 80.0
ROCKET_EXPLOSION_DAMAGE = 500.0

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_weapon_stat(weapon_id, stat_name):
    """Get a specific stat for a weapon by name"""
    if weapon_id not in WEAPON_STATS:
        return None

    if stat_name not in WEAPON_STATS[weapon_id]:
        return None

    return WEAPON_STATS[weapon_id][stat_name]

def get_all_weapon_ids():
    """Get list of all weapon IDs"""
    return list(WEAPON_STATS.keys())

def get_spawn_points_for_map(map_name):
    """Get spawn points for a specific map"""
    return GUN_SPAWN_POINTS.get(map_name, [])
