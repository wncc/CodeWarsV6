def run(state, memory):
    roam_dir = 1
    roam_ticks = 180
    strafe_dir = 1
    strafe_ticks = 0
    grenade_cd = 0
    evade_dir = 1
    evade_ticks = 0
    stuck = 0
    last_x = 0
    last_y = 0

    if memory:
        try:
            parts = memory.split(",")
            if len(parts) >= 10:
                roam_dir = -1 if int(parts[0]) < 0 else 1
                roam_ticks = int(parts[1])
                strafe_dir = -1 if int(parts[2]) < 0 else 1
                strafe_ticks = int(parts[3])
                grenade_cd = int(parts[4])
                evade_dir = -1 if int(parts[5]) < 0 else 1
                evade_ticks = int(parts[6])
                stuck = int(parts[7])
                last_x = int(parts[8])
                last_y = int(parts[9])
        except Exception:
            roam_dir = 1
            roam_ticks = 180
            strafe_dir = 1
            strafe_ticks = 0
            grenade_cd = 0
            evade_dir = 1
            evade_ticks = 0
            stuck = 0
            last_x = 0
            last_y = 0

    x, y = state.my_position()
    health = state.my_health()
    fuel = state.my_fuel()
    aim = state.my_aim_angle()
    ammo_cur, _ = state.my_ammo()
    current_gun = state.my_gun()
    grenades = state.my_grenades()
    enemies = state.enemy_info()
    markers = state.player_markers()
    current_damage = 0
    current_range = 0

    if current_gun is not None:
        current_damage = state.get_weapon_stat(current_gun, "damage") or 0
        current_range = state.get_weapon_stat(current_gun, "effective_range") or 0

    if grenade_cd > 0:
        grenade_cd -= 1
    if evade_ticks > 0:
        evade_ticks -= 1
    if strafe_ticks > 0:
        strafe_ticks -= 1

    nearest_live_grenade = None
    grenade_dist = 999999.0
    for g in state.active_grenades():
        dxg = x - g["x"]
        dyg = y - g["y"]
        dg = math.sqrt(dxg * dxg + dyg * dyg)
        if dg < grenade_dist:
            grenade_dist = dg
            nearest_live_grenade = g

    if nearest_live_grenade is not None and grenade_dist < 165.0:
        if x < nearest_live_grenade["x"]:
            move_left()
        else:
            move_right()
        if fuel > 8.0:
            jetpack()
        roam_dir = -1 if x < nearest_live_grenade["x"] else 1
    elif enemies:
        target = enemies[0]
        best_score = 10 ** 9
        for enemy in enemies:
            score = enemy["distance"] + enemy["health"] * 0.15
            if score < best_score:
                best_score = score
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

        if err > 0.01:
            aim_right()
        elif err < -0.01:
            aim_left()

        desired_dir = -1 if dx < 0 else 1
        front_angle = math.pi if desired_dir == -1 else 0.0
        back_angle = 0.0 if desired_dir == -1 else math.pi
        front_dist = state.distance_to_obstacle(front_angle, max_distance=64.0, step=4.0)
        back_dist = state.distance_to_obstacle(back_angle, max_distance=64.0, step=4.0)
        blocked = state.distance_to_obstacle(angle, max_distance=2000.0, step=4.0) < max(0.0, dist - 18.0)

        if blocked:
            if evade_ticks <= 0:
                evade_dir = -evade_dir
                evade_ticks = 36
            if evade_dir < 0:
                move_left()
            else:
                move_right()
            if fuel > 8.0 and (front_dist < 20.0 or dy < -28.0):
                jetpack()
        elif dist > 250.0:
            if desired_dir < 0:
                move_left()
            else:
                move_right()
            if fuel > 8.0 and (front_dist < 20.0 or dy < -24.0):
                jetpack()
        elif dist < 105.0:
            if desired_dir < 0:
                move_right()
            else:
                move_left()
            if fuel > 10.0 and health < 90.0:
                jetpack()
        else:
            if strafe_ticks <= 0:
                strafe_dir = -strafe_dir
                strafe_ticks = 45
            if strafe_dir < 0:
                move_left()
            else:
                move_right()
            if fuel > 8.0 and (front_dist < 18.0 or dy < -32.0):
                jetpack()

        if front_dist < 16.0 and back_dist > front_dist:
            if desired_dir < 0:
                move_right()
            else:
                move_left()

        if (not blocked) and abs(err) < 0.13:
            if ammo_cur <= 0:
                switch_weapon()
                reload()
            else:
                shoot()
        elif ammo_cur <= 0:
            switch_weapon()
            reload()

        if (not blocked) and grenade_cd == 0 and dist < 220.0:
            desired_type = 1
            if grenades["gas"] > 0 and (dist < 170.0 or health > 120.0):
                desired_type = 3
            elif grenades["frag"] <= 0 and grenades["proxy"] > 0:
                desired_type = 2
            elif grenades["frag"] <= 0 and grenades["gas"] > 0:
                desired_type = 3

            total_nades = grenades["frag"] + grenades["proxy"] + grenades["gas"]
            if total_nades > 0:
                if grenades["selected_type"] != desired_type:
                    change_grenade_type()
                else:
                    throw_grenade()
                    grenade_cd = 50

        best_spawn = None
        best_spawn_score = -999999.0
        for gun in state.gun_spawns():
            weapon_id = gun["weapon_id"]
            damage = state.get_weapon_stat(weapon_id, "damage") or 0
            effective_range = state.get_weapon_stat(weapon_id, "effective_range") or 0
            dist_score = math.sqrt((gun["x"] - x) * (gun["x"] - x) + (gun["y"] - y) * (gun["y"] - y))
            spawn_score = damage * 20.0 + effective_range * 0.03 - dist_score * 0.25
            if weapon_id in (3, 4, 5, 10, 11, 12, 13, 14, 15):
                spawn_score += 30.0
            if spawn_score > best_spawn_score:
                best_spawn_score = spawn_score
                best_spawn = gun

        if best_spawn is not None:
            better_damage = (state.get_weapon_stat(best_spawn["weapon_id"], "damage") or 0) >= current_damage + 4
            better_range = (state.get_weapon_stat(best_spawn["weapon_id"], "effective_range") or 0) >= current_range + 120
            if current_gun is None or current_damage < 12 or better_damage or better_range:
                pickup_gun(state)
    elif markers:
        marker = markers[0]
        for candidate in markers:
            if candidate["distance"] < marker["distance"]:
                marker = candidate

        m_angle = float(marker["angle"])
        m_dist = float(marker["distance"])
        m_err = m_angle - aim
        if m_err > math.pi:
            m_err -= 2.0 * math.pi
        elif m_err < -math.pi:
            m_err += 2.0 * math.pi

        if m_err > 0.01:
            aim_right()
        elif m_err < -0.01:
            aim_left()

        desired_dir = -1 if math.cos(m_angle) < 0 else 1
        front_angle = math.pi if desired_dir == -1 else 0.0
        front_dist = state.distance_to_obstacle(front_angle, max_distance=64.0, step=4.0)

        if desired_dir < 0:
            move_left()
        else:
            move_right()

        if fuel > 8.0 and (front_dist < 20.0 or (m_angle < -0.3 and m_angle > -2.8 and m_dist > 120.0)):
            jetpack()

        best_spawn = None
        best_spawn_score = -999999.0
        for gun in state.gun_spawns():
            weapon_id = gun["weapon_id"]
            damage = state.get_weapon_stat(weapon_id, "damage") or 0
            effective_range = state.get_weapon_stat(weapon_id, "effective_range") or 0
            dist_score = math.sqrt((gun["x"] - x) * (gun["x"] - x) + (gun["y"] - y) * (gun["y"] - y))
            spawn_score = damage * 20.0 + effective_range * 0.03 - dist_score * 0.25
            if weapon_id in (3, 4, 5, 10, 11, 12, 13, 14, 15):
                spawn_score += 30.0
            if spawn_score > best_spawn_score:
                best_spawn_score = spawn_score
                best_spawn = gun

        if best_spawn is not None:
            better_damage = (state.get_weapon_stat(best_spawn["weapon_id"], "damage") or 0) >= current_damage + 4
            better_range = (state.get_weapon_stat(best_spawn["weapon_id"], "effective_range") or 0) >= current_range + 120
            if current_gun is None or current_damage < 12 or better_damage or better_range:
                pickup_gun(state)
    else:
        medkit_target = None
        gun_target = None
        best_medkit_dist = 999999.0
        best_gun_dist = 999999.0

        for medkit in state.medkit_spawns():
            dmx = medkit["x"] - x
            dmy = medkit["y"] - y
            dd = math.sqrt(dmx * dmx + dmy * dmy)
            if dd < best_medkit_dist:
                best_medkit_dist = dd
                medkit_target = medkit

        for gun in state.gun_spawns():
            dgx = gun["x"] - x
            dgy = gun["y"] - y
            dd = math.sqrt(dgx * dgx + dgy * dgy)
            if dd < best_gun_dist:
                best_gun_dist = dd
                gun_target = gun

        want_gun = current_gun is None or current_damage < 12
        if gun_target is not None and current_gun is not None:
            gun_damage = state.get_weapon_stat(gun_target["weapon_id"], "damage") or 0
            gun_range = state.get_weapon_stat(gun_target["weapon_id"], "effective_range") or 0
            want_gun = want_gun or gun_damage >= current_damage + 4 or gun_range >= current_range + 120

        if health < 110.0 and medkit_target is not None:
            tx = medkit_target["x"]
            desired_dir = -1 if tx < x else 1
            if desired_dir < 0:
                move_left()
            else:
                move_right()
            if fuel > 8.0 and state.distance_to_obstacle(math.pi if desired_dir < 0 else 0.0, max_distance=64.0, step=4.0) < 18.0:
                jetpack()
            pickup()
        elif want_gun and gun_target is not None:
            tx = gun_target["x"]
            desired_dir = -1 if tx < x else 1
            if desired_dir < 0:
                move_left()
            else:
                move_right()
            if fuel > 8.0 and state.distance_to_obstacle(math.pi if desired_dir < 0 else 0.0, max_distance=64.0, step=4.0) < 18.0:
                jetpack()
            pickup_gun(state)
        else:
            front_angle = math.pi if roam_dir < 0 else 0.0
            front_dist = state.distance_to_obstacle(front_angle, max_distance=64.0, step=4.0)
            if front_dist < 18.0 or roam_ticks <= 0:
                roam_dir = -roam_dir
                roam_ticks = 180
                if fuel > 8.0:
                    jetpack()

            roam_ticks -= 1
            if roam_dir < 0:
                move_left()
            else:
                move_right()

            roam_target = math.pi if roam_dir < 0 else 0.0
            roam_err = roam_target - aim
            if roam_err > math.pi:
                roam_err -= 2.0 * math.pi
            elif roam_err < -math.pi:
                roam_err += 2.0 * math.pi
            if abs(roam_err) > 0.05 and roam_ticks % 8 == 0:
                if roam_err > 0:
                    aim_right()
                else:
                    aim_left()
            if fuel > 10.0 and roam_ticks % 55 == 0:
                jetpack()

    moved = math.sqrt((x - last_x) * (x - last_x) + (y - last_y) * (y - last_y))
    if moved < 1.5:
        stuck += 1
    else:
        stuck = 0

    if stuck > 18:
        roam_dir = -roam_dir
        evade_dir = -evade_dir
        if fuel > 6.0:
            jetpack()
        stuck = 0

    memory = f"{roam_dir},{roam_ticks},{strafe_dir},{strafe_ticks},{grenade_cd},{evade_dir},{evade_ticks},{stuck},{int(x)},{int(y)}"
    return memory[:100]
