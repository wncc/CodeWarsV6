# scripts/core/helpers.py

import numpy as np
import random
import time
import math
import config
from config import BULLET_VISUAL_RADIUS
from config import WEAPON_STATS as WEAPONS

# =========================
# Action Buffer (internal)
# =========================

_action_buffer = np.zeros(14, dtype=bool)


def _reset_action_buffer():
    _action_buffer[:] = False


def _get_action():
    return _action_buffer.copy()


# =========================
# Primitive Controls
# (match existing 14-bit layout)
# =========================
# [0]=jetpack
# [1]=left
# [2]=right
# [3]=aim_up
# [4]=aim_down
# [5]=aim_left
# [6]=aim_right
# [7]=shoot
# [8]=reload
# [9]=switch
# [10]=throw_grenade
# [11]=change_grenade_type
# [12]=pickup
# [13]=kneel


def jetpack():
    _action_buffer[0] = True


def move_left():
    _action_buffer[1] = True


def move_right():
    _action_buffer[2] = True


def aim_up():
    _action_buffer[3] = True


def aim_down():
    _action_buffer[4] = True


def aim_left():
    _action_buffer[5] = True


def aim_right():
    _action_buffer[6] = True


def shoot():
    _action_buffer[7] = True


def reload():
    _action_buffer[8] = True


def switch_weapon():
    _action_buffer[9] = True


def throw_grenade():
    _action_buffer[10] = True


def change_grenade_type():
    _action_buffer[11] = True


def pickup():
    _action_buffer[12] = True


def kneel():
    _action_buffer[13] = True


# =========================
# Read-Only Game State
# =========================


