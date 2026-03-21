def run(state, memory):
    # Persistent state stored inside the engine-provided memory string.
    # These values keep the bot's movement, cooldowns, and anti-stuck behavior
    # stable across frames.
    roam_dir = 1
    patrol_idx = 0
    jump_cd = 0
    grenade_cd = 0
    stuck = 0
    last_x = 0
    last_y = 0
    climb_ticks = 0
    fly_ticks = 0

    # Restore the previous frame's state from memory.
    # If parsing fails, the bot falls back to safe defaults.
    if memory:
        try:
            parts = memory.split(",")
            if len(parts) >= 9:
                roam_dir = -1 if int(parts[0]) < 0 else 1
                patrol_idx = int(parts[1])
                jump_cd = int(parts[2])
                grenade_cd = int(parts[3])
                stuck = int(parts[4])
                last_x = int(parts[5])
                last_y = int(parts[6])
                climb_ticks = int(parts[7])
                fly_ticks = int(parts[8])
        except Exception:
            roam_dir = 1
            patrol_idx = 0
            jump_cd = 0
            grenade_cd = 0
            stuck = 0
            last_x = 0
            last_y = 0
            climb_ticks = 0
            fly_ticks = 0

    # Read the current game snapshot. The bot makes all decisions for this
    # frame from these state values.
    x, y = state.my_position()
    health = state.my_health()
    fuel = state.my_fuel()
    aim = state.my_aim_angle()
    ammo_cur, ammo_total = state.my_ammo()
    current_gun = state.my_gun()
    enemies = state.enemy_info()
    markers = state.player_markers()
    grenades = state.my_grenades()

    # Cache the current weapon's basic stats so upgrade decisions are easy.
    current_damage = 0
    current_range = 0
    if current_gun is not None:
        current_damage = state.get_weapon_stat(current_gun, "damage") or 0
        current_range = state.get_weapon_stat(current_gun, "effective_range") or 0

    # Count down all frame-based timers and cooldowns.
    if jump_cd > 0:
        jump_cd -= 1
    if grenade_cd > 0:
        grenade_cd -= 1
    if climb_ticks > 0:
        climb_ticks -= 1
    if fly_ticks > 0:
        fly_ticks -= 1

    # Predefined patrol / traversal points for the catacombs map.
    # When no urgent combat or pickup goal exists, the bot walks these points.
    patrol_points = [
        (38, 105),
        (200, 150),
        (350, 50),
        (500, 100),
        (750, 150),
        (887, 291),
        (926, 656),
        (1141, 677),
        (1281, 291),
        (1546, 998),
        (1811, 286),
        (2017, 709),
        (2163, 299),
        (2269, 296),
        (2378, 617),
    ]
    patrol_len = len(patrol_points)
    if patrol_len > 0:
        patrol_idx = patrol_idx % patrol_len

    # Find the nearest visible gun that is a meaningful upgrade.
    best_gun = None
    best_gun_dist = 999999.0
    for gun in state.gun_spawns():
        weapon_id = gun["weapon_id"]
        damage = state.get_weapon_stat(weapon_id, "damage") or 0
        effective_range = state.get_weapon_stat(weapon_id, "effective_range") or 0
        better_damage = damage >= current_damage + 4
        better_range = effective_range >= current_range + 120
        need_upgrade = current_gun is None or current_damage < 12
        if need_upgrade or better_damage or better_range:
            dx = gun["x"] - x
            dy = gun["y"] - y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < best_gun_dist:
                best_gun_dist = dist
                best_gun = gun

    # Find the nearest visible medkit for low-health recovery.
    nearest_medkit = None
    nearest_medkit_dist = 999999.0
    for medkit in state.medkit_spawns():
        dx = medkit["x"] - x
        dy = medkit["y"] - y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < nearest_medkit_dist:
            nearest_medkit_dist = dist
            nearest_medkit = medkit

    # Track the nearest visible grenade for emergency avoidance.
    nearest_grenade = None
    nearest_grenade_dist = 999999.0
    for grenade in state.active_grenades():
        dx = x - grenade["x"]
        dy = y - grenade["y"]
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < nearest_grenade_dist:
            nearest_grenade_dist = dist
            nearest_grenade = grenade

    # Highest-priority escape behavior: move away from a nearby live grenade.
    if nearest_grenade is not None and nearest_grenade_dist < 150.0:
        if x < nearest_grenade["x"]:
            move_left()
            roam_dir = -1
        else:
            move_right()
            roam_dir = 1
        if fuel > 65.0 and jump_cd <= 0:
            jetpack()
            jump_cd = 28
            climb_ticks = 10
    # Visible-enemy combat behavior:
    # aim at the closest enemy, move to pressure/fight, use jetpack for blocked
    # climbs, shoot when aim and line-of-sight are good, and optionally throw
    # grenades.
    elif enemies:
        target = enemies[0]
        best_dist = float(target["distance"])
        for enemy in enemies:
            if enemy["distance"] < best_dist:
                best_dist = float(enemy["distance"])
                target = enemy

        ex = float(target["x"])
        ey = float(target["y"])
        dx = ex - x
        dy = ey - y
        dist = math.sqrt(dx * dx + dy * dy)
        angle = math.atan2(dy, dx)
        err = angle - aim
        if err > math.pi:
            err -= 2.0 * math.pi
        elif err < -math.pi:
            err += 2.0 * math.pi

        # Aim the weapon toward the target.
        if err > 0.02:
            aim_right()
        elif err < -0.02:
            aim_left()

        move_dir = -1 if dx < 0 else 1
        roam_dir = move_dir
        front_angle = math.pi if move_dir < 0 else 0.0
        front_dist = state.distance_to_obstacle(front_angle, max_distance=64.0, step=4.0)
        blocked = state.distance_to_obstacle(angle, max_distance=2000.0, step=4.0) < max(0.0, dist - 18.0)

        # Core combat movement:
        # far or blocked -> close distance
        # too near -> back off
        # mid-range -> keep pressuring in the target direction
        if dist > 180.0 or blocked:
            if move_dir < 0:
                move_left()
            else:
                move_right()
        elif dist < 90.0:
            if move_dir < 0:
                move_right()
            else:
                move_left()
        else:
            if move_dir < 0:
                move_left()
            else:
                move_right()

        # Detect vertical / terrain obstruction and prepare short climbs.
        if front_dist < 18.0:
            climb_ticks = 8
        if dy < -70.0 and abs(dx) < 140.0:
            climb_ticks = 8

        # Jetpack usage in combat:
        # short bursts for ledges and for enemies above the bot.
        if fuel > 38.0 and (climb_ticks > 0 or (dy < -70.0 and abs(dx) < 140.0)):
            jetpack()
        if fuel > 55.0 and jump_cd <= 0 and (front_dist < 18.0 or (dy < -70.0 and abs(dx) < 140.0)):
            jetpack()
            jump_cd = 20
            climb_ticks = 8

        # Fire only with acceptable aim and line-of-sight.
        if not blocked and abs(err) < 0.14:
            if ammo_cur > 0:
                shoot()
            elif ammo_total > 0:
                reload()
            else:
                switch_weapon()
        elif ammo_cur <= 0 and ammo_total > 0:
            reload()

        # Grenade behavior:
        # pick a grenade type based on distance / inventory and use cooldowns to
        # avoid spamming.
        if not blocked and grenade_cd <= 0 and dist < 170.0:
            desired_type = 1
            if grenades["gas"] > 0 and dist < 140.0:
                desired_type = 3
            elif grenades["frag"] <= 0 and grenades["proxy"] > 0:
                desired_type = 2

            total_nades = grenades["frag"] + grenades["proxy"] + grenades["gas"]
            if total_nades > 0:
                if grenades["selected_type"] != desired_type:
                    change_grenade_type()
                else:
                    throw_grenade()
                    grenade_cd = 60

        # Opportunistically grab a better gun if already close enough.
        if best_gun is not None and best_gun_dist < 20.0:
            pickup_gun(state)
    # Long-range chase behavior:
    # if no enemy is visible locally, use global player markers to move toward
    # the nearest distant opponent.
    elif markers:
        target = markers[0]
        best_dist = float(target["distance"])
        for marker in markers:
            if marker["distance"] < best_dist:
                best_dist = float(marker["distance"])
                target = marker

        angle = float(target["angle"])
        dist = float(target["distance"])
        err = angle - aim
        if err > math.pi:
            err -= 2.0 * math.pi
        elif err < -math.pi:
            err += 2.0 * math.pi

        # Rotate aim toward the marker direction while approaching.
        if err > 0.02:
            aim_right()
        elif err < -0.02:
            aim_left()

        move_dir = -1 if math.cos(angle) < 0 else 1
        roam_dir = move_dir
        if move_dir < 0:
            move_left()
        else:
            move_right()

        front_angle = math.pi if move_dir < 0 else 0.0
        front_dist = state.distance_to_obstacle(front_angle, max_distance=96.0, step=4.0)
        long_chase = dist > 320.0
        very_long_chase = dist > 520.0
        target_above = angle < -0.35 and angle > -2.8

        # Prepare climbs / flights for long route traversal.
        if front_dist < 28.0:
            climb_ticks = 10
        if target_above and dist > 140.0:
            fly_ticks = 12
        if very_long_chase:
            fly_ticks = 16

        # Jetpack usage for longer chases and vertical travel.
        if fuel > 34.0 and (climb_ticks > 0 or fly_ticks > 0):
            jetpack()
        if fuel > 44.0 and jump_cd <= 0 and (
            front_dist < 28.0
            or (target_above and dist > 140.0)
            or very_long_chase
        ):
            jetpack()
            jump_cd = 14
            if target_above or very_long_chase:
                fly_ticks = 12
            else:
                climb_ticks = 10

        if long_chase and not target_above and fuel > 60.0 and jump_cd <= 4:
            jetpack()
    # Low-health recovery behavior: move toward the nearest visible medkit.
    elif health < 100.0 and nearest_medkit is not None:
        tx = nearest_medkit["x"]
        move_dir = -1 if tx < x else 1
        roam_dir = move_dir
        if move_dir < 0:
            move_left()
        else:
            move_right()
        front_angle = math.pi if move_dir < 0 else 0.0
        front_dist = state.distance_to_obstacle(front_angle, max_distance=64.0, step=4.0)
        if front_dist < 18.0:
            climb_ticks = 8
        if fuel > 38.0 and climb_ticks > 0:
            jetpack()
        if fuel > 55.0 and jump_cd <= 0 and front_dist < 18.0:
            jetpack()
            jump_cd = 20
            climb_ticks = 8
        pickup()
    # Weapon-upgrade behavior: move toward the nearest visible useful gun.
    elif best_gun is not None:
        tx = best_gun["x"]
        move_dir = -1 if tx < x else 1
        roam_dir = move_dir
        if move_dir < 0:
            move_left()
        else:
            move_right()
        front_angle = math.pi if move_dir < 0 else 0.0
        front_dist = state.distance_to_obstacle(front_angle, max_distance=64.0, step=4.0)
        if front_dist < 18.0:
            climb_ticks = 10
        if fuel > 38.0 and climb_ticks > 0:
            jetpack()
        if fuel > 55.0 and jump_cd <= 0 and front_dist < 18.0:
            jetpack()
            jump_cd = 20
            climb_ticks = 10
        if best_gun_dist < 20.0:
            pickup_gun(state)
        else:
            pickup()
    # Default patrol behavior:
    # follow predefined map points, using jetpack to climb over route obstacles.
    else:
        tx, ty = patrol_points[patrol_idx]
        if abs(tx - x) < 36.0:
            patrol_idx = (patrol_idx + 1) % patrol_len
            tx, ty = patrol_points[patrol_idx]

        move_dir = -1 if tx < x else 1
        roam_dir = move_dir
        front_angle = math.pi if move_dir < 0 else 0.0
        front_dist = state.distance_to_obstacle(front_angle, max_distance=64.0, step=4.0)

        if move_dir < 0:
            move_left()
        else:
            move_right()

        if front_dist < 18.0:
            climb_ticks = 10
        if ty < y - 90.0 and abs(tx - x) < 120.0:
            climb_ticks = 10

        # Jetpack usage during patrol and route traversal.
        if fuel > 34.0 and (climb_ticks > 0 or fly_ticks > 0):
            jetpack()
        if fuel > 48.0 and jump_cd <= 0 and (front_dist < 18.0 or (ty < y - 90.0 and abs(tx - x) < 120.0)):
            jetpack()
            jump_cd = 22
            if ty < y - 90.0 and abs(tx - x) < 120.0:
                fly_ticks = 8
            else:
                climb_ticks = 10

        roam_target = math.pi if move_dir < 0 else 0.0
        roam_err = roam_target - aim
        if roam_err > math.pi:
            roam_err -= 2.0 * math.pi
        elif roam_err < -math.pi:
            roam_err += 2.0 * math.pi
        if roam_err > 0.08:
            aim_right()
        elif roam_err < -0.08:
            aim_left()

    # Anti-stuck detection:
    # if the bot fails to make progress for many frames, it flips patrol
    # direction and forces a recovery jump.
    moved = math.sqrt((x - last_x) * (x - last_x) + (y - last_y) * (y - last_y))
    if moved < 2.0:
        stuck += 1
    else:
        stuck = 0

    if stuck > 18:
        patrol_idx = (patrol_idx + 1) % patrol_len
        roam_dir = -roam_dir
        climb_ticks = 12
        if fuel > 55.0 and jump_cd <= 0:
            jetpack()
            jump_cd = 24
        stuck = 0

    # Save the updated state back into the memory string for the next frame.
    memory = f"{roam_dir},{patrol_idx},{jump_cd},{grenade_cd},{stuck},{int(x)},{int(y)},{climb_ticks},{fly_ticks}"
    return memory[:100]
