import pygame
import threading
import importlib
import numpy as np
import os
from client import Network
import time
from weapons import WEAPONS, get_grenade
from weapon_renderer import WeaponRenderer
from weapon_effects import WeaponEffectsManager
import config
from scripts.bot import Bot

class PlayerClient:
    def __init__(self, script_name=None, render=True, W=800, H=600):

        self.render_enabled = render

        # ---- Only initialize pygame window in main thread ----
        if self.render_enabled:
            self.screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
            pygame.display.set_caption("PyTanks")
            self.font = pygame.font.SysFont(None, 24)
            self.hud_font = pygame.font.SysFont(None, 38)

        self.name = script_name if script_name is not None else "Keyboard"
        self.join_server()

        # ---- Input provider ----
        if script_name is not None:
            self.input_provider = Bot(self.ID, script_name)
        else:
            self.input_provider = None

        # ---- Rendering-only resources ----
        if self.render_enabled:
            self.map_width = self.grid_w * self.grid_size
            self.map_height = self.grid_h * self.grid_size
            self.world_surface = pygame.Surface((self.map_width, self.map_height)).convert()
            self.map_background = self._load_map_background()
            self.gas_cloud_sprite = self._create_gas_cloud_sprite(256)

            initial_w, initial_h = self._compute_initial_window_size()
            self.screen = pygame.display.set_mode((initial_w, initial_h), pygame.RESIZABLE)

            # Load player sprite frames for animation
            self.player_frames = [
                pygame.image.load("assets/character/character1.png").convert_alpha(),
                pygame.image.load("assets/character/character2.png").convert_alpha(),
                pygame.image.load("assets/character/character3.png").convert_alpha(),
                pygame.image.load("assets/character/character4.png").convert_alpha(),
            ]
            
            # Scale all frames
            self.player_frames = [
                pygame.transform.scale(frame, (40, 40))
                for frame in self.player_frames
            ]
            
            # Animation tracking
            self.player_anim_timers = [0] * 8
            self.prev_positions = [(0, 0)] * 8
            self.animation_speed = 6

            self.weapon_renderer = WeaponRenderer()
            self.effects_manager = WeaponEffectsManager()
            # Remove single bullet_sprite - will load dynamically per weapon
            self.player_weapons = [WEAPONS[1] for _ in range(8)]
            
            # Track previous state for effect detection
            self.prev_shooting = np.zeros(8, dtype=bool)
            self.prev_bullets = {}
            self.prev_ammo = {}
            self.prev_grenades = {}

        self.run_game()

        if self.render_enabled:
            self.quit_game()

    def get_player_name(self):
        self.name = ""
        while not (0 < len(self.name) < 20):
            self.name = input("Please enter your name: ")

    def join_server(self):
        self.server = Network()
        self.ID = self.server.connect(self.name)
        self.collision_map, self.grid_w, self.grid_h, self.grid_size = self.server.get_collision_map()
        self.running = True
        print("Connected to server, player ID:", self.ID)
    
    def _get_barrel_distance(self, weapon_id):
        """Get distance from player center to gun barrel tip for muzzle flash positioning"""
        barrel_distances = {
            1: 35, 2: 35, 6: 36,  # Pistols
            7: 34, 8: 33, 9: 34,  # SMGs
            0: 38, 4: 39, 12: 38, 13: 39,  # Assault Rifles
            3: 42, 5: 45,  # Snipers
            10: 37, 11: 41, 14: 40,  # Special weapons
        }
        return barrel_distances.get(weapon_id, 37)
    
    def _get_barrel_offset(self, weapon_id):
        """Get x,y offset adjustments for specific weapons (in pixels)"""
        offsets = {
            8: (6, 4),  # UZI: offset for better positioning
        }
        return offsets.get(weapon_id, (0, 0))

    def _load_map_background(self):
        """Load and scale the map background image to match world dimensions."""
        map_name = str(config.DEFAULT_MAP).strip().lower()
        alias_candidates = {
            "catacombs": ["catacomb", "catacombs"],
            "outpost": ["outpost"],
        }

        name_candidates = [map_name] + alias_candidates.get(map_name, [])
        bg_candidates = [
            os.path.join("assets", f"{name}_final.png") for name in name_candidates
        ]
        bg_candidates += [
            os.path.join("assets", f"{name} final.png") for name in name_candidates
        ]

        for bg_path in bg_candidates:
            if os.path.exists(bg_path):
                try:
                    bg = pygame.image.load(bg_path).convert()
                    return pygame.transform.smoothscale(bg, (self.map_width, self.map_height))
                except pygame.error:
                    continue

        return None

    def _create_gas_cloud_sprite(self, size=256):
        """Create a soft, foggy gas cloud sprite procedurally (no PNG dependency)."""
        sprite = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2

        # Layer many translucent circles to create a blurred cloud look.
        for _ in range(180):
            angle = np.random.uniform(0, 2 * np.pi)
            distance = np.random.uniform(0, size * 0.28)
            cx = int(center + np.cos(angle) * distance)
            cy = int(center + np.sin(angle) * distance)
            r = int(np.random.uniform(size * 0.07, size * 0.18))

            # Slight color variation gives a natural toxic cloud feel.
            g = int(np.random.uniform(175, 235))
            color = (
                int(np.random.uniform(70, 120)),
                g,
                int(np.random.uniform(50, 95)),
                int(np.random.uniform(40, 95)),
            )
            pygame.draw.circle(sprite, color, (cx, cy), max(2, r))

        # Green center glow (avoid white-looking core).
        pygame.draw.circle(sprite, (70, 220, 95, 120), (center, center), int(size * 0.23))
        pygame.draw.circle(sprite, (40, 180, 70, 90), (center, center), int(size * 0.16))
        return sprite

    def _draw_gas_cloud(self, ex, ey, radius, time_factor):
        """Draw animated layered gas cloud from the procedural sprite."""
        if self.gas_cloud_sprite is None:
            return

        diameter = max(4, int(radius * 2))
        main = pygame.transform.smoothscale(self.gas_cloud_sprite, (diameter, diameter))

        pulse = 0.92 + 0.08 * np.sin(time_factor * 0.004)
        pulse_d = max(4, int(diameter * pulse))
        pulse_layer = pygame.transform.smoothscale(self.gas_cloud_sprite, (pulse_d, pulse_d))

        drift = max(1, int(radius * 0.08))
        ox = int(np.cos(time_factor * 0.002) * drift)
        oy = int(np.sin(time_factor * 0.0027) * drift)

        main.set_alpha(185)
        pulse_layer.set_alpha(145)

        main_rect = main.get_rect(center=(int(ex), int(ey)))
        pulse_rect = pulse_layer.get_rect(center=(int(ex + ox), int(ey + oy)))
        self.screen.blit(main, main_rect.topleft)
        self.screen.blit(pulse_layer, pulse_rect.topleft)

        # Intentionally no ring/outline; cloud-only visual.

    def run_game(self):

        if self.render_enabled:
            clock = pygame.time.Clock()
        else:
            clock = None

        keyboard_input = np.zeros(10, dtype=bool)

        while self.running:
            if self.render_enabled:
                dt = clock.tick(config.GAME_FPS) / 1000.0  # Delta time in seconds
            else: 
                time.sleep(1 / config.GAME_FPS)
                dt = 1.0 / config.GAME_FPS

            if self.render_enabled:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.VIDEORESIZE:
                        self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            result = self.server.send(keyboard_input)

            if result is None or result[0] is None:
                self.running = False
                break

            # Unpack result (now includes gas_data + grenade_data)
            if len(result) == 5:
                game_world, gun_spawns, inventory_data, gas_data, grenade_data = result
            elif len(result) == 3:
                # Fallback for older server (backward compatibility)
                game_world, gun_spawns, inventory_data = result
                gas_data = np.zeros((0, 4), dtype=np.float64)
                grenade_data = np.zeros((8, 4), dtype=np.float64)
            else:
                self.running = False
                break

            if self.input_provider is not None:
                self.input_provider.update_state(
                    game_world,
                    gun_spawns,
                    inventory_data,
                    self.collision_map,
                    self.grid_size
                )
                keyboard_input = self.input_provider.get_action()
            else:
                keyboard_input = np.zeros(12, dtype=bool)
                keys = pygame.key.get_pressed()
                # [W=jetpack, A=left, D=right, UP=aim up, DOWN=aim down, LEFT=aim left, RIGHT=aim right, SPACE=shoot, R=reload, S=switch gun, G=grenade, C=change grenade type]

                if keys[pygame.K_w]: keyboard_input[0] = 1
                if keys[pygame.K_a]: keyboard_input[1] = 1
                if keys[pygame.K_d]: keyboard_input[2] = 1
                if keys[pygame.K_UP]: keyboard_input[3] = 1
                if keys[pygame.K_DOWN]: keyboard_input[4] = 1
                if keys[pygame.K_LEFT]: keyboard_input[5] = 1
                if keys[pygame.K_RIGHT]: keyboard_input[6] = 1
                if keys[pygame.K_SPACE]: keyboard_input[7] = 1
                if keys[pygame.K_r]: keyboard_input[8] = 1
                if keys[pygame.K_s]: keyboard_input[9] = 1
                if keys[pygame.K_g]: keyboard_input[10] = 1
                if keys[pygame.K_c]: keyboard_input[11] = 1
          
            # Update player weapons from inventory data
            if self.render_enabled and inventory_data is not None:
                for i in range(8):
                    gun1_id, gun2_id, current_slot = inventory_data[i]
                    # For now, just track current gun (client-side full inventory tracking can be added later)
                    if gun1_id >= 0:
                        if current_slot == 0:
                            current_gun_id = gun1_id
                        elif gun2_id >= 0:
                            current_gun_id = gun2_id
                        else:
                            current_gun_id = gun1_id
                        
                        # Update player's displayed weapon
                        from weapons import WEAPONS
                        if current_gun_id in WEAPONS:
                            self.player_weapons[i] = WEAPONS[current_gun_id]
            
            # Update player weapon ammo from server (synced via world_data columns 9 and 10)
            if self.render_enabled:
                for i in range(8):
                    if game_world[i, 0] == 1:  # if player is active
                        self.player_weapons[i].current_ammo = int(game_world[i, 9])
                        self.player_weapons[i].total_ammo = int(game_world[i, 10])
                
                # Update visual effects
                self.effects_manager.update(dt)
                
                # Detect muzzle flashes (when ammo decreases = shot fired)
                for i in range(8):
                    if game_world[i, 0] == 1:
                        current_ammo = int(game_world[i, 9])
                        if i in self.prev_ammo and current_ammo < self.prev_ammo[i]:
                            # Shot fired! Add muzzle flash
                            x, y, angle = game_world[i, 1], game_world[i, 2], game_world[i, 3]
                            weapon_id = self.player_weapons[i].gun_id
                            
                            # Calculate muzzle flash position at gun barrel
                            barrel_dist = self._get_barrel_distance(weapon_id)
                            offset_x, offset_y = self._get_barrel_offset(weapon_id)
                            flash_x = x + barrel_dist * np.cos(angle) + offset_x * np.cos(angle + np.pi/2)
                            flash_y = y + barrel_dist * np.sin(angle) + offset_y * np.sin(angle + np.pi/2)
                            
                            self.effects_manager.add_muzzle_flash(flash_x, flash_y, angle, weapon_id)
                        
                        self.prev_ammo[i] = current_ammo
                
                # Detect bullet impacts (when bullets disappear)
                active_bullets = {}
                for b in range(8, 48):
                    if game_world[b, 0] == 1:
                        active_bullets[b] = (game_world[b, 1], game_world[b, 2], game_world[b, 9])
                
                # Check for bullets that disappeared (impact)
                for b_id, (prev_x, prev_y, owner_id) in self.prev_bullets.items():
                    if b_id not in active_bullets:
                        # Bullet disappeared - add impact effect
                        if 0 <= owner_id < 8:
                            weapon_id = self.player_weapons[int(owner_id)].gun_id
                            self.effects_manager.add_impact_effect(prev_x, prev_y, weapon_id)
                
                self.prev_bullets = active_bullets

                # Detect grenade explosions (grenade slot disappeared this frame)
                active_grenades = {}
                for g in range(48, 55):
                    if game_world[g, 0] == 1:
                        active_grenades[g] = (game_world[g, 1], game_world[g, 2], int(game_world[g, 10]))

                for g_id, (prev_x, prev_y, grenade_type) in self.prev_grenades.items():
                    if g_id not in active_grenades:
                        self.effects_manager.add_grenade_explosion(prev_x, prev_y, grenade_type)

                self.prev_grenades = active_grenades
            
            if self.render_enabled:
                self.render(game_world, gun_spawns, gas_data, grenade_data)

    def render(self, game_world, gun_spawns, gas_data, grenade_data):
        display_surface = self.screen
        self.screen = self.world_surface

        # Draw map art as background; collisions still come from collision_map on server.
        if self.map_background is not None:
            self.screen.blit(self.map_background, (0, 0))
        else:
            self.screen.fill(config.BACKGROUND_COLOR)
        
        # Draw gun spawns with actual gun images
        for spawn in gun_spawns:
            x, y, weapon_id, is_active = spawn
            if is_active == 1:
                # Draw glow effect behind gun
                pygame.draw.circle(self.screen, config.GUN_SPAWN_GLOW_COLOR, (int(x), int(y)), 18)
                
                # Get and draw the gun sprite
                weapon_id_int = int(weapon_id)
                from weapons import WEAPONS
                if weapon_id_int in WEAPONS:
                    weapon = WEAPONS[weapon_id_int]
                    gun_sprite = self.weapon_renderer.load_gun_sprite(weapon.sprite_file)
                    if gun_sprite:
                        # Scale the gun sprite for pickup display (similar to player size)
                        gun_width = gun_sprite.get_width()
                        gun_height = gun_sprite.get_height()
                        target_size = config.GUN_SPAWN_SCALE
                        scale_factor = target_size / max(gun_width, gun_height)
                        scaled_sprite = pygame.transform.scale(gun_sprite, 
                            (int(gun_width * scale_factor), int(gun_height * scale_factor)))
                        
                        # Center the gun sprite at spawn location
                        sprite_x = int(x) - scaled_sprite.get_width() // 2
                        sprite_y = int(y) - scaled_sprite.get_height() // 2
                        self.screen.blit(scaled_sprite, (sprite_x, sprite_y))
                    else:
                        # Fallback if sprite not found
                        pygame.draw.circle(self.screen, (255, 255, 0), (int(x), int(y)), 8)
                        text = self.font.render("G", True, (0, 0, 0))
                        self.screen.blit(text, (int(x) - 6, int(y) - 8))
        
        for i in range(8):
            if game_world[i, 0] == 0:
                continue

            color = config.PLAYER_COLOR
            if i == self.ID:
                    color = config.SELF_COLOR
            
            # Get player position and state
            px = int(game_world[i, 1])
            py = int(game_world[i, 2])
            theta = game_world[i, 3]
            fuel = game_world[i, 6]
            
            # Detect movement and jetpack usage
            prev_x, prev_y = self.prev_positions[i]
            using_jet = fuel < 99.9   # jetpack active
            moving = abs(px - prev_x) > 1
            
            # Walking animation only if moving AND not jetpacking
            if moving and not using_jet:
                self.player_anim_timers[i] += 1
                frame_index = 1 + (self.player_anim_timers[i] // self.animation_speed) % 2
            else:
                frame_index = 0
            
            # Update previous position
            self.prev_positions[i] = (px, py)
            
            # Draw character sprite
            sprite = self.player_frames[frame_index]
            
            # Flip based on facing direction
            if np.cos(theta) < 0:
                sprite = pygame.transform.flip(sprite, True, False)
            
            rect = sprite.get_rect(center=(px, py))
            self.screen.blit(sprite, rect.topleft)
            
            # Draw weapon instead of aim line
            self.weapon_renderer.draw_gun(
                self.screen, 
                px, 
                py, 
                theta,  # angle
                self.player_weapons[i],
                tank_radius=12.5
            )
            
            # Draw jetpack indicator (orange dot below player when fuel is being used)
            # If fuel is decreasing (not at max), show jetpack is active
            fuel = game_world[i, 6]
            if fuel < 99.9:  # jetpack was used recently
                pygame.draw.circle(self.screen, (255, 165, 0), (int(game_world[i, 1]), int(game_world[i, 2] + 17.5)), 5)

            # Draw small health bar above each player
            health = game_world[i, 7]
            if health is not None:
                # clamp and compute percent
                health_percent = max(0.0, min(1.0, health / 200.0))
                hb_x = int(game_world[i, 1]) - 20
                hb_y = int(game_world[i, 2]) - 40
                hb_w, hb_h = 40, 6
                pygame.draw.rect(self.screen, (50, 50, 50), (hb_x, hb_y, hb_w, hb_h))
                pygame.draw.rect(self.screen, (255, 0, 0), (hb_x, hb_y, int(hb_w * health_percent), hb_h))
                pygame.draw.rect(self.screen, (255, 255, 255), (hb_x, hb_y, hb_w, hb_h), 1)
        
        # Draw fuel meter for local player
        if game_world[self.ID, 0] == 1:
            fuel = game_world[self.ID, 6]
            fuel_percent = fuel / 100.0
            # Draw fuel bar in top-left corner
            bar_x, bar_y = 10, 10
            bar_width, bar_height = 620, 52
            # Background (empty)
            pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            # Fuel level (cyan color like Mini Militia)
            fuel_width = int(bar_width * fuel_percent)
            pygame.draw.rect(self.screen, (0, 255, 255), (bar_x, bar_y, fuel_width, bar_height))
            # Border
            pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)

            # Draw health bar below fuel
            health = game_world[self.ID, 7]
            health_percent = max(0.0, min(1.0, health / 200.0))
            hbar_x, hbar_y = 10, bar_y + bar_height + 10
            hbar_w, hbar_h = 620, 52
            pygame.draw.rect(self.screen, (50, 50, 50), (hbar_x, hbar_y, hbar_w, hbar_h))
            pygame.draw.rect(self.screen, (255, 0, 0), (hbar_x, hbar_y, int(hbar_w * health_percent), hbar_h))
            pygame.draw.rect(self.screen, (255, 255, 255), (hbar_x, hbar_y, hbar_w, hbar_h), 2)

            # Draw score at top-center (always visible)
            score = int(game_world[self.ID, 8])
            score_surf = self.font.render(f"Score: {score}", True, (255, 255, 255))
            sx = self.screen.get_width() // 2 - score_surf.get_width() // 2
            self.screen.blit(score_surf, (sx, 10))
            
            # Draw weapon name and ammo counter
            weapon = self.player_weapons[self.ID]
            weapon_name_y = hbar_y + hbar_h + 12
            weapon_name_surf = self.hud_font.render(weapon.name, True, (255, 255, 255))
            self.screen.blit(weapon_name_surf, (10, weapon_name_y))
            ammo_y = weapon_name_y + 36
            self.weapon_renderer.draw_ammo_counter(self.screen, weapon, 10, ammo_y, self.hud_font)
            # Draw grenade counter
            self.weapon_renderer.draw_grenade_counter(self.screen, grenade_data, self.ID, 10, ammo_y + 36, self.hud_font)
        
        # Draw bullets with trails (Mini Militia style)
        for i in range(8, 48):
            if game_world[i, 0] == 0:
                continue
            
            bx, by = int(game_world[i, 1]), int(game_world[i, 2])
            bullet_angle = game_world[i, 3]
            weapon_id = int(game_world[i, 10])  # Get weapon ID for this bullet
            
            # Draw bullet trail (line behind bullet)
            trail_length = 15  # Trail length in pixels
            trail_start_x = bx - int(np.cos(bullet_angle) * trail_length)
            trail_start_y = by - int(np.sin(bullet_angle) * trail_length)
            pygame.draw.line(self.screen, (255, 255, 100), (trail_start_x, trail_start_y), (bx, by), 2)
            
            # Get weapon-specific bullet sprite
            bullet_sprite = self.weapon_renderer.get_bullet_sprite(weapon_id)
            
            # Draw bullet sprite if available
            if bullet_sprite:
                # Scale bullet sprite to small size
                bullet_size = 6
                scaled_bullet = pygame.transform.scale(bullet_sprite, (bullet_size, bullet_size))
                # Rotate bullet to match trajectory
                angle_degrees = np.degrees(bullet_angle)
                rotated_bullet = pygame.transform.rotate(scaled_bullet, -angle_degrees)
                # Center the sprite
                rect = rotated_bullet.get_rect(center=(bx, by))
                self.screen.blit(rotated_bullet, rect.topleft)
            else:
                # Fallback: draw circle with glow
                pygame.draw.circle(self.screen, (255, 255, 150), (bx, by), 3)
                pygame.draw.circle(self.screen, (255, 255, 255), (bx, by), 2)

        # Draw grenades (rows 48-54 in world_data)
        for i in range(48, 55):
            if game_world[i, 0] == 1:
                gx = int(game_world[i, 1])  # x position
                gy = int(game_world[i, 2])  # y position
                grenade_id = int(game_world[i, 10])  # grenade type ID

                # Get grenade definition to access sprite file
                grenade = get_grenade(grenade_id)
                sprite_file = grenade.sprite_file if grenade else None

                self.weapon_renderer.draw_grenade(
                    self.screen,
                    gx,
                    gy,
                    grenade_type=grenade_id,
                    sprite_file=sprite_file,
                    is_armed=False  # Armed state not transmitted to client yet
                )

        # Draw gas effects (visual indicator for gas zones)
        for effect in gas_data:
            if len(effect) >= 4:
                ex, ey, radius, duration = effect
                if duration > 0:
                    time_factor = time.time() * 1000
                    self._draw_gas_cloud(ex, ey, radius, time_factor)
                    

        # Draw visual effects (muzzle flashes and impacts)
        self.effects_manager.draw(self.screen)

        self._present_frame(display_surface)
        self.screen = display_surface

    def _compute_initial_window_size(self):
        display_info = pygame.display.Info()
        desktop_w = max(800, display_info.current_w)
        desktop_h = max(600, display_info.current_h - 80)
        return min(self.map_width, desktop_w), min(self.map_height, desktop_h)

    def _present_frame(self, display_surface):
        window_w, window_h = display_surface.get_size()

        if window_w <= 0 or window_h <= 0:
            return

        scale = min(window_w / self.map_width, window_h / self.map_height)
        scaled_w = max(1, int(self.map_width * scale))
        scaled_h = max(1, int(self.map_height * scale))

        # Letterbox the full map so it always fits inside the window.
        viewport = pygame.transform.smoothscale(self.world_surface, (scaled_w, scaled_h))
        offset_x = (window_w - scaled_w) // 2
        offset_y = (window_h - scaled_h) // 2

        display_surface.fill((0, 0, 0))
        display_surface.blit(viewport, (offset_x, offset_y))
        pygame.display.update()


    def quit_game(self):
        self.server.disconnect()
        pygame.quit()
        quit()
	
def launch_bot(script_name):
    PlayerClient(script_name=script_name, render=False)

if __name__ == "__main__":

    pygame.init()

    threads = []

    # 1️⃣ Start headless bots in background threads
    for script in config.BOT_SCRIPTS:
        t = threading.Thread(
            target=launch_bot,
            args=(script,),
            daemon=True
        )
        t.start()
        threads.append(t)

    # 2️⃣ Run keyboard player OR first bot in MAIN thread
    if config.ENABLE_KEYBOARD_PLAYER:
        PlayerClient(script_name=None, render=True)
    else:
        PlayerClient(script_name=config.BOT_SCRIPTS[0], render=True)
