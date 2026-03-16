# Your bot logic goes here.
# Rules: only define run(state, memory). No imports, no classes.

def run(state, memory):
    # Memory layout: dir,roam_ticks,stuck,grenade_cd,strafe_dir,strafe_ticks,last_x,last_y
    roam_dir = 1
    roam_ticks = 120
    stuck = 0
    grenade_cd = 0
    strafe_dir = 1
    strafe_ticks = 0
    last_x = 0.0
    last_y = 0.0

    if memory:
        try:
            parts = memory.split(",")
            if len(parts) >= 8:
                roam_dir = int(parts[0]) or 1
                roam_ticks = int(parts[1])
                stuck = int(parts[2])
                grenade_cd = int(parts[3])
                strafe_dir = int(parts[4]) or 1
                strafe_ticks = int(parts[5])
                last_x = float(parts[6])
                last_y = float(parts[7])
        except Exception:
            roam_dir = 1
            roam_ticks = 120
            stuck = 0
            grenade_cd = 0
            strafe_dir = 1
            strafe_ticks = 0
            last_x = 0.0
            last_y = 0.0

    x, y = state.my_position()
    fuel = state.my_fuel()
    ammo_cur, _ = state.my_ammo()
    aim = state.my_aim_angle()
    health = state.my_health()
    grenades = state.my_grenades()

    if grenade_cd > 0:
        grenade_cd -= 1

    # Immediate threat: nearby grenades -> move away + jetpack.
    for g in state.active_grenades():
        dx = x - g["x"]
        dy = y - g["y"]
        d = (dx * dx + dy * dy) ** 0.5
        if d < 140.0:
            if dx < 0:
                move_left()
            else:
                move_right()
            if fuel > 6.0:
                jetpack()
            memory = f"{roam_dir},{roam_ticks},{stuck},{grenade_cd},{strafe_dir},{strafe_ticks},{int(x)},{int(y)}"
            return memory[:100]

    enemies = state.enemy_positions()

    if enemies:
        # Pick closest enemy.
        target = None
        best_d = 1e9
        for ex, ey in enemies:
            dx = ex - x
            dy = ey - y
            d = (dx * dx + dy * dy) ** 0.5
            if d < best_d:
                best_d = d
                target = (ex, ey, dx, dy, d)

        if target is not None:
            ex, ey, dx, dy, dist = target
            angle = math.atan2(dy, dx)
            err = angle - aim
            if err > math.pi:
                err -= 2.0 * math.pi
            elif err < -math.pi:
                err += 2.0 * math.pi

            if err > 0.05:
                aim_right()
            elif err < -0.05:
                aim_left()

            desired_dir = -1 if dx < 0 else 1
            front_angle = math.pi if desired_dir == -1 else 0.0
            front_dist = state.distance_to_obstacle(front_angle, max_distance=64.0, step=4.0)
            if front_dist < 18.0 and fuel > 6.0:
                jetpack()

            # Movement: close in if far, back off if too close, otherwise strafe.
            if dist > 260.0:
                if desired_dir == -1:
                    move_left()
                else:
                    move_right()
            elif dist < 120.0:
                if desired_dir == -1:
                    move_right()
                else:
                    move_left()
            else:
                if strafe_ticks <= 0:
                    strafe_dir = -strafe_dir
                    strafe_ticks = 60
                strafe_ticks -= 1
                if strafe_dir == -1:
                    move_left()
                else:
                    move_right()

            # Line of sight check.
            obs = state.distance_to_obstacle(angle, max_distance=2000.0, step=4.0)
            blocked = obs < max(0.0, dist - 16.0)

            if (not blocked) and abs(err) < 0.18:
                if ammo_cur <= 0:
                    reload()
                else:
                    shoot()
            elif ammo_cur <= 0:
                reload()

            # Grenade usage on close/clustered target.
            if (not blocked) and dist < 220.0 and grenade_cd == 0:
                desired_type = 1  # frag
                if grenades["gas"] > 0 and dist < 180.0:
                    desired_type = 3
                elif grenades["frag"] <= 0 and grenades["gas"] > 0:
                    desired_type = 3
                elif grenades["frag"] <= 0 and grenades["proxy"] > 0:
                    desired_type = 2

                if grenades["frag"] + grenades["gas"] + grenades["proxy"] > 0:
                    if grenades["selected_type"] != desired_type:
                        change_grenade_type()
                    else:
                        throw_grenade()
                        grenade_cd = 45

            pickup()

    else:
        # Look for nearby medkits or guns within sensor radius.
        target = None
        best_d = 1e9

        if health < 120.0:
            for m in state.medkit_spawns():
                dx = m["x"] - x
                dy = m["y"] - y
                d = (dx * dx + dy * dy) ** 0.5
                if d < best_d:
                    best_d = d
                    target = (m["x"], m["y"])

        if target is None:
            for g in state.gun_spawns():
                dx = g["x"] - x
                dy = g["y"] - y
                d = (dx * dx + dy * dy) ** 0.5
                if d < best_d:
                    best_d = d
                    target = (g["x"], g["y"])

        if target is not None:
            tx, ty = target
            dx = tx - x
            desired_dir = -1 if dx < 0 else 1
            front_angle = math.pi if desired_dir == -1 else 0.0
            front_dist = state.distance_to_obstacle(front_angle, max_distance=64.0, step=4.0)
            if front_dist < 18.0 and fuel > 6.0:
                jetpack()

            if desired_dir == -1:
                move_left()
            else:
                move_right()

            pickup()
        else:
            front_angle = math.pi if roam_dir == -1 else 0.0
            front_dist = state.distance_to_obstacle(front_angle, max_distance=64.0, step=4.0)
            if front_dist < 18.0 or roam_ticks <= 0:
                roam_dir = -roam_dir
                roam_ticks = 120
                if fuel > 8.0:
                    jetpack()

            roam_ticks -= 1

            if roam_dir == -1:
                move_left()
            else:
                move_right()

            if roam_ticks % 50 == 0 and fuel > 8.0:
                jetpack()

    moved = ((x - last_x) * (x - last_x) + (y - last_y) * (y - last_y)) ** 0.5
    if moved < 1.5:
        stuck += 1
    else:
        stuck = 0

    if stuck > 18 and fuel > 6.0:
        jetpack()
        roam_dir = -roam_dir
        stuck = 0

    memory = f"{roam_dir},{roam_ticks},{stuck},{grenade_cd},{strafe_dir},{strafe_ticks},{int(x)},{int(y)}"
    return memory[:100]
