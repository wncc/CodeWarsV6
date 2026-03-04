# Developer Documentation

*A comprehensive technical guide for developers working on PyTanks*

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [File Structure](#file-structure)
4. [Core Systems](#core-systems)
5. [Network Protocol](#network-protocol)
6. [Game State Management](#game-state-management)
7. [Weapon System](#weapon-system)
8. [Bot Development](#bot-development)
9. [Map System](#map-system)
10. [Visual Effects](#visual-effects)
11. [Development Workflow](#development-workflow)
12. [Extending the Game](#extending-the-game)

---

## Project Overview
- **Mini Militia-Inspired Gameplay**: Jetpack flight, dual wielding, gun pickups, and fast-paced combat
- **Client-Server Architecture**: Authoritative server with multiple clients
- **Real-time Multiplayer**: Up to 8 players simultaneously
- **Jetpack Physics**: Gravity-based movement with limited fuel mechanics
- **Weapon System**: 15 different guns with unique stats and behaviors
- **Bot Framework**: Scriptable AI players with sandboxed execution
- **Map Editor**: Visual tool for creating custom maps and weapon spawns
- **Visual Effects**: Muzzle flashes, particle effects, bullet tracers

### Technology Stack
- **Python 3.x**: Core language
- **Pygame**: Rendering and input handling
- **NumPy**: Efficient array-based game state
- **Socket**: TCP network communication
- **JSON**: Map and spawn data serialization

---

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                     GAME CLIENTS                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Keyboard   │  │   Bot #1     │  │   Bot #2     │  │
│  │   Player     │  │ (random_bot) │  │ (debug_bot)  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│         └─────────────────┴─────────────────┘           │
│                           │                             │
│                      game.py                            │
│                    (PlayerClient)                       │
│                           │                             │
└───────────────────────────┼─────────────────────────────┘
                            │
                     Network (TCP/IP)
                            │
┌───────────────────────────▼─────────────────────────────┐
│                    GAME SERVER                          │
│                       server.py                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Authoritative Game State               │   │
│  │  • Player positions, health, velocity            │   │
│  │  • Bullet trajectories and collisions            │   │
│  │  • Gun spawns and inventory                      │   │
│  │  • Physics simulation                            │   │
│  │  • Hit detection and damage                      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ GunSpawner   │  │   Weapons    │  │  Collision   │  │
│  │   System     │  │   & Grenades │  │     Map      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Client Input** → `game.py` collects keyboard/bot inputs
2. **Client Sends** → 10-bool action array sent to server
3. **Server Processes** → Physics, collisions, damage calculated
4. **Server Sends** → Complete game state broadcast to all clients
5. **Client Renders** → Visual representation of game state

---

## File Structure

### Core Files

| File | Purpose | Key Responsibilities |
|------|---------|---------------------|
| `server.py` | Game server (1077 lines) | Physics simulation, collision detection, authoritative game state, player connections |
| `game.py` | Game client (487 lines) | Rendering, input handling, client-side prediction, visual effects |
| `client.py` | Network layer (106 lines) | TCP socket communication, data serialization/deserialization |
| `config.py` | Configuration (459 lines) | All game parameters, weapon stats, physics constants, network settings |

### System Files

| File | Purpose | Key Components |
|------|---------|----------------|
| `weapons.py` | Weapon definitions (128 lines) | `Gun` class, `Grenade` class, weapon registry |
| `gun_spawner.py` | Gun spawn system (154 lines) | `GunSpawner`, `PlayerInventory`, spawn management |
| `weapon_renderer.py` | Weapon visuals (247 lines) | Gun sprite rendering, bullet sprites, visual scaling |
| `weapon_effects.py` | Visual effects (228 lines) | Muzzle flashes, particle systems, impact effects |

### Tools

| File | Purpose | Features |
|------|---------|----------|
| `map_editor.py` | Map creation tool (336 lines) | Visual map editing, collision painting, weapon spawn placement |
| `create_maps.py` | Programmatic map creation | Scripted map generation |
| `migrate_spawns.py` | Data migration utility | Convert spawn formats |

### Bot Framework

| Path | Purpose |
|------|---------|
| `scripts/bot.py` | Bot execution engine with sandboxing |
| `scripts/helpers.py` | Bot API (movement, aiming, state queries) |
| `scripts/random_bot.py` | Example: Random movement bot |
| `scripts/simple_bot.py` | Example: Simple AI bot |
| `scripts/debug_bot.py` | Example: Debug/test bot |

### Assets

```
assets/
├── character/          # Player sprite animation frames
│   ├── character1.png
│   ├── character2.png
│   ├── character3.png
│   └── character4.png
├── guns/               # Weapon sprites (15 different guns)
│   ├── ak47.png
│   ├── Minieagle.png
│   ├── M14.png
│   └── ...
└── grenades/           # Grenade sprites
```

### Maps

```
maps/
├── catacombs.npy              # Collision map (NumPy array)
├── catacombs_spawns.json      # Weapon spawn locations
├── arena.npy
├── default.npy
└── ...
```

---

## Core Systems

### 1. World Data Structure

The game state is stored in a **single NumPy array** called `world_data`:

```python
world_data = np.zeros((55, 11), dtype=np.float64)
```

#### Rows 0-7: Players
Each player occupies one row with 11 columns:

| Column | Data | Description |
|--------|------|-------------|
| 0 | `alive` | 1.0 = active, 0.0 = dead/disconnected |
| 1 | `x` | X position (pixels) |
| 2 | `y` | Y position (pixels) |
| 3 | `vx` | X velocity (pixels/frame) |
| 4 | `vy` | Y velocity (pixels/frame) |
| 5 | `angle` | Gun aim angle (radians) |
| 6 | `fuel` | Jetpack fuel (0-100) - Mini Militia style |
| 7 | `health` | Health points (0-200) |
| 8 | `shooting` | 1.0 = currently firing |
| 9 | `reloading` | 1.0 = currently reloading |
| 10 | `respawn_timer` | Seconds until respawn |

#### Rows 8-47: Bullets
40 bullet slots (supports 40 active bullets):

| Column | Data |
|--------|------|
| 0 | `active` (1.0 or 0.0) |
| 1 | `x` position |
| 2 | `y` position |
| 3 | `vx` velocity |
| 4 | `vy` velocity |
| 5 | `damage` |
| 6 | `player_id` (who fired it) |
| 7 | `weapon_id` |
| 8 | `distance_traveled` |

#### Rows 48-54: Grenades
7 grenade slots:

| Column | Data |
|--------|------|
| 0 | `active` |
| 1-2 | `x, y` position |
| 3 | `angle` |
| 4-5 | `vx, vy` velocity |
| 6 | `blast_radius` |
| 7 | `damage` |
| 8 | `effect_time` |
| 9 | `player_id` (thrower) |
| 10 | `grenade_id` |

### 2. Player Inventory System

Each player can carry **2 guns simultaneously**:

```python
inventory_data[player_id] = [weapon1_id, weapon2_id, active_slot]
```

- `active_slot`: 0 or 1 (which gun is equipped)
- Players switch guns with the 'S' key
- Picking up a gun replaces the currently held gun

### 3. Physics Engine (Server-Side)

Runs at **60 FPS** with fixed timestep, implementing Mini Militia-style movement:

```python
# Gravity (always applies)
vy += GRAVITY  # 0.6 pixels/frame²

# Jetpack thrust (Mini Militia-style limited fuel)
if jetpack_active:
    vy -= JETPACK_THRUST  # 0.8 pixels/frame (upward)
    fuel -= FUEL_CONSUMPTION  # 0.5 fuel/frame

# Horizontal movement
if move_left:
    x -= PLAYER_SPEED  # 3.0 pixels/frame
if move_right:
    x += PLAYER_SPEED  # 3.0 pixels/frame
```

**Collision Detection**:
- Grid-based collision map (10x10 pixel cells)
- Characters have 6-pixel collision radius
- Bullets use raycasting for precision
- Inspired by Mini Militia's hit detection system

### 4. Gun Spawn System

**Mini Militia-Style Gun Spawns**:
1. `GunSpawner.initialize_map(map_name)` loads spawn points
2. Guns spawn at fixed locations with visual indicators (like Mini Militia)
3. Guns respawn at fixed intervals (default: 15 seconds)
4. Players pick up guns by proximity (radius: 30 pixels)
5. After pickup, spawn point enters cooldown before next spawn
6. Players can carry 2 guns simultaneously (dual wielding)

**Spawn Point Format**:
```json
[
  [x, y, weapon_id],
  [400, 300, 3],  // M14 Sniper spawns at (400, 300)
  [600, 450, 11]  // SAW spawns at (600, 450)
]
```

---

## Network Protocol

### Connection Handshake

**Client → Server**:
1. Send player name (16 bytes, UTF-8, padded)

**Server → Client**:
1. Send player ID (4 bytes, little-endian int32)
2. Send map info (12 bytes: grid_w, grid_h, grid_size)
3. Send collision map (grid_w × grid_h × 4 bytes)

### Game Loop Communication

**Every Frame (60 FPS)**:

**Client → Server** (10 bytes):
```python
action_array = np.array([
    jetpack,      # bool
    move_left,    # bool
    move_right,   # bool
    aim_up,       # bool
    aim_down,     # bool
    aim_left,     # bool
    aim_right,    # bool
    shoot,        # bool
    reload,       # bool
    switch_gun    # bool
], dtype=bool)
```

**Server → Client** (variable size):
```python
# 1. World data (4840 bytes)
world_data: (55, 11) float64 array

# 2. Header (12 bytes)
[spawn_len, gas_len, grenade_len]: 3 int32s

# 3. Gun spawns (variable)
spawn_data: [(x, y, weapon_id, active), ...] as float32

# 4. Gas effects (variable)
gas_data: [(x, y, radius, duration), ...] as float64

# 5. Grenade visual data (256 bytes)
grenade_data: (8, 4) float64 array

# 6. Inventory data (96 bytes)
inventory_data: (8, 3) int32 array
```

**Total minimum packet size**: ~5200 bytes per frame

---

## Game State Management

### Server Authority

The server is the **single source of truth**:
- All physics calculations on server
- Hit detection on server
- Damage application on server
- Respawn logic on server

### Client Responsibilities

Clients are **display-only**:
- Render the world state
- Collect input (keyboard/bot)
- Send input to server
- Display visual effects (client-side only)

### Synchronization

- **No client prediction** (simpler, no lag compensation)
- **No interpolation** (direct state rendering)
- Clients render exactly what server sends
- 60 FPS sync between all clients

---

## Weapon System

### Weapon Definition

Weapons are defined in `config.py` as `WEAPON_STATS` dictionaries:

```python
WEAPON_STATS = {
    3: {  # M14 Sniper Rifle
        "name": "M14",
        "damage": 36,                  # Per shot
        "accuracy": 0,                 # Spread in degrees (0 = perfect)
        "reload_time": 3,              # Seconds
        "melee": 35,                   # Melee damage
        "rpf": 1,                      # Rounds per fire (shotguns use >1)
        "effective_range": 1200,       # Pixels
        "dual_wielding": False,        # Can dual-wield?
        "rate_of_fire": 0.55,         # Seconds between shots
        "magazine_capacity": 6,        # Bullets per magazine
        "ammo_given": 36,              # Total ammo on pickup
        "sprite_file": "M14.png",      # Asset filename
        "bullet_speed": 80,            # Pixels per frame
    }
}
```

### Special Weapon Types

**Shotguns** (rpf > 1):
- Fire multiple bullets per shot
- Each bullet has random spread

**Sniper Rifles** (accuracy = 0):
- Perfect accuracy
- High damage per shot

**SMGs** (high rate_of_fire):
- Fast shooting
- Lower damage per bullet

### Weapon Classes

```python
# weapons.py
class Gun:
    def can_shoot(self):
        """Check if enough ammo"""
        return self.current_ammo >= self.rpf
    
    def shoot(self):
        """Consume ammo"""
        self.current_ammo -= self.rpf
    
    def reload(self):
        """Refill magazine from reserve"""
        ammo_needed = self.magazine_capacity - self.current_ammo
        ammo_to_reload = min(ammo_needed, self.total_ammo)
        self.current_ammo += ammo_to_reload
        self.total_ammo -= ammo_to_reload
```

### Grenade System

Grenades use physics-based arcs:

```python
class Grenade:
    def __init__(self, grenade_id, name, damage, blast_radius, 
                 fuse_time, sprite_file, effect_time, proxy):
        self.blast_radius = 100  # Explosion radius
        self.fuse_time = 3.0     # Seconds until detonation
        self.is_proxy = False    # Proximity detonation?
        self.effect_time = 5.0   # Lingering gas duration
```

**Grenade Types**:
- **Frag**: Standard explosion damage
- **Gas**: Lingering area-of-effect damage
- **Proxy**: Detonation when enemy is near

---

## Bot Development

### Bot API Overview

Bots are Python scripts with a single `run(state, memory)` function.

**Restrictions**:
- ✅ Only one function: `run`
- ❌ No imports
- ❌ No classes
- ❌ No global variables (use `memory` string)
- ✅ Access to helper functions (movement, aiming, queries)

### Bot Script Template

```python
# scripts/my_bot.py

def run(state, memory):
    """
    Args:
        state: GameState object with query methods
        memory: String (max 100 chars) persisted between frames
    
    Returns:
        String: Updated memory for next frame
    """
    
    # Get my position
    my_x, my_y = state.my_position()
    my_health = state.my_health()
    
    # Find nearest enemy
    enemies = state.enemy_positions()
    if enemies:
        enemy_x, enemy_y = enemies[0]
        
        # Move toward enemy
        if enemy_x < my_x:
            move_left()
        else:
            move_right()
        
        # Aim at enemy
        dx = enemy_x - my_x
        dy = enemy_y - my_y
        
        if abs(dx) > 50:  # Close enough to shoot
            shoot()
    
    # Jump if on ground
    if state.my_velocity()[1] == 0:
        jetpack()
    
    return memory
```

### Available Helper Functions

**Movement**:
```python
jetpack()         # Activate jetpack (upward thrust)
move_left()       # Move left
move_right()      # Move right
```

**Aiming**:
```python
aim_up()          # Rotate gun up
aim_down()        # Rotate gun down
aim_left()        # Rotate gun left
aim_right()       # Rotate gun right
```

**Actions**:
```python
shoot()           # Fire weapon
reload()          # Reload current gun
switch_weapon()   # Switch to other gun
```

**State Queries**:
```python
state.my_position()        # → (x, y)
state.my_velocity()        # → (vx, vy)
state.my_health()          # → health (0-200)
state.my_fuel()            # → fuel (0-100)
state.my_aim_angle()       # → angle in radians

state.enemy_positions()    # → [(x, y), ...] sorted by distance
state.enemy_count()        # → int
state.bullet_positions()   # → [(x, y, vx, vy, damage), ...]
state.gun_spawn_positions()# → [(x, y, weapon_id), ...]
```

**Utilities**:
```python
cos(angle)        # Math.cos
sin(angle)        # Math.sin
pi()              # Math.pi
now()             # Current time (seconds)
rand()            # Random float [0, 1)
```

### Bot Execution Flow

1. `Bot.__init__()` validates and imports script
2. Helper functions injected into script namespace
3. Each frame: `bot.update_state()` → `bot.get_action()`
4. Script's `run()` called with current state
5. Helper calls populate action buffer
6. Action buffer sent to server

### Example Bots

**Random Bot** (`random_bot.py`):
```python
def run(state, memory):
    if rand() > 0.5:
        move_right()
    else:
        move_left()
    
    if rand() > 0.7:
        jetpack()
    
    if rand() > 0.8:
        shoot()
    
    return memory
```

**Aggressive Bot** (`simple_bot.py`):
```python
def run(state, memory):
    enemies = state.enemy_positions()
    
    if enemies:
        ex, ey = enemies[0]  # Closest enemy
        mx, my = state.my_position()
        angle = state.my_aim_angle()
        
        # Move toward enemy
        if ex > mx + 50:
            move_right()
        elif ex < mx - 50:
            move_left()
        
        # Aim and shoot
        target_angle = atan2(ey - my, ex - mx)
        if abs(angle - target_angle) < 0.2:
            shoot()
        elif angle < target_angle:
            aim_up() if ey < my else aim_right()
        else:
            aim_down() if ey > my else aim_left()
    
    return memory
```

---

## Map System

### Map File Format

Maps consist of **two files**:

1. **Collision Map**: `{map_name}.npy` (NumPy binary)
   - 2D array of int32
   - 1 = passable, 0 = solid obstacle
   - Grid size: 10×10 pixel cells

2. **Spawn Points**: `{map_name}_spawns.json` (JSON)
   - Array of `[x, y, weapon_id]`

### Map Editor Usage

**Launch Map Editor**:
```bash
python map_editor.py
```

**Controls**:
- **Left-click + drag**: Draw obstacles (solid terrain)
- **Right-click + drag**: Erase obstacles
- **W**: Place weapon spawn (cycles through weapons)
- **S**: Save current map
- **L**: Load existing map
- **C**: Clear map
- **SPACE**: Test play

**Saving Maps**:
1. Draw terrain with mouse
2. Press 'W' to place weapon spawns
3. Press 'S' and enter map name
4. Files saved to `maps/` directory

### Creating Maps Programmatically

```python
# create_maps.py example
import numpy as np

def create_platform_map():
    # 80×60 grid (800×600 pixels with 10px cells)
    collision_map = np.ones((60, 80), dtype=np.int32)
    
    # Ground
    collision_map[55:60, :] = 0
    
    # Platforms
    collision_map[40:42, 10:30] = 0  # Left platform
    collision_map[40:42, 50:70] = 0  # Right platform
    
    # Save
    np.save("maps/platform_map.npy", collision_map)
    
    # Weapon spawns
    spawns = [
        [150, 350, 3],   # M14 sniper
        [650, 350, 11],  # SAW
        [400, 500, 0]    # AK47
    ]
    
    with open("maps/platform_map_spawns.json", 'w') as f:
        json.dump(spawns, f, indent=2)
```

### Loading Maps

In `config.py`:
```python
DEFAULT_MAP = "catacombs"  # Name without .npy extension
```

Server loads map in `server.py`:
```python
def load_map(self, map_name):
    collision_map = np.load(f"maps/{map_name}.npy")
    gun_spawner.initialize_map(map_name)  # Loads spawns
```

---

## Visual Effects

### Muzzle Flash System

Located in `weapon_effects.py`:

```python
class MuzzleFlash:
    def __init__(self, x, y, angle, weapon_id):
        self.lifetime = 0.05  # 50ms flash
        
        # Weapon-specific colors
        if weapon_id in [3, 5]:  # Snipers
            self.color = (255, 255, 150)  # Bright yellow
            self.size = 25
        elif weapon_id in [15]:  # Rockets
            self.color = (255, 100, 0)    # Orange
            self.size = 30
        else:
            self.color = (255, 200, 0)    # Standard yellow
            self.size = 15
```

**Triggered when**:
- Player's `shooting` flag changes from 0 → 1
- Positioned at gun barrel tip based on weapon type

### Particle System

```python
class Particle:
    def __init__(self, x, y, vx, vy, color, size, lifetime):
        self.vx = vx  # Velocity spreads outward
        self.vy = vy
        self.lifetime = 0.3  # Fades over 300ms
    
    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.lifetime -= dt
        
        # Alpha fade
        alpha = int(255 * (self.lifetime / self.max_lifetime))
```

**Used for**:
- Bullet impact sparks
- Explosion debris
- Grenade gas clouds

### Weapon Rendering

Weapons rotate around the player character:

```python
def draw_gun(screen, x, y, angle, gun, player_radius):
    # Position gun relative to player center
    gun_offset = player_radius + 10
    gun_x = x + gun_offset * cos(angle)
    gun_y = y + gun_offset * sin(angle)
    
    # Rotate sprite
    rotated = pygame.transform.rotate(gun_sprite, -angle * 180 / pi)
    screen.blit(rotated, (gun_x, gun_y))
```

---

## Development Workflow

### 1. Setting Up Development Environment

**Install Dependencies**:
```bash
pip install pygame numpy
```

**Project Structure**:
```
CodeWars_Version_6/
├── server.py           # Run server first
├── game.py             # Run clients
├── config.py           # Modify settings here
├── assets/             # Add sprites here
├── maps/               # Add maps here
└── scripts/            # Add bots here
```

### 2. Running Locally

**Terminal 1 (Server)**:
```bash
python server.py
```
Output shows server IP (e.g., `10.51.19.103:5555`)

**Terminal 2+ (Clients)**:
```bash
python game.py
```

### 3. Testing Workflow

**Quick Test with Bots**:
1. Edit `config.py`:
   ```python
   ENABLE_KEYBOARD_PLAYER = True
   BOT_SCRIPTS = ["random_bot", "debug_bot"]
   ```
2. Run `python game.py` once
3. Keyboard player + 2 bots spawn

**Map Testing**:
1. Create map: `python map_editor.py`
2. Save as "test_map"
3. Set `DEFAULT_MAP = "test_map"` in `config.py`
4. Restart server

### 4. Debugging

**Print Server State**:
```python
# In server.py run_game() loop
print(f"Player 0: pos=({self.world_data[0,1]}, {self.world_data[0,2]})")
```

**Print Bot Decisions**:
```python
# In scripts/helpers.py
def shoot():
    print(f"Bot shooting! State: {state.my_position()}")
    _action_buffer[7] = True
```

**Check Network Traffic**:
```python
# In client.py send()
print(f"Sent {len(client_msg)} bytes, received {len(reply)} bytes")
```

### 5. Version Control

**Key Branches**:
- `main`: Stable releases
- `dev`: Active development
- `feature/*`: New features

**Ignore Files** (`.gitignore`):
```
__pycache__/
*.pyc
*.npy.backup
```

---

## Extending the Game

### Adding a New Weapon

**Step 1**: Define weapon stats in `config.py`:
```python
WEAPON_STATS[16] = {
    "name": "Laser Rifle",
    "damage": 25,
    "accuracy": 0,
    "reload_time": 1.5,
    "melee": 20,
    "rpf": 1,
    "effective_range": 2000,
    "dual_wielding": False,  # Set True for Mini Militia-style dual wielding
    "rate_of_fire": 0.3,
    "magazine_capacity": 50,
    "ammo_given": 200,
    "sprite_file": "laser_rifle.png",
    "bullet_speed": 100,
}
```

**Step 2**: Add sprite to `assets/guns/laser_rifle.png`

**Step 3**: (Optional) Custom bullet sprite:
```python
# In weapon_renderer.py
self.weapon_bullet_sprites[16] = "laser_beam.png"
```

**Step 4**: Add to spawn points:
```json
// In maps/your_map_spawns.json
[400, 300, 16]
```

### Adding a New Game Mode

**Step 1**: Add mode config:
```python
# config.py
GAME_MODE = "deathmatch"  # or "capture_the_flag", "team_battle"
RESPAWN_TIME = 3.0
SCORE_LIMIT = 50
```

**Step 2**: Implement in server:
```python
# server.py
def check_win_condition(self):
    if self.game_mode == "deathmatch":
        for player_id in range(8):
            if self.player_scores[player_id] >= SCORE_LIMIT:
                return player_id
    return None
```

**Step 3**: Update UI in `game.py`:
```python
def draw_scoreboard(self):
    for i, score in enumerate(self.player_scores):
        text = f"Player {i}: {score} kills"
        self.screen.blit(...)
```

### Adding Environmental Hazards

**Step 1**: Extend world_data or add new data structure:
```python
# server.py
self.hazard_zones = [
    {"x": 400, "y": 300, "radius": 50, "damage": 5},  # Lava pool
]
```

**Step 2**: Check collision each frame:
```python
def apply_hazard_damage(self):
    for hazard in self.hazard_zones:
        for player_id in range(8):
            if self.world_data[player_id, 0] == 0:
                continue
            
            px, py = self.world_data[player_id, 1:3]
            distance = np.sqrt((px - hazard["x"])**2 + (py - hazard["y"])**2)
            
            if distance < hazard["radius"]:
                self.world_data[player_id, 7] -= hazard["damage"]
```

**Step 3**: Render in client:
```python
# game.py
def draw_hazards(self):
    for hazard in self.hazards:
        pygame.draw.circle(self.screen, (255, 0, 0), 
                          (hazard["x"], hazard["y"]), 
                          hazard["radius"])
```

### Adding Power-Ups

**Step 1**: Similar to gun spawns, create power-up system:
```python
# powerup_spawner.py
POWERUP_TYPES = {
    0: {"name": "Health Pack", "health": 50},
    1: {"name": "Speed Boost", "duration": 10, "multiplier": 1.5},
    2: {"name": "Damage Boost", "duration": 5, "multiplier": 2.0},
}
```

**Step 2**: Track active power-ups per player:
```python
# server.py
self.player_powerups = [{} for _ in range(8)]

def apply_powerup(self, player_id, powerup_id):
    powerup = POWERUP_TYPES[powerup_id]
    self.player_powerups[player_id] = {
        "type": powerup_id,
        "expires_at": time.time() + powerup["duration"]
    }
```

### Custom Bot Helpers

Add new helper functions for bot scripts:

```python
# scripts/helpers.py
def nearest_health_pack():
    """Find closest health pack position"""
    healthpacks = state.healthpack_positions()
    if not healthpacks:
        return None
    
    my_x, my_y = state.my_position()
    closest = min(healthpacks, key=lambda p: 
                  (p[0] - my_x)**2 + (p[1] - my_y)**2)
    return closest

def is_safe_position(x, y):
    """Check if position has no nearby enemies"""
    enemies = state.enemy_positions()
    for ex, ey in enemies:
        if (ex - x)**2 + (ey - y)**2 < 100**2:
            return False
    return True
```

---

## Performance Optimization

### Current Bottlenecks

1. **Network**: ~5KB sent to each client every frame (60 FPS)
2. **Physics**: Collision checks for 8 players + 40 bullets + jetpack calculations
3. **Rendering**: Drawing animated character sprites with transparency and weapon overlays

### Optimization Strategies

**Network Compression**:
```python
# Use delta compression - only send changed values
def get_world_delta(self, prev_world):
    delta_mask = (self.world_data != prev_world)
    compressed = np.packbits(delta_mask).tobytes()
    return compressed + changed_values.tobytes()
```

**Spatial Hashing for Collisions**:
```python
# Instead of checking all bullets vs all obstacles
def get_nearby_cells(self, x, y, radius):
    cells = set()
    for dx in range(-radius, radius+1):
        for dy in range(-radius, radius+1):
            cells.add((x//CELL_SIZE + dx, y//CELL_SIZE + dy))
    return cells
```

**Sprite Caching**:
```python
# Pre-rotate sprites at initialization
self.rotated_sprites = {}
for angle in range(0, 360, 5):  # Every 5 degrees
    self.rotated_sprites[angle] = pygame.transform.rotate(sprite, angle)
```

---

## Troubleshooting

### Common Issues

**"Connection refused" error**:
- Check `SERVER_HOST` in `config.py` matches server IP
- Ensure server is running first
- Verify firewall allows port 5555

**Players falling through ground**:
- Collision map has 1s (passable) where ground should be
- Use map editor to paint solid terrain (0s)

**Gun not appearing**:
- Check sprite file exists in `assets/guns/`
- Verify filename matches `sprite_file` in `WEAPON_STATS`
- Ensure PNG has transparency (RGBA)

**Bot script crashes**:
- Check for forbidden imports/classes
- Ensure `run()` function exists
- Verify memory string stays under 100 chars

**Lag/stuttering**:
- Reduce `MAX_BULLET_DISTANCE` in config
- Lower number of active bots
- Check network bandwidth

---

## Code Style Guidelines

### Python Conventions

- **PEP 8** for formatting (4-space indents)
- **Type hints** for new functions:
  ```python
  def calculate_damage(distance: float, max_damage: int) -> float:
  ```
- **Docstrings** for public methods:
  ```python
  def respawn(self, player_id: int, delay: float = 0.0) -> None:
      """
      Respawn a player after delay seconds.
      
      Args:
          player_id: Index of player (0-7)
          delay: Seconds to wait before respawn
      """
  ```

### Naming Conventions

- **snake_case** for functions/variables: `player_health`, `get_bullet_position()`
- **PascalCase** for classes: `GunSpawner`, `WeaponRenderer`
- **UPPER_CASE** for constants: `MAX_HEALTH`, `BULLET_SPEED`

### Comments

- **Inline** for complex logic:
  ```python
  # Normalize to [-π, π] range
  angle = (angle + math.pi) % (2 * math.pi) - math.pi
  ```
- **Section headers** for file organization:
  ```python
  # =============================================================================
  # PHYSICS SETTINGS
  # =============================================================================
  ```

---

## Testing

### Manual Testing Checklist

**Core Gameplay (Mini Militia Features)**:
- [ ] Player movement (A/D keys)
- [ ] Jetpack flight (W key + fuel consumption + recharge)
- [ ] Aiming (arrow keys - 360° rotation)
- [ ] Shooting (spacebar)
- [ ] Reloading (R key + auto-reload)
- [ ] Gun switching (S key - dual wielding)
- [ ] Gun pickup from spawn points
- [ ] Dual gun inventory (carry 2 guns)
- [ ] Damage dealt and received
- [ ] Death and respawn mechanics
- [ ] Gravity and physics feel

**Multiplayer**:
- [ ] 2+ players can connect
- [ ] Players see each other
- [ ] Bullets hit other players
- [ ] Gun pickups work correctly for all players
- [ ] Disconnection handled gracefully

**Bot System**:
- [ ] Bot connects and moves
- [ ] Bot can shoot and hit targets
- [ ] Bot respawns after death
- [ ] Multiple bots can coexist

### Automated Testing (Future)

```python
# test_weapons.py
import unittest
from weapons import get_weapon

class TestWeapons(unittest.TestCase):
    def test_gun_shoot(self):
        gun = get_weapon(0)  # AK47
        initial_ammo = gun.current_ammo
        gun.shoot()
        self.assertEqual(gun.current_ammo, initial_ammo - 1)
    
    def test_gun_reload(self):
        gun = get_weapon(1)  # Desert Eagle
        gun.current_ammo = 0
        gun.reload()
        self.assertEqual(gun.current_ammo, gun.magazine_capacity)
```

---

## Future Roadmap

### Planned Features

1. **Team Battles**: Red vs Blue teams with team scoring
2. **Capture the Flag**: Objective-based gameplay
3. **Leaderboards**: Persistent stats tracking
4. **Spectator Mode**: Watch ongoing games
5. **Replay System**: Record and playback matches
6. **Custom Skins**: Player and weapon customization
7. **Sound Effects**: Gunfire, explosions, impacts
8. **Mini-Map**: Real-time tactical overview
9. **Equipment Slots**: Grenades, armor, gadgets
10. **Ranked Matchmaking**: Skill-based player matching

### Technical Improvements

- **WebSocket support** for better network performance
- **Client-side prediction** for reduced perceived latency
- **Interpolation** for smoother movement
- **Anti-cheat** mechanisms
- **Server browser** for multiple game instances
- **Admin commands** for server management
- **Logging system** for debugging and analytics

---

## Contributing

### Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and test thoroughly
4. Commit with clear messages: `git commit -m "Add laser rifle weapon"`
5. Push and create pull request

### Pull Request Guidelines

- **Describe changes** clearly in PR description
- **Test on multiple clients** (keyboard + bots)
- **Update documentation** if adding features
- **Follow code style** guidelines
- **No breaking changes** without discussion

---

## Resources

### Documentation
- [Pygame Documentation](https://www.pygame.org/docs/)
- [NumPy Documentation](https://numpy.org/doc/)
- [Python Socket Programming](https://docs.python.org/3/library/socket.html)

### Learning Materials
- **Game Networking**: [Gaffer on Games](https://gafferongames.com/)
- **2D Collision**: [MDN 2D Collision Detection](https://developer.mozilla.org/en-US/docs/Games/Techniques/2D_collision_detection)
- **Pygame Tutorials**: [RealPython Pygame Primer](https://realpython.com/pygame-a-primer/)

---

## License

This project is for educational purposes. See `LICENSE` file for details.

---

## Contact

For questions or suggestions, contact the development team or open an issue on the repository.

**Happy Coding! 🎮🚀**
