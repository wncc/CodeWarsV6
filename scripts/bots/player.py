def run(state, memory):
    # Persistent state. 'recovery' = frames to commit to roam_dir after unstick.
    roam_dir = 1
    patrol_idx = 0
    jump_cd = 0
    grenade_cd = 0
    stuck = 0
    last_x = 0
    last_y = 0
    climb_ticks = 0
    fly_ticks = 0
    recovery = 0

    if memory:
        try:
            p = memory.split(",")
            if len(p) >= 9:
                roam_dir = -1 if int(p[0]) < 0 else 1
                patrol_idx = int(p[1])
                jump_cd = max(0, int(p[2]))
                grenade_cd = max(0, int(p[3]))
                stuck = max(0, int(p[4]))
                last_x = int(p[5])
                last_y = int(p[6])
                climb_ticks = max(0, int(p[7]))
                fly_ticks = max(0, int(p[8]))
            if len(p) >= 10:
                recovery = max(0, int(p[9]))
        except Exception:
            pass

    x, y = state.my_position()
    health = state.my_health()
    fuel = state.my_fuel()
    aim = state.my_aim_angle()
    ammo_cur, ammo_total = state.my_ammo()
    current_gun = state.my_gun()
    enemies = state.enemy_info()
    markers = state.player_markers()
    grenades = state.my_grenades()

    if jump_cd > 0: jump_cd -= 1
    if grenade_cd > 0: grenade_cd -= 1
    if climb_ticks > 0: climb_ticks -= 1
    if fly_ticks > 0: fly_ticks -= 1
    if recovery > 0: recovery -= 1

    cur_dmg = 0
    cur_range = 0
    if current_gun is not None:
        cur_dmg = state.get_weapon_stat(current_gun, "damage") or 0
        cur_range = state.get_weapon_stat(current_gun, "effective_range") or 0

    patrol_points = [
        (38, 105), (200, 150), (350, 50), (500, 100), (750, 150),
        (887, 291), (926, 656), (1141, 677), (1281, 291), (1546, 998),
        (1575, 990), (1811, 286), (2017, 709), (2163, 299), (2378, 617), (2698, 1056),
    ]
    patrol_len = len(patrol_points)
    patrol_idx = patrol_idx % patrol_len

    best_gun = None
    best_gun_dist = 999999.0
    for gun in state.gun_spawns():
        wid = gun["weapon_id"]
        dmg = state.get_weapon_stat(wid, "damage") or 0
        rng = state.get_weapon_stat(wid, "effective_range") or 0
        gdx = gun["x"] - x
        gdy = gun["y"] - y
        gdist = math.sqrt(gdx * gdx + gdy * gdy)
        need = current_gun is None or cur_dmg < 12
        if need or dmg >= cur_dmg + 4 or rng >= cur_range + 120:
            if gdist < best_gun_dist:
                best_gun_dist = gdist
                best_gun = gun

    nearest_medkit = None
    nearest_medkit_dist = 999999.0
    for mk in state.medkit_spawns():
        mdx = mk["x"] - x
        mdy = mk["y"] - y
        mdist = math.sqrt(mdx * mdx + mdy * mdy)
        if mdist < nearest_medkit_dist:
            nearest_medkit_dist = mdist
            nearest_medkit = mk

    danger_g = None
    danger_dist = 999999.0
    for g in state.active_grenades():
        gdx = x - g["x"]
        gdy = y - g["y"]
        gdist = math.sqrt(gdx * gdx + gdy * gdy)
        if gdist < danger_dist:
            danger_dist = gdist
            danger_g = g

    in_gas = False
    gas_flee_dir = 1
    for cloud in state.gas_clouds():
        if cloud["distance"] < cloud["radius"] + 20.0:
            in_gas = True
            gas_flee_dir = -1 if x > cloud["x"] else 1
            break

    # =========================================================
    # PRIORITY 1: Escape live grenades.
    # Threshold raised to 220 = frag blast radius so the bot starts
    # running before the explosion reaches it.
    # =========================================================
    if danger_g is not None and danger_dist < 220.0:
        if x < danger_g["x"]:
            move_left()
            roam_dir = -1
        else:
            move_right()
            roam_dir = 1
        if fuel > 40.0 and jump_cd <= 0:
            jetpack()
            jump_cd = 20
        if ammo_cur <= 0 and ammo_total > 0:
            reload()

    # =========================================================
    # PRIORITY 2: Gas cloud escape
    # =========================================================
    elif in_gas:
        if gas_flee_dir < 0:
            move_left()
        else:
            move_right()
        if fuel > 20.0:
            jetpack()

    # =========================================================
    # PRIORITY 3: Critical health — heal before doing anything else
    # if a medkit is reachable (< 200 px).  Moved above combat/markers
    # so the bot doesn't get finished off while chasing enemies.
    # =========================================================
    elif health < 65.0 and nearest_medkit is not None and nearest_medkit_dist < 200.0:
        tx = nearest_medkit["x"]
        ty = nearest_medkit["y"]
        move_dir = -1 if tx < x else 1
        roam_dir = move_dir
        if move_dir < 0:
            move_left()
        else:
            move_right()
        front_angle = math.pi if move_dir < 0 else 0.0
        front_dist = state.distance_to_obstacle(front_angle, max_distance=64.0, step=2.0)
        mk_above = ty < y - 60.0
        if front_dist < 18.0:
            climb_ticks = 12
        if mk_above:
            climb_ticks = 12
        if mk_above and fuel > 18.0:
            jetpack()
        elif fuel > 32.0 and climb_ticks > 0:
            jetpack()
        if nearest_medkit_dist < 22.0:
            pickup()

    # =========================================================
    # PRIORITY 4: Combat — visible enemies in sensor range
    # =========================================================
    elif enemies:
        target = min(enemies, key=lambda e: e["distance"])
        ex = float(target["x"])
        ey = float(target["y"])
        dist = float(target["distance"])
        dx = ex - x
        dy = ey - y
        angle = math.atan2(dy, dx)

        err = angle - aim
        if err > math.pi: err -= 2.0 * math.pi
        elif err < -math.pi: err += 2.0 * math.pi
        if err > 0.02: aim_right()
        elif err < -0.02: aim_left()

        # FIX: use step=2.0 so thin walls are not skipped by raycasting.
        obs_dist = state.distance_to_obstacle(angle, max_distance=2000.0, step=2.0)
        blocked = obs_dist < max(0.0, dist - 16.0)

        # Enemy is below a floor: dy > 40 means enemy is significantly lower.
        # Moving toward them would mean trying to walk through solid ground.
        enemy_below_floor = blocked and dy > 40.0

        # Enemy is above a ceiling: dy < -40 means enemy is significantly higher
        # and a solid surface blocks the path — don't jetpack into ceiling.
        enemy_above_ceiling = blocked and dy < -40.0

        # Enemy separated by a solid wall/floor/ceiling — no direct path.
        # The bot should roam horizontally instead of charging or jumping.
        enemy_behind_solid = enemy_below_floor or enemy_above_ceiling

        move_dir = -1 if dx < 0 else 1
        roam_dir = move_dir
        front_angle = math.pi if move_dir < 0 else 0.0
        front_dist = state.distance_to_obstacle(front_angle, max_distance=64.0, step=2.0)

        if enemy_behind_solid:
            # Move horizontally to find a gap, ledge, or stairs.
            # Reverse if a wall blocks the horizontal path.
            if front_dist < 18.0:
                if move_dir < 0: move_right()
                else: move_left()
            else:
                if move_dir < 0: move_left()
                else: move_right()
            # No jetpack — need to navigate around, not fly into solid surfaces.
        elif dist > 190.0 or blocked:
            if move_dir < 0: move_left()
            else: move_right()
            # Only climb/jetpack when NOT blocked by a solid surface between
            # us and the enemy.  If blocked, the obstacle is between us — flying
            # up won't help and wastes fuel / looks like hallucination.
            if not blocked:
                if front_dist < 18.0: climb_ticks = 10
                if dy < -60.0 and abs(dx) < 150.0: climb_ticks = 10
                if fuel > 28.0 and climb_ticks > 0: jetpack()
                if fuel > 46.0 and jump_cd <= 0 and front_dist < 18.0:
                    jetpack()
                    jump_cd = 16
                    climb_ticks = 10
            else:
                # Blocked but not below/above — side wall.  Only climb to
                # get over the wall itself, don't aggressively chase.
                if front_dist < 18.0 and fuel > 38.0 and jump_cd <= 0:
                    jetpack()
                    jump_cd = 18
                    climb_ticks = 8
        elif dist < 80.0:
            if move_dir < 0: move_right()
            else: move_left()
        else:
            if move_dir < 0: move_left()
            else: move_right()
            if front_dist < 18.0: climb_ticks = 8
            if dy < -60.0 and abs(dx) < 150.0: climb_ticks = 8
            if fuel > 28.0 and climb_ticks > 0: jetpack()

        # FIX: check BOTH the enemy angle AND the actual current aim direction
        # before firing.  The bullet travels along `aim`, not `angle`, so if
        # aim is slightly off and points into a wall the bullet hits the wall.
        aim_obs = state.distance_to_obstacle(aim, max_distance=2000.0, step=2.0)
        aim_clear = aim_obs >= dist - 16.0
        if not blocked and aim_clear and abs(err) < 0.12:
            if ammo_cur > 0:
                shoot()
            elif ammo_total > 0:
                reload()
            else:
                switch_weapon()
        elif ammo_cur <= 0 and ammo_total > 0:
            reload()

        # -------------------------------------------------------
        # Grenade strategy — safe distances only.
        #
        # Blast radii (pixels):  frag=200, proxy=200, gas=125
        # Safe throw rule: bot must be OUTSIDE the blast when it
        # explodes, i.e. dist > blast_radius + 20 px margin.
        #
        #   Gas  (blast 125): safe when dist > 145
        #   Frag (blast 200): safe when dist > 220
        #   Proxy (blast 200): safe when dist > 220
        #
        # Also check the throw path is not blocked by a wall
        # (otherwise grenade bounces back).
        # -------------------------------------------------------
        if not blocked and not enemy_behind_solid and grenade_cd <= 0:
            total_nades = grenades["frag"] + grenades["proxy"] + grenades["gas"]
            # Verify no wall stands between us and the throw target.
            throw_wall = state.distance_to_obstacle(angle, max_distance=300.0, step=2.0)
            path_ok = throw_wall >= dist * 0.85
            if total_nades > 0 and path_ok:
                desired = 0
                if 145.0 < dist < 220.0 and grenades["gas"] > 0:
                    desired = 3   # gas: safe at this range
                elif dist > 220.0 and grenades["frag"] > 0:
                    desired = 1   # frag: outside its own blast radius
                elif dist > 220.0 and grenades["proxy"] > 0:
                    desired = 2   # proxy: outside blast, enemy walks into it
                if desired > 0:
                    if grenades["selected_type"] != desired:
                        change_grenade_type()
                    else:
                        throw_grenade()
                        grenade_cd = 65

        if health < 80.0 and nearest_medkit is not None and nearest_medkit_dist < 25.0:
            pickup()

    # =========================================================
    # PRIORITY 5: Long-range pursuit via global player markers
    # =========================================================
    elif markers:
        target = min(markers, key=lambda m: m["distance"])
        angle = float(target["angle"])
        dist = float(target["distance"])

        err = angle - aim
        if err > math.pi: err -= 2.0 * math.pi
        elif err < -math.pi: err += 2.0 * math.pi
        if err > 0.02: aim_right()
        elif err < -0.02: aim_left()

        # FIX: the key detour fix.
        # When recovery > 0 the bot was just stuck.  The anti-stuck already
        # flipped roam_dir to the opposite direction.  Use that flipped
        # roam_dir for horizontal movement instead of blindly following the
        # marker angle — this makes the bot go AROUND the obstacle rather
        # than walking straight back into the same wall.
        # When recovery == 0 operate normally and update roam_dir.
        if recovery > 0:
            move_dir = roam_dir
            # Also sustain upward flight during recovery to help clear walls.
            if fuel > 18.0:
                jetpack()
        else:
            move_dir = -1 if math.cos(angle) < 0 else 1
            roam_dir = move_dir

        if move_dir < 0:
            move_left()
        else:
            move_right()

        front_angle = math.pi if move_dir < 0 else 0.0
        front_dist = state.distance_to_obstacle(front_angle, max_distance=96.0, step=2.0)

        target_above = -2.8 < angle < -0.35
        very_far = dist > 350.0

        if front_dist < 28.0:
            climb_ticks = 14
        if target_above:
            fly_ticks = 14
        if very_far:
            fly_ticks = 16

        # Sustained upward flight when target is above (no jump_cd gate).
        if target_above and fuel > 18.0:
            jetpack()
        elif fuel > 28.0 and (climb_ticks > 0 or fly_ticks > 0):
            jetpack()

        if fuel > 36.0 and jump_cd <= 0 and (front_dist < 28.0 or very_far):
            jetpack()
            jump_cd = 12
            if very_far: fly_ticks = 14
            else: climb_ticks = 14

        # Opportunistic long-range shots using step=2.0 for accuracy.
        obs = state.distance_to_obstacle(angle, max_distance=2000.0, step=2.0)
        if obs >= dist - 16.0 and abs(err) < 0.12:
            if ammo_cur > 0:
                shoot()
            elif ammo_total > 0:
                reload()

    # =========================================================
    # PRIORITY 6: Medkit recovery when health is low
    # =========================================================
    elif health < 120.0 and nearest_medkit is not None:
        tx = nearest_medkit["x"]
        ty = nearest_medkit["y"]
        move_dir = -1 if tx < x else 1
        roam_dir = move_dir
        if move_dir < 0: move_left()
        else: move_right()

        front_angle = math.pi if move_dir < 0 else 0.0
        front_dist = state.distance_to_obstacle(front_angle, max_distance=64.0, step=2.0)
        mk_above = ty < y - 60.0
        if front_dist < 18.0: climb_ticks = 12
        if mk_above: climb_ticks = 12
        if mk_above and fuel > 18.0: jetpack()
        elif fuel > 32.0 and climb_ticks > 0: jetpack()
        if not mk_above and fuel > 46.0 and jump_cd <= 0 and front_dist < 18.0:
            jetpack()
            jump_cd = 18
            climb_ticks = 12
        if nearest_medkit_dist < 22.0:
            pickup()

    # =========================================================
    # PRIORITY 7: Weapon upgrade
    # =========================================================
    elif best_gun is not None:
        tx = best_gun["x"]
        ty = best_gun["y"]
        move_dir = -1 if tx < x else 1
        roam_dir = move_dir
        if move_dir < 0: move_left()
        else: move_right()

        front_angle = math.pi if move_dir < 0 else 0.0
        front_dist = state.distance_to_obstacle(front_angle, max_distance=64.0, step=2.0)
        gun_above = ty < y - 60.0
        if front_dist < 18.0: climb_ticks = 12
        if gun_above: climb_ticks = 12
        if gun_above and fuel > 18.0: jetpack()
        elif fuel > 32.0 and climb_ticks > 0: jetpack()
        if not gun_above and fuel > 46.0 and jump_cd <= 0 and front_dist < 18.0:
            jetpack()
            jump_cd = 18
            climb_ticks = 12
        if best_gun_dist < 22.0:
            pickup_gun(state)

    # =========================================================
    # PRIORITY 8: Patrol
    # =========================================================
    else:
        tx, ty = patrol_points[patrol_idx]
        if abs(tx - x) < 38.0:
            patrol_idx = (patrol_idx + 1) % patrol_len
            tx, ty = patrol_points[patrol_idx]

        move_dir = -1 if tx < x else 1
        roam_dir = move_dir
        front_angle = math.pi if move_dir < 0 else 0.0
        front_dist = state.distance_to_obstacle(front_angle, max_distance=64.0, step=2.0)

        if move_dir < 0: move_left()
        else: move_right()

        if front_dist < 18.0: climb_ticks = 12
        if ty < y - 80.0 and abs(tx - x) < 120.0: climb_ticks = 12

        if fuel > 28.0 and (climb_ticks > 0 or fly_ticks > 0): jetpack()
        if fuel > 42.0 and jump_cd <= 0 and (front_dist < 18.0 or (ty < y - 80.0 and abs(tx - x) < 120.0)):
            jetpack()
            jump_cd = 20
            if ty < y - 80.0: fly_ticks = 10
            else: climb_ticks = 12

        roam_target = math.pi if move_dir < 0 else 0.0
        roam_err = roam_target - aim
        if roam_err > math.pi: roam_err -= 2.0 * math.pi
        elif roam_err < -math.pi: roam_err += 2.0 * math.pi
        if roam_err > 0.08: aim_right()
        elif roam_err < -0.08: aim_left()

    # Global opportunistic weapon pickup — every frame regardless of priority.
    if best_gun is not None and best_gun_dist < 22.0:
        pickup_gun(state)

    # =========================================================
    # Anti-stuck
    # During recovery the stuck counter is frozen so the bot
    # can't immediately re-trigger another detour event.
    # =========================================================
    moved = math.sqrt((x - last_x) ** 2 + (y - last_y) ** 2)
    if recovery == 0:
        if moved < 2.0:
            stuck += 1
        else:
            stuck = 0

        if stuck > 25:
            roam_dir = -roam_dir   # flip — markers branch will use this during recovery
            climb_ticks = 16
            fly_ticks = 12
            if fuel > 40.0 and jump_cd <= 0:
                jetpack()
                jump_cd = 20
            recovery = 55
            stuck = 0

    memory = f"{roam_dir},{patrol_idx},{jump_cd},{grenade_cd},{stuck},{int(x)},{int(y)},{climb_ticks},{fly_ticks},{recovery}"
    return memory[:100]
