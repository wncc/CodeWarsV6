# scripts/simple_bot.py

def run(state, memory):

    x, y = state.my_position()
    enemies = state.enemy_positions()

    if enemies:
        ex, ey = enemies[0]

        if ex < x:
            move_left()
            aim_left()
        else:
            move_right()
            aim_right()

        shoot()

    return memory