class GameState:
    def __init__(self, player_id, world_data, gun_spawns, medkit_spawns, grenade_data, inventory_data, collision_map, grid_size, gas_data=None, leaderboard_data=None, time_remaining=None):

        self.__id = player_id
        self.__world = world_data.copy()
        self.__world.setflags(write=False)
        self.__gun_spawns = gun_spawns
        self.__medkit_spawns = medkit_spawns
        self.__grenade_data = grenade_data
        self.__inventory_data = inventory_data
        self.__collision_map = collision_map
        self.__grid_size = grid_size
        self.__grid_h, self.__grid_w = collision_map.shape
        self.__gas_data = gas_data if gas_data is not None else np.zeros((0, 4), dtype=np.float64)
        self.__leaderboard_data = leaderboard_data if leaderboard_data is not None else np.zeros((0, 4), dtype=np.int32)
        self.__time_remaining = float(time_remaining) if time_remaining is not None else 0.0

    # ---- Match Info ----
    def time_remaining(self):
        """
        Returns the number of seconds remaining in the current match.
        Returns 0.0 if the match timer has not started or has ended.
        """
        return self.__time_remaining

    # ---- Self ----
    def my_position(self):
        me = self.__world[self.__id]
        return float(me[1]), float(me[2])

    def my_health(self):
        return float(self.__world[self.__id, 7])

    def my_fuel(self):
        return float(self.__world[self.__id, 6])

    def my_score(self):
        return float(self.__world[self.__id, 8])

    def my_ammo(self):
        return float(self.__world[self.__id, 9]), float(self.__world[self.__id, 10])

    def my_aim_angle(self):
        """
        Returns the angle (radians) the bot is currently aiming.
        0 = right
        π/2 = down
        -π/2 = up
        """

        return float(self.__world[self.__id, 3])

    def _sensor_radius(self):
        gun = self.my_gun()

        if gun is None:
            return BULLET_VISUAL_RADIUS

        scope = config.get_weapon_stat(gun, "scope")

        if scope is None:
            return BULLET_VISUAL_RADIUS

        return scope * BULLET_VISUAL_RADIUS

    def enemy_positions(self):

        radius = self._sensor_radius()
        px, py = self.my_position()

        enemy_data = []

        for i in range(8):
            if i == self.__id:
                continue

            if self.__world[i, 0] != 1:
                continue

            ex = float(self.__world[i, 1])
            ey = float(self.__world[i, 2])
            enemy_health = float(self.__world[i, 7])
            dist = math.sqrt((ex - px)**2 + (ey - py)**2)

            if dist <= radius:
                gun1_id, gun2_id, current_slot = self.__inventory_data[i]
                if int(current_slot) == 0:
                    current_gun = int(gun1_id) if gun1_id >= 0 else None
                    secondary_gun = int(gun2_id) if gun2_id >= 0 else None
                else:
                    current_gun = int(gun2_id) if gun2_id >= 0 else None
                    secondary_gun = int(gun1_id) if gun1_id >= 0 else None

                current_grenade = int(self.__grenade_data[i, 0])

                enemy_data.append({
                    "id": i,
                    "x": ex,
                    "y": ey,
                    "health": enemy_health,
                    "current_gun": current_gun,
                    "secondary_gun": secondary_gun,
                    "current_grenade": current_grenade,
                    "distance": dist,
                })

        return enemy_data

    def all_players(self):

        radius = self._sensor_radius()
        px, py = self.my_position()

        players = []

        for i in range(8):

            if self.__world[i, 0] != 1:
                continue

            ex = float(self.__world[i, 1])
            ey = float(self.__world[i, 2])

            dist = math.sqrt((ex - px)**2 + (ey - py)**2)

            if dist <= radius:

                players.append({
                    "id": i,
                    "x": ex,
                    "y": ey,
                    "health": float(self.__world[i, 7]),
                })

        return players

    def my_gun(self):
        """
        Returns the weapon ID of the gun currently held by the player.
        Returns None if the player has no gun.
        """
        gun1_id, gun2_id, current_slot = self.__inventory_data[self.__id]

        if current_slot == 0:
            return int(gun1_id) if gun1_id >= 0 else None
        else:
            return int(gun2_id) if gun2_id >= 0 else None

    def local_map(self, radius):
        """
        Returns a square slice of the collision map centered on the bot.

        radius = number of cells around the bot
        returned size = (2*radius + 1) x (2*radius + 1)

        0 = obstacle
        1 = empty

        """
        radius = min(radius, self._sensor_radius())
        size = 2 * radius + 1

        px, py = self.my_position()

        grid_x = int(px / self.__grid_size)
        grid_y = int(py / self.__grid_size)

        result = [[0 for _ in range(size)] for _ in range(size)]

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):

                map_x = grid_x + dx
                map_y = grid_y + dy

                local_x = dx + radius
                local_y = dy + radius

                if 0 <= map_x < self.__grid_w and 0 <= map_y < self.__grid_h:
                    result[local_y][local_x] = int(self.__collision_map[map_y, map_x])

        return result

    def get_weapon_stat(self, weapon_name, stat):
        """
        Returns a specific stat of a weapon.

        Example:
            get_weapon_stat("sniper", "damage")
        """

        weapon = WEAPONS.get(weapon_name)

        if weapon is None:
            return None

        return weapon.get(stat)

    def bullet_positions(self):

        radius = self._sensor_radius()
        px, py = self.my_position()

        bullets = []

        for i in range(8, 48):

            if self.__world[i, 0] != 1:
                continue

            bx = float(self.__world[i, 1])
            by = float(self.__world[i, 2])

            dist = math.sqrt((bx - px)**2 + (by - py)**2)

            if dist <= radius:

                angle = self.__world[i, 3]
                speed = self.__world[i, 4]

                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed

                bullets.append({
                    "x": bx,
                    "y": by,
                    "vx": vx,
                    "vy": vy
                })

        return bullets

    def saw_bullets_in_view(self):
        """
        Returns active SAW bullets within the bot's sensor/view radius.
        """
        radius = self._sensor_radius()
        px, py = self.my_position()
        saw_weapon_id = getattr(config, "SAW_WEAPON_ID", 11)

        saw_bullets = []

        for i in range(8, 48):
            if self.__world[i, 0] != 1:
                continue

            weapon_id = int(self.__world[i, 10])
            if weapon_id != saw_weapon_id:
                continue

            bx = float(self.__world[i, 1])
            by = float(self.__world[i, 2])
            dist = math.sqrt((bx - px) ** 2 + (by - py) ** 2)

            if dist <= radius:
                angle = float(self.__world[i, 3])
                speed = float(self.__world[i, 4])
                saw_bullets.append({
                    "x": bx,
                    "y": by,
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "distance": dist,
                    "owner_id": int(self.__world[i, 9]),
                    "slot": i,
                })

        return saw_bullets

    def active_grenades(self):

        radius = self._sensor_radius()
        px, py = self.my_position()

        grenades = []

        for i in range(48, 55):

            if self.__world[i, 0] != 1:
                continue

            gx = float(self.__world[i, 1])
            gy = float(self.__world[i, 2])

            dist = math.sqrt((gx-px)**2 + (gy-py)**2)

            if dist <= radius:

                grenades.append({
                    "x": gx,
                    "y": gy,
                    "vx": float(self.__world[i, 4]),
                    "vy": float(self.__world[i, 5]),
                    "type": int(self.__world[i, 10])
                })

        return grenades

    def gun_spawns(self):

        radius = self._sensor_radius()
        px, py = self.my_position()

        spawns = []

        for spawn in self.__gun_spawns:

            x, y, weapon_id, active = spawn

            if active != 1:
                continue

            dist = math.sqrt((x-px)**2 + (y-py)**2)

            if dist <= radius:

                spawns.append({
                    "x": float(x),
                    "y": float(y),
                    "weapon_id": int(weapon_id)
                })

        return spawns

    def medkit_spawns(self):

        radius = self._sensor_radius()
        px, py = self.my_position()

        spawns = []

        for spawn in self.__medkit_spawns:

            x, y, active = spawn

            if active != 1:
                continue

            dist = math.sqrt((x-px)**2 + (y-py)**2)

            if dist <= radius:

                spawns.append({
                    "x": float(x),
                    "y": float(y)
                })

        return spawns
    
    def player_markers(self):
        """
        Helper for bots: return angle and distance to ALL active players on the map.
        No sensor-radius or quadrant restriction — full map visibility.

        Output format:
        [
            {"id": int, "angle": float, "distance": float},
            ...
        ]

        angle is radians from bot -> player using atan2(dy, dx).
        0 means right, pi/2 means down, -pi/2 means up.
        """
        px, py = self.my_position()
        me_id = self._GameState__id
        world = self._GameState__world

        markers = []

        for i in range(8):
            if i == me_id:
                continue
            if world[i, 0] != 1:
                continue

            ex = float(world[i, 1])
            ey = float(world[i, 2])

            dx = ex - px
            dy = ey - py

            markers.append({
                "id": i,
                "angle": math.atan2(dy, dx),
                "distance": math.sqrt(dx * dx + dy * dy),
            })

        return markers

    def my_grenades(self):
        """
        Returns the bot's grenade counts.
        Returns a dictionary with grenade types and their counts.
        """
        selected_type, frag_count, proxy_count, gas_count = self.__grenade_data[self.__id]

        return {
            "selected_type": int(selected_type),  # 1=frag, 2=proxy, 3=gas
            "frag": int(frag_count),
            "proxy": int(proxy_count),
            "gas": int(gas_count)
        }

    def distance_to_obstacle(self, theta, max_distance=2000.0, step=2.0):
        """
        raycasting function
        """

        x, y = self.my_position()

        dx = math.cos(theta)
        dy = math.sin(theta)

        distance = 0.0

        while distance < max_distance:
            check_x = x + dx * distance
            check_y = y + dy * distance

            # Convert to grid cell
            grid_x = int(check_x / self.__grid_size)
            grid_y = int(check_y / self.__grid_size)

            # Out of bounds counts as obstacle
            if (grid_x < 0 or grid_x >= self.__grid_w or
                grid_y < 0 or grid_y >= self.__grid_h):
                return distance

            # Check obstacle
            if self.__collision_map[grid_y, grid_x] == 0:
                return distance

            distance += step

        return max_distance

    def gas_clouds(self):
        """
        Returns active gas clouds within the bot's sensor radius.
        Each cloud has: x, y, radius, duration, distance from bot
        """
        radius = self._sensor_radius()
        px, py = self.my_position()

        clouds = []

        for effect in self.__gas_data:
            if len(effect) < 4:
                continue

            gx, gy, cloud_radius, duration = effect

            if duration <= 0:
                continue

            dist = math.sqrt((gx - px)**2 + (gy - py)**2)

            if dist <= radius:
                clouds.append({
                    "x": float(gx),
                    "y": float(gy),
                    "radius": float(cloud_radius),
                    "duration": float(duration),
                    "distance": dist
                })

        return clouds

    def leaderboard(self):
        """
        Returns the current match leaderboard (top 8 players), sorted by kills.

        Each entry is a dictionary with:
            - "rank":    1-based position on the leaderboard
            - "id":      player index (0-7)
            - "kills":   total kills
            - "deaths":  total deaths
            - "kd_delta": kills minus deaths

        Returns an empty list if leaderboard data is unavailable.
        """
        board = self.__leaderboard_data
        if board is None or len(board) == 0:
            return []

        entries = []
        for rank, row in enumerate(board, start=1):
            if len(row) < 4:
                continue
            player_idx = int(row[0])
            if player_idx < 0:
                continue
            entries.append({
                "rank": rank,
                "id": player_idx,
                "kills": int(row[1]),
                "deaths": int(row[2]),
                "kd_delta": int(row[3]),
            })

        return entries


