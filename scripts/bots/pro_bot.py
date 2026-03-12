# scripts/pro_bot.py
# Pro Bot — all logic lives inside run() because the validator forbids
# any FunctionDef whose name is not "run".
#
# Injected globals (from helpers):
#   move_left, move_right, aim_up, aim_down, aim_left, aim_right,
#   shoot, reload, switch_weapon, throw_grenade, change_grenade_type,
#   pickup, jetpack, kneel, math, random, saw_info
#
# State API:
#   state.my_position()        -> (x, y)
#   state.my_health()          -> float
#   state.my_fuel()            -> float
#   state.my_gun()             -> int or None   (current weapon id)
#   state.my_ammo()            -> (current, total)
#   state.my_grenades()        -> {selected_type, frag, proxy, gas}
#   state.enemy_positions()    -> [{id,x,y,health,current_gun,secondary_gun,current_grenade,distance}]
#   state.gun_spawns()         -> [{x,y,weapon_id}]
#   state.medkit_spawns()      -> [{x,y}]
#   state.active_grenades()    -> [{x,y,vx,vy,type}]
#   state.saw_bullets_in_view()-> [{x,y,vx,vy,distance,owner_id,slot}]
#   state.bullet_positions()   -> [{x,y,vx,vy}]
#   state.distance_to_obstacle(theta) -> float

