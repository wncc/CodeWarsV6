# Overview

[What’s the game about?](https://www.notion.so/What-s-the-game-about-c9b99d4fa18b831c8a0c010e61bb1dac?pvs=21) 

[What are you supposed to do?](https://www.notion.so/What-are-you-supposed-to-do-8e199d4fa18b82518e25015e278970d7?pvs=21) 

# What’s the game about?

---

Welcome to CodeWars V6! This year, we are dropping straight into a fast-paced, 2D multiplayer deathmatch. Inspired by the classic Catacombs map from Mini Militia, your script will control a single, highly mobile combat bot in a free-for-all arena.

The objective is simple: **accumulate the highest kill score before the match ends.** The battlefield is an 800x500 pixel world filled with solid obstacles, platforms, and open airspace. You'll need to navigate the terrain using your jetpack, scavenge for weapon spawns, hunt down enemy bots, and survive the crossfire. If you die, you will respawn at a random location after a brief delay.

## **Game Mechanics**

![image.png](attachment:5afd6928-65b5-4c7f-8679-aeed00a54bdb:image.png)

### **Your Bot & Resources**

You are fully responsible for your bot's survival and combat effectiveness. You must manage:

- **Health:** You spawn with 200 HP, and die when your HP drops to zero.
- **Jetpack Fuel:** You have a capacity of 100 fuel units, allowing you to fly between platforms and gain the high ground.
- **Weapons:** You drop in empty-handed. You must navigate to find weapon spawn points to pick up guns.
- **Loadout:** You can carry and dual-wield up to 2 of the 15 available weapons (snipers, shotguns, assault rifles, etc.), keeping track of your current magazine and reserve ammo.

Game speed can be changed while testing using arrow keys (Up-increase speed up to 7x or Down-decrease speed)

### **Health**

- You start with 200 HP.
- If your bot's **HP drops to 0** from enemy fire, it dies and respawns at a random location after a brief delay.

### Jetpack

- Your bot has a jetpack with a maximum capacity of **100 fuel units**, letting you fly between platforms and claim the high ground.
- Fuel depletes at **0.5 units per frame** while thrusting upward and recharges at **0.5 units per frame** when grounded.
- If your fuel hits 0, the jetpack won't activate until it recharges.

### Weapons

- You start with both a Primary Weapon and a Secondary Weapon
    - **Primary Weapon:** Picked randomly from: (Desert Eagle - 40%, Uzi - 30%, or Tec-9 - 30%).
    - **Secondary Weapon:**  a Golden Deagle.
- There are **15** different weapons available (e.g., AK-47, snipers, shotguns, SMGs).
- You can carry and dual-wield up to **2 weapons simultaneously**. Manage your active weapon's magazine and reload using reserve ammo.

## **How the Game Progresses**

The game runs at **60 Frames Per Second (FPS)**. Every single frame, your script is evaluated, and you can issue multiple simultaneous commands. You can move left, thrust your jetpack upward, aim your gun, and shoot all at the exact same time.

## **Game End Conditions**

Each CodeWars V6 match lasts exactly **6 minutes**. Focus on combat efficiency, movement, and survival. When time runs out, the bot with the **highest kill score** wins.

# What are you supposed to do?

---

You are required to implement a single logic function, `run(state, memory)`, inside your team's Python script. This function acts as your bot's sensory input and decision-making centre, and it executes every single frame.

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

# **Built-in Helper Functions**

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

# Attributes Inside `state`

---

The `state` object passed into your `run(state, memory)` function is your bot's only way to **see the arena**. It's an instance of the `GameState` class and provides a **read-only snapshot** of the world at the current frame.

Below is the complete reference for every method you can call on `state` to gather intel.

---

### Sensor System

**Crucial mechanic:** Your bot lacks a global view of the arena.

You are restricted by a **Sensor Radius**. You can only detect enemies, bullets, grenades, and gun spawns if they are physically within this radius.

- If you are unarmed, your base sensor radius is **100** **pixels**.
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

Use this to attempt **evasive manoeuvres**.

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

- `state.time_remaining()`:
    - **Returns:** The time remaining for the game to end.
- `state.leaderboard()`:
    - **Returns** : A list of dictionaries: `{ "rank", "id", "kills", "deaths", "kd_delta"}`
    - **Description** : Returns the current leaderboard of the match.

---

### **Common Mistakes That Will Fail Validation**

| Mistake | Reason |
| --- | --- |
| Adding any `import` or `from … import` statement | All imports are **forbidden**. |
| Missing **`run`** function | The script **must** contain a function named `run`. |
| Having functions other than `run` | The script can contain only **one** function, ie. `run`. |
| Using **global variables** to **persist state** | There are **no persistent globals** between frames. Use the `memory` string parameter instead. Any global state is reset each time the module is re-executed. |
| Letting `memory` exceed **100 characters** | Anything beyond that is truncated. Structure your memory string accordingly. |

---

- If the team **meets all conditions**, it **passes validation**. Otherwise, it fails and loses the match.

## **Goal**

- Write an intelligent bot script that maximises kills and minimises deaths through strategic movement, aiming, and weapon management.
- **Optimise** your strategy to counter enemy movements effectively.

You can use the provided **helper functions** or create your own logic to optimise your strategy!