# TODO: figure out how to make this private
def build_state(player_id, game_world, gun_spawns, medkit_spawns, grenade_data, inventory_data, collision_map, grid_size, gas_data=None, leaderboard_data=None, time_remaining=None):
    return GameState(
        player_id,
        game_world,
        gun_spawns,
        medkit_spawns,
        grenade_data,
        inventory_data,
        collision_map,
        grid_size,
        gas_data,
        leaderboard_data,
        time_remaining
    )


def pickup_gun(state):
    spawns = state.gun_spawns()

    if len(spawns) == 0:
        return False

    px, py = state.my_position()
    closest_spawn = None
    closest_dist = float("inf")

    for spawn in spawns:
        x = spawn["x"]
        y = spawn["y"]
        dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)

        if dist < closest_dist:
            closest_dist = dist
            closest_spawn = spawn

    if closest_spawn is None:
        return False

    if closest_dist <= config.GUN_PICKUP_RADIUS:
        _action_buffer[12] = True
        return True

    return False


def saw_info(state):
    """
    Helper for bots: get SAW bullets currently visible to this player.
    """
    return state.saw_bullets_in_view()


# TODO: medkit positions 
# change grenade hardcoding after integrating medkit 
# grenade cloud thingy 
# change gun radius LUT 
# add saw 
# add dead state functionality