def run(state, memory):
    did_attack = False

    if not memory:
        memory = {
            "roam_dir": 1,
            "roam_ticks": 240,
            "evade_dir": 1,
            "evade_ticks": 0,
            "strafe_dir": 1,
            "strafe_ticks": 0,
            "grenade_tick": 0,
            "dodge_tick": 0,
            "target_id": -1,
            "target_health": -1.0,
            "no_damage_ticks": 0,
            "target_x": 0.0,
            "target_y": 0.0,
            "stable_ticks": 0,
            "last_x": 0.0,
            "last_y": 0.0,
            "stuck_ticks": 0,
            "nade_escape_ticks": 0,
            "nade_escape_dir": 1,
            "fly_tick": 0,
        }

    # Use enemy_positions for actual coordinates anywhere on map (not quadrant-limited).
    enemies = state.enemy_positions()
    markers = state.player_markers()
    ammo_cur, _ = state.my_ammo()
    grenades = state.my_grenades()
    health = state.my_health()
    fuel = state.my_fuel()
    current_aim = state.my_aim_angle()
    my_x, my_y = state.my_position()

    # Backward compatibility for matches that already had older memory schema.
    memory.setdefault("target_id", -1)
    memory.setdefault("target_health", -1.0)
    memory.setdefault("no_damage_ticks", 0)
    memory.setdefault("target_x", 0.0)
    memory.setdefault("target_y", 0.0)
    memory.setdefault("stable_ticks", 0)
    memory.setdefault("grenade_tick", 0)
    memory.setdefault("dodge_tick", 0)
    memory.setdefault("last_x", my_x)
    memory.setdefault("last_y", my_y)
    memory.setdefault("stuck_ticks", 0)
    memory.setdefault("nade_escape_ticks", 0)
    memory.setdefault("nade_escape_dir", 1)
    memory.setdefault("fly_tick", 0)

    # Engagement distances.
    MIN_FIGHT_DIST = 100.0
    MAX_FIGHT_DIST = 300.0
    PRESSURE_DIST = 145.0
    GRENADE_ESCAPE_DIST = 180.0
    STABLE_POS_TOLERANCE = 10.0
    STABLE_TICKS_TO_THROW = 6
    GRENADE_COOLDOWN_TICKS = 55
    FLY_UP_DY = -24.0
    FLY_COOLDOWN_TICKS = 2
    # Aim must be within this many radians before we fire (~7 degrees).
    # Slightly wider threshold to compensate for 0.12 rad/frame step size.
    AIM_THRESHOLD = 0.13

    # Tick down cooldowns every frame.
    if memory["grenade_tick"] > 0:
        memory["grenade_tick"] -= 1
    if memory["dodge_tick"] > 0:
        memory["dodge_tick"] -= 1
    if memory["fly_tick"] > 0:
        memory["fly_tick"] -= 1

    # Run away from nearby live grenades with higher priority than normal strafing.
    nades = state.active_grenades()
    nearest_nade = None
    nearest_nade_dist = 1e9
    for g in nades:
        nx = float(g["x"])
        ny = float(g["y"])
        d = math.sqrt((nx - my_x) * (nx - my_x) + (ny - my_y) * (ny - my_y))
        if d < nearest_nade_dist:
            nearest_nade_dist = d
            nearest_nade = g

    if nearest_nade is not None and nearest_nade_dist < GRENADE_ESCAPE_DIST:
        gx = float(nearest_nade["x"])
        memory["nade_escape_dir"] = -1 if my_x < gx else 1
        memory["nade_escape_ticks"] = 18
    elif memory["nade_escape_ticks"] > 0:
        memory["nade_escape_ticks"] -= 1

    escaping_nade = memory["nade_escape_ticks"] > 0

    if enemies:
        # Target the closest enemy.
        target = min(enemies, key=lambda e: e["distance"])
        target_id = int(target["id"])
        ex = float(target["x"])
        ey = float(target["y"])
        target_health = float(target["health"])
        distance = float(target["distance"])

        # Precise direction vector and angle to target.
        dx = ex - my_x
        dy = ey - my_y
        angle = math.atan2(dy, dx)

        # Line-of-sight: blocked if an obstacle is closer than the target.
        obstacle_dist = state.distance_to_obstacle(angle, max_distance=2000.0, step=4.0)
        blocked = obstacle_dist < max(0.0, distance - 20.0)

        # Aim error normalized to [-pi, pi].
        aim_error = angle - current_aim
        if aim_error > math.pi:
            aim_error -= 2.0 * math.pi
        elif aim_error < -math.pi:
            aim_error += 2.0 * math.pi

        # Single aim command per frame. AIM_ROTATION_SPEED = 0.12 rad/frame now,
        # so a 180° flip takes ~26 frames instead of ~78.
        if aim_error > 0.01:
            aim_right()   # clockwise: increases angle
        elif aim_error < -0.01:
            aim_left()    # counter-clockwise: decreases angle

        # Track whether target is stationary enough for a high-value grenade.
        if memory["target_id"] == target_id:
            moved = math.sqrt((ex - memory["target_x"]) * (ex - memory["target_x"]) + (ey - memory["target_y"]) * (ey - memory["target_y"]))
            if moved <= STABLE_POS_TOLERANCE:
                memory["stable_ticks"] += 1
            else:
                memory["stable_ticks"] = 0
        else:
            memory["stable_ticks"] = 0

        # If we keep firing but enemy HP is not dropping, pressure in closer.
        # Small epsilon avoids float jitter counting as damage.
        if memory["target_id"] == target_id and not blocked and abs(aim_error) < AIM_THRESHOLD:
            if target_health >= memory["target_health"] - 0.2:
                memory["no_damage_ticks"] += 1
            else:
                memory["no_damage_ticks"] = 0
        else:
            memory["no_damage_ticks"] = 0

        force_close = memory["no_damage_ticks"] >= 16

        # Movement based on actual pixel x-position, not angle hemisphere.
        if escaping_nade:
            if memory["nade_escape_dir"] < 0:
                move_left()
            else:
                move_right()
            if nearest_nade_dist < 120.0:
                jetpack()
        elif blocked:
            # Reposition: alternate direction every 50 ticks until LoS clears.
            if memory["evade_ticks"] <= 0:
                memory["evade_dir"] = -memory["evade_dir"]
                memory["evade_ticks"] = 50
            memory["evade_ticks"] -= 1
            if memory["evade_dir"] == -1:
                move_left()
            else:
                move_right()
            if memory["evade_ticks"] == 25:
                jetpack()
        elif distance > MAX_FIGHT_DIST:
            # Close the gap: move directly toward enemy.
            if dx < 0:
                move_left()
            else:
                move_right()
        elif distance < MIN_FIGHT_DIST and (not force_close):
            # Back away.
            if dx < 0:
                move_right()
            else:
                move_left()
        elif force_close and distance > PRESSURE_DIST:
            if dx < 0:
                move_left()
            else:
                move_right()
        else:
            # Ideal range: strafe side to side.
            if memory["strafe_ticks"] <= 0:
                memory["strafe_dir"] = -memory["strafe_dir"]
                memory["strafe_ticks"] = 80
            memory["strafe_ticks"] -= 1
            if memory["strafe_dir"] == -1:
                move_left()
            else:
                move_right()

        # Aggressive aerial chase: if target is above us, keep flying up while closing.
        if (not escaping_nade) and fuel > 10.0:
            should_fly_up = (dy < FLY_UP_DY) and (distance > PRESSURE_DIST or blocked)
            if should_fly_up and memory["fly_tick"] <= 0:
                jetpack()
                memory["fly_tick"] = FLY_COOLDOWN_TICKS

        # Fire only when aimed accurately and line-of-sight is clear.
        if not blocked and abs(aim_error) < AIM_THRESHOLD:
            if ammo_cur <= 0:
                reload()
            else:
                shoot()
                did_attack = True
        elif ammo_cur <= 0:
            reload()

        # Throw grenade when target position is stable long enough (tolerance-based).
        if (
            not escaping_nade
            and (not blocked)
            and distance < 320.0
            and (memory["stable_ticks"] >= STABLE_TICKS_TO_THROW or memory["no_damage_ticks"] >= 10)
            and memory["grenade_tick"] <= 0
        ):
            if grenades["gas"] > 0:
                if grenades["selected_type"] != 3:
                    change_grenade_type()
                else:
                    throw_grenade()
                    memory["grenade_tick"] = GRENADE_COOLDOWN_TICKS
                    did_attack = True
            elif grenades["frag"] > 0:
                if grenades["selected_type"] != 1:
                    change_grenade_type()
                else:
                    throw_grenade()
                    memory["grenade_tick"] = GRENADE_COOLDOWN_TICKS
                    did_attack = True

        # Save target tracking for next frame.
        memory["target_id"] = target_id
        memory["target_health"] = target_health
        memory["target_x"] = ex
        memory["target_y"] = ey

        # Dodge with jetpack when low health.
        if health < 30.0 and memory["dodge_tick"] <= 0:
            jetpack()
            memory["dodge_tick"] = 30

    elif markers:
        # Target is outside sensor radius but known from global markers: pursue it directly.
        marker = min(markers, key=lambda m: m["distance"])
        m_angle = float(marker["angle"])
        m_dist = float(marker["distance"])

        # Aim precisely toward marker angle (no circular spin).
        m_error = m_angle - current_aim
        if m_error > math.pi:
            m_error -= 2.0 * math.pi
        elif m_error < -math.pi:
            m_error += 2.0 * math.pi

        if m_error > 0.01:
            aim_right()
        elif m_error < -0.01:
            aim_left()

        if m_angle > 1.57 or m_angle < -1.57:
            move_left()
        else:
            move_right()

        # If marker is above us, use jetpack to climb toward the target lane.
        if (m_angle < -0.25 and m_angle > -2.9) and fuel > 8.0:
            if m_dist > PRESSURE_DIST or memory["stuck_ticks"] >= 6:
                jetpack()

        # Opportunistic long-range shots when marker aim is aligned and line of sight is clear.
        m_obstacle = state.distance_to_obstacle(m_angle, max_distance=2000.0, step=4.0)
        m_blocked = m_obstacle < max(0.0, m_dist - 20.0)
        if (not m_blocked) and abs(m_error) < AIM_THRESHOLD:
            if ammo_cur <= 0:
                reload()
            else:
                shoot()
                did_attack = True
        elif ammo_cur <= 0:
            reload()

        memory["target_id"] = int(marker["id"])
        memory["target_health"] = memory["target_health"]
        memory["no_damage_ticks"] = 0
        memory["stable_ticks"] = 0

    else:
        memory["target_id"] = -1
        memory["target_health"] = -1.0
        memory["no_damage_ticks"] = 0
        memory["stable_ticks"] = 0

        # No visible enemy: commit to one direction and only turn when a wall forces it.
        # Check ahead BEFORE issuing a move command so the turn takes immediate effect.
        front_angle = math.pi if memory["roam_dir"] == -1 else 0.0
        front_dist = state.distance_to_obstacle(front_angle, max_distance=64.0, step=4.0)
        if front_dist < 22.0 or memory["roam_ticks"] <= 0:
            # Wall hit or safety timeout — pick opposite direction and commit for ~4 secs.
            memory["roam_dir"] = -memory["roam_dir"]
            memory["roam_ticks"] = 240
            jetpack()  # hop over low ledge instead of jamming against it

        memory["roam_ticks"] -= 1

        if memory["roam_dir"] == -1:
            move_left()
        else:
            move_right()

        # Sweep aim toward the direction of travel so the gun leads the body.
        # Compute angular error to forward heading (0 = right, pi = left).
        roam_aim_target = math.pi if memory["roam_dir"] == -1 else 0.0
        roam_aim_err = roam_aim_target - current_aim
        if roam_aim_err > math.pi:
            roam_aim_err -= 2.0 * math.pi
        elif roam_aim_err < -math.pi:
            roam_aim_err += 2.0 * math.pi
        # Nudge once every 8 ticks — slow drift, not spinning.
        if memory["roam_ticks"] % 8 == 0:
            if roam_aim_err > 0.05:
                aim_right()
            elif roam_aim_err < -0.05:
                aim_left()

        # Occasional platform check — hop upward to scan higher terrain.
        if memory["roam_ticks"] % 55 == 0:
            jetpack()

    # Grab nearby guns opportunistically.
    pickup_gun(state)

    # Anti-stuck behavior: if position barely changes while not attacking,
    # force a fly-reposition to avoid camping in one place.
    moved = math.sqrt(
        (my_x - memory["last_x"]) * (my_x - memory["last_x"]) +
        (my_y - memory["last_y"]) * (my_y - memory["last_y"])
    )

    non_fight = (not enemies) and (not markers)

    if moved < 2.0 and ((not did_attack) or non_fight):
        memory["stuck_ticks"] += 1
    else:
        memory["stuck_ticks"] = 0

    # 22 frames (~0.37 s) outside combat before calling this truly stuck.
    # 14 frames in combat — a genuine wall press during a fight.
    stuck_limit = 22 if non_fight else 14
    if memory["stuck_ticks"] >= stuck_limit:
        # Do not add extra left/right here to avoid canceling current movement.
        # Just force vertical displacement and flip roam bias.
        memory["roam_dir"] = -memory["roam_dir"]
        jetpack()
        memory["stuck_ticks"] = 0

    memory["last_x"] = my_x
    memory["last_y"] = my_y

    return memory
