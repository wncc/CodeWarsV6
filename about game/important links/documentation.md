# Documentation

[1. Code Structure](https://www.notion.so/1-Code-Structure-def99d4fa18b837bb45d014d145d9356?pvs=21) 

[**2. Core Files Overview**](https://www.notion.so/2-Core-Files-Overview-1ec27b31c11b4087a275e1791b3036b4?pvs=21) 

[3. Scripts](https://www.notion.so/3-Scripts-44f99d4fa18b8335bf5a01b614b38518?pvs=21) 

[](https://www.notion.so/32699d4fa18b80cba30bfc2028cbd7d1?pvs=21) 

<aside>
⚠️

> **DISCLAIMER**
> 

This game is not an exact replica of Mini Militia. It features unique mechanics, weapon properties, and gameplay dynamics. Please refer to the documentation below for game-specific details and apply them accordingly.

</aside>

# Weapon Mechanics

**Inventory**

- Maximum weapons per player: `2`
- Default starting weapon: `Desert Eagle (ID 1)`

**Weapon Spawning**

- Spawn interval: `15 seconds`
- Pickup radius: `20 units`

# Weapon Stats

| ID | Name | Damage | Accuracy | Reload Time | Melee | RPF | Range | ROF | Mag | Ammo | Bullet Speed | Scope | Dual |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | AK47 | 45 | 4 | 2.5 | 30 | 1 | 800 | 0.1 | 35 | 250 | 60 | 4.0 | No |
| 1 | Desert Eagle | 20 | 2 | 1.5 | 15 | 1 | 500 | 0.25 | 15 | 75 | 70 | 2.0 | No |
| 2 | Golden Deagle | 30 | 2 | 1.5 | 25 | 1 | 600 | 0.2 | 15 | 75 | 70 | 4.0 | No |
| 3 | M14 | 100 | 0 | 3.0 | 35 | 1 | 1200 | 0.55 | 6 | 36 | 80 | 4.0 | No |
| 4 | M4 | 40 | 2 | 2.5 | 30 | 1 | 1000 | 0.5 | 24 | 300 | 75 | 5.0 | No |
| 5 | M93BA Sniper | 200 | 0 | 3.5 | 35 | 1 | 1500 | 0.8 | 3 | 20 | 100 | 7.0 | No |
| 6 | Magnum | 30 | 1 | 2.5 | 25 | 1 | 650 | 0.6 | 6 | 36 | 75 | 2.0 | No |
| 7 | MP5 | 25 | 5 | 2.0 | 30 | 1 | 700 | 0.06 | 50 | 400 | 65 | 4.0 | Yes |
| 8 | UZI | 25 | 6 | 1.8 | 20 | 1 | 500 | 0.1 | 40 | 400 | 60 | 4.0 | Yes |
| 9 | TEC9 | 25 | 4 | 1.8 | 25 | 1 | 600 | 0.15 | 40 | 400 | 65 | 4.0 | Yes |
| 10 | SPAS-12 | 75 | 10 | 3.5 | 40 | 5 | 325 | 0.75 | 5 | 24 | 55 | 2.0 | No |
| 11 | SAW | 100 | 0 | 5.0 | 35 | 1 | 1000 | 1.25 | 3 | 6 | 3.0 | 4.0 | No |
| 12 | TAVOR | 9 | 2 | 2.0 | 30 | 1 | 750 | 0.12 | 35 | 200 | 70 | 5.0 | No |
| 13 | XM8 | 8 | 3.25 | 2.2 | 30 | 1 | 875 | 0.085 | 30 | 200 | 72 | 5.0 | No |
| 14 | MINIGUN | 30 | 7 | 4.5 | 35 | 1 | 650 | 0.08 | 50 | 200 | 68 | 4.0 | No |
| 15 | ROCKET LAUNCHER | 100 | 10 | 4.0 | 40 | 1 | 1200 | 0.5 | 3 | 12 | 3.0 | 6.0 | No |

## Column Definitions

- **ID:** Unique integer used to identify the weapon in the codebase.
- **Name:** Official display name of the weapon.
- **Damage:** Hit points deducted from a player's 200 HP per bullet hit.
- **Accuracy:** Maximum random angular spread of a fired bullet in degrees. Lower values mean higher precision; 0 is perfectly accurate.
- **Reload Time:** Time in seconds a bot must wait after reloading before it can shoot again.
- **Melee:** Damage dealt when using the weapon in close-range melee.
- **RPF (Rounds per fire)**: The number of projectiles fired each time the weapon shoots once.
- **Range (Effective Range):** Maximum distance at which the weapon remains effective.
- **ROF (Rate of Fire):** Minimum time in seconds between consecutive shots.
- **Mag (Magazine Capacity):** Number of bullets that can be fired before reloading.
- **Ammo Given:** Total reserve ammo granted when the weapon is picked up, excluding the loaded magazine.
- **Bullet Speed:** Pixels a projectile travels per server tick (at 60 ticks/sec), determining how fast it crosses the arena.
- **Scope:** Zoom level or aiming magnification provided by the weapon.
- **Dual:** Whether the weapon can be carried alongside another gun in your two-slot inventory.

# Grenade Stats

| ID | Name | Damage | Blast Radius | Fuse Time | Effect Time | Proxy |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Frag Grenade | 275 | 200 | 3 | 1 | No |
| 2 | Proximity Grenade | 275 | 200 | 5 | 1.5 | Yes |
| 3 | Gas Grenade | 150 | 125 | 2 | 10 | No |

## Column Definitions

- **Damage:** Amount of damage dealt when the grenade explodes.
- **Blast Radius:** Distance from the explosion centre where players take damage.
- **Fuse Time:** Time in seconds before the grenade detonates.
- **Effect Duration:** How long the grenade's effect lasts after activation.
- **Proximity Trigger:** If `True`, the grenade explodes automatically when an enemy comes close.

## 1. Code Structure

- scripts
    - bots
        
        Contains all the bot scripts
        
    - core
        
        bot.py
        
        game_config.py
        
        helpers.py
        
    - map
        
        Handles map structure, environment data, and collision logic
        
- assets
    - characters
        
        Player sprite images and animations
        
    - grenades
        
        Visual assets for grenade objects and effects
        
    - guns
        
        Gun sprites and weapon-related images
        
    - medkit
        
        Images for health pickups
        
    - sounds
        
        Sound effects used during gameplay
        
- maps
    
    Stores map related files and layouts used by the game 
    
- engine
    - audio
        
        Handles audio rendering and sound playback.
        
    - spawners
        
        Manages spawn point logic
        
    - weapons
        
        Responsible for weapon rendering and visual effects
        

config.py

main.py

game.py

server.py

client.py

## **2. Core Files Overview**

| **File** | **Purpose** |
| --- | --- |
| **config.py** | Central configuration file containing all game settings (physics, weapons, network, map data, spawn points, and game mechanics parameters). |
| **main.py** | Entry point for the application - starts the game server and initializes the game loop (note: not found in current search, likely starts server.py). |
| **game.py** | `PlayerClient` class that manages the local game instance, handles pygame rendering, player input, bot AI integration, and communication with the server via the Network class. |
| **server.py** | `Server` class that runs the game server, manages all player connections, simulates physics/collisions, processes weapon/grenade mechanics, and broadcasts world state to all connected clients. |
| **client.py** | `Network` class that handles socket communication between the client and server, sends player input to the server, and receives world state data (player positions, bullets, grenades, etc.). |

## 3. Scripts

- core:
    - bot.py
    - game_config.py
    - helpers.py
- bots:
    - player.py

### 3.1 bot.py

Loads and executes bot AI scripts in a sandboxed environment, validating that scripts only define a `run()` function (no imports/classes), and injects helper functions to control bot actions while managing bot memory and state.

---

### 3.2 game_config

Alternative/secondary configuration file containing engine settings (FPS, debug flags, physics parameters, camera controls, player movement speeds, jetpack mechanics, and per-weapon data) separate from the main config.py.

---

### 3.3 player.py

You are required to implement a single logic function, `run(state, memory)`, inside your team's Python script. This function acts as your bot's sensory input and decision-making centre, and it executes every single frame.

<aside>
⚠️

### **Adding your own script (bot)**

To add your own script (bot), ****create a new bot file under `scripts/bots/` and then tell the game to run it via `config.BOT_SCRIPTS`.

1. Create a new Python file in the repo under: `scripts/bots/your_bot_name.py`
2. Tell the game to launch your bot: Open `config.py` and set/add your script in `BOT_SCRIPTS`.
</aside>

### **Key Points**

- **Write your logic in the function:** `run(state, memory)`
- Use the `state` object to analyse the game and make decisions
- **NO classes or global variables:** You must use the `memory`string for memory persistence between frames.
- **NO imports:** Do not import `os`, `subprocesses`, or any other libraries. Everything you need is already loaded for you.

### **What You Need to Do**

1. **Analyze `state`**
    - The `state` object provides real-time telemetry about the environment.
    - You can use it to check your coordinates, track enemy positions, detect incoming bullets, and use the array provided to choose your next action.
2. **Execute Actions**
    - Based on the data you read, you will call simple action functions to move, aim, shoot, or swap weapons.
3. **Modify `memory` (Optional)**
    - Since the function reruns every frame, you are provided with a `memory` string (up to 100 characters) that you can return at the end of the frame.
    - It will be passed back to your function on the next frame, allowing you to retain your current strategy, destination, or target.

Here is a basic structure for your bot:

```python
def run(state, memory):
  # 1. Read the environment
  my_x, my_y = state.my_position()
  enemies = state.enemy_positions()
  
  # 2. Make decisions and take actions
  if enemies:
      # trigger combat actions
      pass
  
  # Example movement condition
  if my_y > 0:
      # trigger movement/flight actions
      pass
  
  # 3. Return memory for the next frame
  return memory
```

---

### 3.4 helpers

Provides the bot API with control functions (`move_left()`, `shoot()`, `aim_up()`, etc.), state query methods (`my_position()`, `enemy_positions()`, `my_health()`, etc.), and math utilities for bot scripts to read game state and execute actions.

### **Built-in Helper Functions**

### **1. `Movement`**

Control your bot's position and trajectory.

- `jetpack()`: Activate jetpack (upward thrust)
- `move_left()`: Move left
- `move_right()`: Move right

### **2. `Aiming`**

Adjust your gun's aim direction.

- `aim_up()`: Aim upward
- `aim_down()`: Aim downward
- `aim_left()`: Aim left
- `aim_right()`: Aim right

### **3. `Combat`**

Fire, reload, and switch between weapons.

- `shoot()`: Fire your current weapon
- `reload()`: Reload your current weapon
- `switch_weapon()`: Switch to your other weapon ****
- `pickup_gun(state)`:   Pickup a weapon. The current active weapon is replaced.
- `throw_grenade` : Throws the currently selected grenade.
- `change_grenade_type()` : Cycles to the next grenade type in the order Frag, Proximity, Gas
- `kneel()`: Makes the player kneel.
- `saw_info(state)` : Returns information about visible SAW bullets detected by the player's sensors.

### Attributes Inside `state`

---

The `state` object passed into your `run(state, memory)` function is your bot's only way to **see the arena**. It's an instance of the `GameState` class and provides a **read-only snapshot** of the world at the current frame.

Below is the complete reference for every method you can call on `state` to gather intel.

---

### Sensor System

**Crucial mechanic:** Your bot lacks a global view of the arena.

You are restricted by a **Sensor Radius**. You can only detect enemies, bullets, grenades, and gun spawns if they are physically within this radius.

- If you are unarmed, your base sensor radius is **100 pixels**.
- If you are holding a weapon, your sensor radius changes based on the weapon’s scope.

*Keep this in mind when using the World Info methods below!*

---

### 1. Self/Bot Info

Use these methods to check your bot's status and resources.

| Method | Description & Details |
| --- | --- |
| `state.my_position()` | Returns your `(x, y)`pixel coordinates. **Note:** The origin`(0, 0)`is at the top-left of the map. X increases to the right, Y increases downward. |
| `state.my_health()` | Returns your current HP, ranging from`0.0`to`200.0`. If this reaches zero, your bot dies and respawns. |
| `state.my_fuel()` | Returns your jetpack fuel, ranging from`0.0`to`100.0`. Depletes by 0.5 per frame while flying and recharges by 0.5 per frame when grounded. |
| `state.my_score()` | Returns your total kill count for the current match. |
| `state.my_ammo()` | Returns `(current_mag, reserve_ammo)`for your **currently equipped gun only**. If you switch weapons, this updates on the next frame to reflect the new gun. |
| `state.my_aim_angle()` | Returns your current aim angle in radians (`0`=right, `π/2`=down, `-π/2`=up). |
| `state.my_gun()` | Returns the Weapon ID of your currently held gun (or `None` if unarmed). |
| `state._sensor_radius()` | Returns the sensor radius of your current gun, defaults to 30 if you aren’t holding one. |
| `state.get_weapon_stat()` | Returns a specific stat (damage, fire rate, etc.) for a given weapon. |
| `state.my_grenades()` | Returns grenade counts for the player by type |

### 2. Enemy & Player Info

Use these to track your targets.

**Note:** enemy/player methods only return entities currently inside your sensor radius.

- `state.enemy_positions()`
    - **Returns:** A list of `(x, y)` tuples `[(x1, y1), (x2, y2), ...]`
- `state.all_players()`
    - **Returns:** A list of dictionaries of type: `{”id”, “x”, “y”, “health”, “score”}`
    - **Description:** Provides detailed stats on every living player in your sensor radius, **including yourself**.
- `state.player_markers()`
    - **Returns**: A list of dictionaries: `{ "id", "angle", "distance"}`
    - **Description**: Returns angle and distance to all active players on the map. No sensor-radius restriction.

---

### 3. Bullet/Grenade Info

Use these to attempt **evasive manoeuvres**.

- `state.active_grenades()`
    - **Returns:** A list of dictionaries: `{ "x", "y", "vx", "vy", "type" }`, where `type` is the Grenade ID.
    - **Description:** Tracks live grenades within your sensor radius.
- `state.bullet_positions()`
    - **Returns:** A list of dictionaries of type: `{ "x", "y", "vx", "vy" }` .
    - **Description:** Returns the current coordinates and velocities of **all active bullets** flying through your sensor radius, including your own.
- `state.saw_bullets_in_view()`
    - **Returns**: A list of dictionaries of type: `{ "x", "y", "vx", "vy", "distance", "owner_id", "slot" }` .
    - **Description**: Returns all active visible SAW bullets including velocity and owner information.
- `state.gas_clouds()`
    - **Returns**: A list of dictionaries of type: `{ "x", "y", "radius", "duration", "distance"}`
    - **Description**: Returns active gas clouds within the bot's sensor radius.

---

### 4. Gun/Medkit spawns

- `state.gun_spawns()`
    - **Returns:** A list of dictionaries: `{ "x", "y", "weapon_id" }`
    - **Description:** Shows active pick-up-able weapons on the ground within your sensor radius.
- `state.medkit_spawns()`
    - **Returns**: A list of dictionaries: `{ "x", "y"}`
    - **Description**:  Returns nearby medkit spawn locations within the sensor radius.

---

### 5. Map & Environment (Local Grid + Raycasting)

- `state.local_map(radius)`
    - **Returns:** A 2D list (matrix) of integers.
    - **Description:** Returns a square grid of the collision map centred on your bot. Size is `(2*radius + 1) x (2*radius + 1)`.
    - **Note:** The maximum allowed radius is the sensor radius and will be used if the radius exceeds it.
    - **Values:** `0` = obstacle/wall, `1` = empty passable space.
- `state.distance_to_obstacle(theta, max_distance, step)`
    - **Returns:** `float` *(distance in pixels)*
    - **Description:** Acts like your bot's **radar**. It tells you how far away the nearest solid wall or map boundary is in a specific direction.
    - **Parameters:**
        - `theta` → direction angle in **radians**
            - `0` = right
            - `π/2` = down
            - `π` = left
            - `3π/2` = up
        - `max_distance` *(optional)* → how far the ray travels before stopping *(default 2000)*
        - `step` *(optional)* → precision of the calculation in pixels *(default 2.0)*

---

### 6. Match Info

- `state.time_remaining()`
    - **Returns:** The time remaining for the game to end.
- `state.leaderboard()`
    - **Returns** : A list of dictionaries: `{ "rank", "id", "kills", "deaths", "kd_delta"}`
    - **Description** : Returns the current leaderboard of the match.