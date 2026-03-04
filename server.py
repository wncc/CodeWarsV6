import socket
import threading
import time
import numpy as np
import pygame
import os
from weapons import WEAPONS, get_weapon
from gun_spawner import GunSpawner, PlayerInventory
import config

class Server:
    def grenade_effect_active_after_explosion(self, grenade_slot):
        """True when a grenade slot is no longer active but its lingering effect still exists."""
        if 48 <= grenade_slot <= 54 and self.world_data[grenade_slot, 0] == 1:
            return False
        return any(
            effect.get('source_slot') == grenade_slot and effect.get('duration', 0) > 0
            for effect in self.gas_effects.values()
        )
    
    def grenade_damage(self, distance, max_damage, radius, falloff=2):
        if distance >= radius:
            return 0.0
        damage = max_damage * (1 - (distance / radius))
        return damage

    def throw_grenade(self, player_id, grenade_id, throw_angle, throw_power):
        """
        Spawns a grenade with gravity-based arc.
        - player_id: int, the player throwing
        - grenade_id: int, type of grenade (from weapons.py)
        - throw_angle: float, angle in radians
        - throw_power: float, initial speed
        """
        from weapons import get_grenade
        # Find a free grenade slot (rows 48-54)
        for i in range(48, 55):
            if self.world_data[i, 0] == 0:
                # Get player position
                px, py = self.world_data[player_id, 1], self.world_data[player_id, 2]
                vx = throw_power * np.cos(throw_angle)
                vy = throw_power * np.sin(throw_angle)
                grenade = get_grenade(grenade_id)
                if grenade is None:
                    return False
                # Fill world_data for grenade
                self.world_data[i, 0] = 1  # active
                self.world_data[i, 1] = px
                self.world_data[i, 2] = py
                self.world_data[i, 3] = throw_angle  # store angle if needed
                self.world_data[i, 4] = vx  # vx
                self.world_data[i, 5] = vy  # vy
                self.world_data[i, 6] = grenade.blast_radius
                self.world_data[i, 7] = grenade.damage
                self.world_data[i, 8] = grenade.effect_time
                self.world_data[i, 9] = player_id
                self.world_data[i, 10] = grenade_id
                # Store fuse timer in a dict for each grenade slot
                if not hasattr(self, 'grenade_fuse_timers'):
                    self.grenade_fuse_timers = {}
                # proxy grenades should arm after 2 seconds regardless of their config
                if grenade.is_proxy:
                    self.grenade_fuse_timers[i] = 2.0
                    # ensure we have an armed-state tracker
                    if not hasattr(self, 'proxy_armed'):
                        self.proxy_armed = set()
                else:
                    self.grenade_fuse_timers[i] = grenade.fuse_time
                return True
        return False  # No free slot
    
    def __init__(self):
        PORT = config.SERVER_PORT
        if not self._start_server(PORT):
            return

        self.setup_game()

        thread = threading.Thread(target=self.add_players, daemon=True)
        thread.start()

        self.player_lock = threading.Lock()

        self.run_game()

    def _start_server(self, PORT):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        HOST_NAME = socket.gethostname()
        SERVER_IP = socket.gethostbyname(HOST_NAME)

        try:
            self.server_socket.bind((SERVER_IP, PORT))
        except socket.error as e:
            print(str(e))
            print("[SERVER] Server could not start")
            return False

        self.server_socket.listen()

        print(f"[SERVER] Server Started with local ip {SERVER_IP}")
        return True

    def setup_game(self):
        # Grenade cooldown per player (seconds)
        self.player_grenade_cooldown = np.zeros(8, dtype=np.float64)
        self.player_respawn_cooldown = np.zeros(8, dtype=np.float64)
        self.player_count = 0
        # world_data columns (per row):
        # 0:is_alive, 1:x, 2:y, 3:theta, 4:v, 5:omega_or_traveled, 6:fuel, 7:health_or_damage, 8:score, 9:current_ammo, 10:total_ammo_or_weapon_id
        # for tanks: column 6 = fuel, 7 = health, 8 = score, 9 = current_ammo, 10 = total_ammo
        # for bullets: column 5 = distance traveled, 7 = snapshot damage, 9 = owner id, 10 = weapon id
        self.world_data = np.zeros((55, 11), dtype=np.float64)
        self.player_inputs = np.zeros((8, 12), dtype=np.int32)  # 12 inputs: W,A,D,UP,DOWN,LEFT,RIGHT,SPACE,R,S,G,C
        self.grenade_data = np.zeros((10, 4), dtype=np.float64)  # separate array for grenades (slots 48-54 in world_data)
        self.grenade_data[:8, 0] = 1  # default selected grenade type: frag
        self.grenade_data[:8, 1] = config.FRAG_GRENADE_COUNT
        self.grenade_data[:8, 2] = config.PROXY_GRENADE_COUNT
        self.grenade_data[:8, 3] = config.GAS_GREANADE_COUNT

        # Load constants from config
        TANK_V = config.TANK_SPEED
        TANK_OMEGA = config.TANK_ROTATION_SPEED
        BULLET_V = config.BULLET_SPEED

        self.world_data[:8, 4] = TANK_V
        self.world_data[:8, 5] = TANK_OMEGA
        self.world_data[8:, 4] = BULLET_V
        # per-player vertical velocity for gravity (tanks only)
        self.player_vy = np.zeros(8, dtype=np.float64)
        # screen and tank constants for ground handling
        self.SCREEN_W = 800
        self.SCREEN_H = 600
        self.TANK_RADIUS = config.TANK_VISUAL_RADIUS
        self.COLLISION_RADIUS = config.TANK_COLLISION_RADIUS
        self.GROUND_Y = self.SCREEN_H - self.COLLISION_RADIUS
        self.GRAVITY = config.GRAVITY
        
        # Jetpack system
        self.player_fuel = np.full(8, config.MAX_FUEL, dtype=np.float64)
        self.MAX_FUEL = config.MAX_FUEL
        self.FUEL_CONSUMPTION = config.FUEL_CONSUMPTION
        self.FUEL_RECHARGE = config.FUEL_RECHARGE
        self.JETPACK_THRUST = config.JETPACK_THRUST
        
        # Use column 6 (info) to store fuel for tanks
        self.world_data[:8, 6] = self.player_fuel

        # Health and score per tank
        self.MAX_HEALTH = config.MAX_HEALTH
        self.world_data[:8, 7] = self.MAX_HEALTH  # health
        self.world_data[:8, 8] = 0.0  # score

        # Weapon system - player inventories with dual gun support
        self.player_inventories = [PlayerInventory(starting_weapon_id=config.DEFAULT_STARTING_WEAPON) for _ in range(8)]
        
        # Fire rate cooldown per player (in seconds, tracks time since last shot)
        self.player_fire_cooldown = np.zeros(8, dtype=np.float64)
        # Reload cooldown per player (in seconds, tracks time remaining for reload)
        self.player_reload_cooldown = np.zeros(8, dtype=np.float64)
        # Track previous frame's input state for edge detection
        self.previous_inputs = np.zeros((8, 12), dtype=np.int32)
        self.last_frame_time = time.time()
        
        # Collision map system - grid-based obstacles
        self.GRID_SIZE = config.GRID_SIZE
        
        # Load map from file - this will set GRID_W, GRID_H, and collision_map
        self.current_map_name = config.DEFAULT_MAP
        self.load_map(self.current_map_name)
        
        # Gas grenade effect tracking - stores active gas zones
        # Format: {effect_id: {'x': x, 'y': y, 'radius': radius, 'damage': damage, 'duration': remaining_time}}
        self.gas_effects = {}
        self.gas_effect_counter = 0  # Unique ID for each gas effect
        
        # Initialize gun spawner system
        self.gun_spawner = GunSpawner()
        self.gun_spawner.initialize_map(self.current_map_name)
        
        # Update screen dimensions based on loaded map
        self.SCREEN_W = self.GRID_W * self.GRID_SIZE
        self.SCREEN_H = self.GRID_H * self.GRID_SIZE
        
        # Convert map to bytes for transmission
        self.collision_map_bytes = self.collision_map.tobytes()

    def load_map(self, map_name):
        """Load map from maps/ folder or create default if not found"""
        map_path = os.path.join("maps", f"{map_name}.npy")
        
        if os.path.exists(map_path):
            try:
                self.collision_map = np.load(map_path)
                # Extract dimensions from loaded map
                self.GRID_H, self.GRID_W = self.collision_map.shape
                print(f"[SERVER] Loaded map: {map_name} (dimensions: {self.GRID_W}x{self.GRID_H})")
                return True
            except Exception as e:
                print(f"[SERVER] Error loading map {map_name}: {e}")
        
        # Create default map if file not found
        print(f"[SERVER] Map '{map_name}' not found, creating default map")
        # Use default dimensions if not already set
        if not hasattr(self, 'GRID_W'):
            self.GRID_W = 80
            self.GRID_H = 60
        
        self.collision_map = np.ones((self.GRID_H, self.GRID_W), dtype=np.int32)
        
        # Simple default layout
        self.collision_map[-1, :] = 0  # Ground floor
        if self.GRID_H > 20:
            self.collision_map[20, 5:min(15, self.GRID_W)] = 0  # Left platform
        if self.GRID_H > 15:
            self.collision_map[15, 25:min(35, self.GRID_W)] = 0  # Right platform
        if self.GRID_H > 10:
            self.collision_map[10, 10:min(20, self.GRID_W)] = 0  # Top platform
        
        return False
    
    def is_colliding_with_obstacle(self, x, y, radius):
        """Check if a circle at (x, y) with given radius collides with any obstacle"""
        # Check all grid cells that the circle overlaps
        min_grid_x = max(0, int((x - radius) / self.GRID_SIZE))
        max_grid_x = min(self.GRID_W - 1, int((x + radius) / self.GRID_SIZE))
        min_grid_y = max(0, int((y - radius) / self.GRID_SIZE))
        max_grid_y = min(self.GRID_H - 1, int((y + radius) / self.GRID_SIZE))
        
        for gy in range(min_grid_y, max_grid_y + 1):
            for gx in range(min_grid_x, max_grid_x + 1):
                if self.collision_map[gy, gx] == 0:  # obstacle
                    # Check if circle intersects this grid cell
                    cell_x = gx * self.GRID_SIZE
                    cell_y = gy * self.GRID_SIZE
                    # Find closest point in rectangle to circle center
                    closest_x = max(cell_x, min(x, cell_x + self.GRID_SIZE))
                    closest_y = max(cell_y, min(y, cell_y + self.GRID_SIZE))
                    # Check distance
                    dist = np.sqrt((x - closest_x)**2 + (y - closest_y)**2)
                    if dist < radius:
                        return True
        return False
    
    def find_ground_below(self, x, y):
        """Find the y-coordinate of the first obstacle below position (x, y)"""
        grid_x = int(x / self.GRID_SIZE)
        start_grid_y = int(y / self.GRID_SIZE)
        
        if grid_x < 0 or grid_x >= self.GRID_W:
            return self.GROUND_Y
        
        # If player is above screen, start search from top
        if start_grid_y < 0:
            start_grid_y = -1
        
        # Search downward for first obstacle
        for gy in range(start_grid_y + 1, self.GRID_H):
            if self.collision_map[gy, grid_x] == 0:
                # Found obstacle, return top of this cell minus collision radius
                return gy * self.GRID_SIZE - self.COLLISION_RADIUS
        
        return self.GROUND_Y
    
    def _get_barrel_distance(self, weapon_id):
        """Get distance from player center to gun barrel tip for bullet spawning"""
        barrel_distances = {
            1: 35, 2: 35, 6: 36,  # Pistols
            7: 34, 8: 33, 9: 34,  # SMGs
            0: 38, 4: 39, 12: 38, 13: 39,  # Assault Rifles
            3: 42, 5: 45,  # Snipers
            10: 37, 11: 41, 14: 40,  # Special weapons
        }
        return barrel_distances.get(weapon_id, 37)
    
    def _get_bullet_spawn_offset(self, weapon_id):
        """Get x,y offset adjustments for bullet spawn (in pixels)"""
        offsets = {
            8: (6, 4),  # UZI: 6px forward, 4px perpendicular down
        }
        return offsets.get(weapon_id, (0, 0))
    
    def get_extended_game_state(self):
        """Package world_data, gun spawns, player inventories, gas effects, and grenade data for client"""
        # Gun spawn data: [[x, y, weapon_id, is_active], ...]
        spawn_data = self.gun_spawner.get_spawn_data_for_client()
        
        # Player inventory data: [[gun1_id, gun2_id, current_slot], ...] for 8 players
        inventory_data = np.zeros((8, 3), dtype=np.int32)
        for i in range(8):
            gun_ids = self.player_inventories[i].get_gun_ids()
            inventory_data[i, 0] = gun_ids[0]
            inventory_data[i, 1] = gun_ids[1]
            inventory_data[i, 2] = self.player_inventories[i].current_slot
            
            # Update ammo in world_data for current gun
            current_gun = self.player_inventories[i].get_current_gun()
            self.world_data[i, 9] = current_gun.current_ammo
            self.world_data[i, 10] = current_gun.total_ammo
        
        # Gas effects data: [[x, y, radius, duration], ...] for all active gas zones
        gas_data = np.array([
            [effect['x'], effect['y'], effect['radius'], effect['duration']]
            for effect in self.gas_effects.values()
        ], dtype=np.float64) if self.gas_effects else np.zeros((0, 4), dtype=np.float64)
        
        # Grenade data per player: [selected_type, frag_count, proxy_count, gas_count]
        grenade_data = self.grenade_data[:8].copy()
        
        return self.world_data, spawn_data, inventory_data, gas_data, grenade_data

    def run_game(self):
        MAX_BULLET_DIST = config.MAX_BULLET_DISTANCE

        clock = pygame.time.Clock()
        while True:
            clock.tick(config.SERVER_FPS)
            # Tank movement: left/right using A/D keys (index 1=A, 2=D)
            horizontal_move = (self.player_inputs[:, 2] - self.player_inputs[:, 1]) * self.world_data[:8, 4]
            
            # Check horizontal collisions before moving - allow movement away from obstacles
            for i in range(8):
                if self.world_data[i, 0] == 0:
                    continue
                old_x = self.world_data[i, 1]
                new_x = old_x + horizontal_move[i]
                
                # Check if currently colliding
                currently_colliding = self.is_colliding_with_obstacle(old_x, self.world_data[i, 2], self.COLLISION_RADIUS)
                will_collide = self.is_colliding_with_obstacle(new_x, self.world_data[i, 2], self.COLLISION_RADIUS)
                
                # Allow movement if: not colliding after, OR currently stuck and trying to move away
                if not will_collide or (currently_colliding and not will_collide):
                    self.world_data[i, 1] = new_x
                elif currently_colliding:
                    # Already stuck, allow any movement to try to escape
                    self.world_data[i, 1] = new_x
            
            # Aim control using all 4 arrow keys for continuous rotation
            # UP=3, DOWN=4, LEFT=5, RIGHT=6
            AIM_ROTATION_SPEED = config.AIM_ROTATION_SPEED
            
            # Handle gun switching (S key = input[9]) - only on key press (rising edge)
            for i in range(8):
                if self.world_data[i, 0] == 0:
                    continue
                # Only switch if S key is pressed now but wasn't pressed last frame
                if self.player_inputs[i, 9] == 1 and self.previous_inputs[i, 9] == 0:
                    self.player_inventories[i].switch_gun()
            
            # Handle reload (R key = input[8])
            for i in range(8):
                if self.world_data[i, 0] == 0:
                    continue
                if self.player_inputs[i, 8] == 1:  # R key pressed
                    weapon = self.player_inventories[i].get_current_gun()
                    # Only start reload if not already reloading and if reload is needed
                    if self.player_reload_cooldown[i] <= 0 and weapon.current_ammo < weapon.magazine_capacity and weapon.total_ammo > 0:
                        self.player_reload_cooldown[i] = weapon.reload_time
            
            for i in range(8):
                if self.world_data[i, 0] == 0:
                    continue
                
                # Continuous rotation based on arrow keys
                if self.player_inputs[i, 5] == 1:  # LEFT arrow
                    self.world_data[i, 3] -= AIM_ROTATION_SPEED
                if self.player_inputs[i, 6] == 1:  # RIGHT arrow
                    self.world_data[i, 3] += AIM_ROTATION_SPEED
                if self.player_inputs[i, 3] == 1:  # UP arrow
                    self.world_data[i, 3] -= AIM_ROTATION_SPEED
                if self.player_inputs[i, 4] == 1:  # DOWN arrow
                    self.world_data[i, 3] += AIM_ROTATION_SPEED

            # Jetpack system (W key = keyboard_input[0])
            jetpack_active = self.player_inputs[:, 0].astype(bool)
            for i in range(8):
                if self.world_data[i, 0] == 0:  # skip inactive players
                    continue
                if jetpack_active[i] and self.player_fuel[i] > 0:
                    # Apply upward thrust
                    self.player_vy[i] -= self.JETPACK_THRUST
                    # Consume fuel
                    self.player_fuel[i] = max(0, self.player_fuel[i] - self.FUEL_CONSUMPTION)
                else:
                    # Recharge fuel when not using jetpack
                    self.player_fuel[i] = min(self.MAX_FUEL, self.player_fuel[i] + self.FUEL_RECHARGE)
                # Update fuel in world_data
                self.world_data[i, 6] = self.player_fuel[i]

            # Apply gravity and vertical movement with obstacle collision
            for i in range(8):
                if self.world_data[i, 0] == 0:
                    continue
                
                # Apply gravity
                self.player_vy[i] += self.GRAVITY
                old_y = self.world_data[i, 2]
                new_y = old_y + self.player_vy[i]
                
                # Check collision with obstacles below
                if self.player_vy[i] > 0:  # falling down
                    ground_y = self.find_ground_below(self.world_data[i, 1], old_y)
                    if new_y >= ground_y:
                        self.world_data[i, 2] = ground_y
                        self.player_vy[i] = 0
                    else:
                        self.world_data[i, 2] = new_y
                else:  # moving up
                    # Check collision when moving up
                    currently_colliding = self.is_colliding_with_obstacle(self.world_data[i, 1], old_y, self.COLLISION_RADIUS)
                    will_collide = self.is_colliding_with_obstacle(self.world_data[i, 1], new_y, self.COLLISION_RADIUS)
                    
                    if not will_collide or currently_colliding:
                        # Allow upward movement if not colliding or already stuck
                        self.world_data[i, 2] = new_y
                    else:
                        self.player_vy[i] = 0
            
            # clamp horizontal position to screen
            self.world_data[:8, 1] = np.clip(self.world_data[:8, 1], self.TANK_RADIUS, self.SCREEN_W - self.TANK_RADIUS)
            # clamp vertical position to prevent going too far up
            self.world_data[:8, 2] = np.clip(self.world_data[:8, 2], self.TANK_RADIUS, self.SCREEN_H)

            # Store bullet old positions before movement for interpolated collision detection
            bullet_old_positions = np.zeros((40, 2), dtype=np.float64)  # 40 bullets, (x, y)
            for b in range(8, 48):
                if self.world_data[b, 0] == 1:
                    bullet_old_positions[b-8, 0] = self.world_data[b, 1]
                    bullet_old_positions[b-8, 1] = self.world_data[b, 2]

            # Move bullets and check collisions
            for b in range(8, 48):
                if self.world_data[b, 0] == 1:  # if bullet is active
                    # Store old position
                    old_x, old_y = self.world_data[b, 1], self.world_data[b, 2]
                    
                    # Move bullet
                    self.world_data[b, 1] += np.cos(self.world_data[b, 3]) * self.world_data[b, 4]
                    self.world_data[b, 2] += np.sin(self.world_data[b, 3]) * self.world_data[b, 4]
                    
                    # Update distance traveled
                    self.world_data[b, 5] += self.world_data[b, 4]
                    
                    # Check if bullet hit obstacle along its path
                    # Always check, even on first movement, to prevent bullets spawning through walls
                    new_x, new_y = self.world_data[b, 1], self.world_data[b, 2]
                    
                    # Check multiple points along the path - more steps for faster bullets
                    # Calculate dynamic step count based on bullet speed to ensure no gaps
                    bullet_speed = self.world_data[b, 4]
                    min_steps = max(10, int(bullet_speed / 2))  # At least 10 steps, more for faster bullets
                    
                    hit_obstacle = False
                    for i in range(min_steps + 1):
                        t = i / min_steps
                        check_x = old_x + (new_x - old_x) * t
                        check_y = old_y + (new_y - old_y) * t
                        if self.is_colliding_with_obstacle(check_x, check_y, 3):  # Slightly larger radius for better detection
                            hit_obstacle = True
                            break
                    
                    if hit_obstacle:
                        self.world_data[b, 0] = 0  # deactivate bullet

            # Deactivate bullets that traveled too far
            self.world_data[8:, 0] = np.where(self.world_data[8:, 5] > MAX_BULLET_DIST, 0, self.world_data[8:, 0])

            # Update fire cooldowns with delta time
            current_time = time.time()
            delta_time = current_time - self.last_frame_time
            self.last_frame_time = current_time
            self.player_fire_cooldown = np.maximum(0, self.player_fire_cooldown - delta_time)
            
            # Update gun spawner
            self.gun_spawner.update(delta_time)
            
            # Check for gun pickups
            for i in range(8):
                if self.world_data[i, 0] == 1:  # Player is alive
                    player_x = self.world_data[i, 1]
                    player_y = self.world_data[i, 2]
                    picked_weapon_id = self.gun_spawner.check_pickup(player_x, player_y)
                    if picked_weapon_id is not None:
                        self.player_inventories[i].pickup_gun(picked_weapon_id)
            
            # Update reload cooldowns and complete reloads when finished
            for i in range(8):
                if self.player_reload_cooldown[i] > 0:
                    self.player_reload_cooldown[i] -= delta_time
                    if self.player_reload_cooldown[i] <= 0:
                        # Reload is complete
                        self.player_reload_cooldown[i] = 0
                        weapon = self.player_inventories[i].get_current_gun()
                        weapon.reload()

            # create bullets (space = index 7)
            shooting_id = np.where(self.player_inputs[:, 7] == 1)[0]
            for idx in shooting_id:
                weapon = self.player_inventories[idx].get_current_gun()
                
                # Check if currently reloading
                if self.player_reload_cooldown[idx] > 0:
                    continue
                
                # Check fire cooldown and ammo
                if self.player_fire_cooldown[idx] > 0:
                    continue
                
                if not weapon.can_shoot():
                    # Auto reload if out of ammo
                    if weapon.total_ammo > 0:
                        self.player_reload_cooldown[idx] = weapon.reload_time
                    continue
                
                # Shoot weapon
                weapon.shoot()
                    
                id = idx * 5 + 8
                
                # Spawn bullets based on rpf (rounds per fire)
                bullets_spawned = 0
                for i in range(weapon.rpf):
                    free_slots = np.where(self.world_data[id:id+5, 0] == 0)[0]
                    if len(free_slots) > 0:
                        bullet_index = free_slots[0]
                        
                        # Calculate bullet angle with spread
                        bullet_angle = weapon.get_bullet_angle_with_spread(self.world_data[idx, 3])
                        
                        # Get proper barrel distance for this weapon
                        barrel_dist = self._get_barrel_distance(weapon.gun_id)
                        offset_x, offset_y = self._get_bullet_spawn_offset(weapon.gun_id)
                        
                        # Calculate spawn position at gun barrel with offset
                        spawn_x = self.world_data[idx, 1] + barrel_dist * np.cos(bullet_angle)
                        spawn_y = self.world_data[idx, 2] + barrel_dist * np.sin(bullet_angle)
                        
                        # Apply perpendicular offset if needed
                        if offset_x != 0 or offset_y != 0:
                            perp_angle = bullet_angle + np.pi / 2
                            spawn_x += offset_x * np.cos(bullet_angle) + offset_y * np.cos(perp_angle)
                            spawn_y += offset_x * np.sin(bullet_angle) + offset_y * np.sin(perp_angle)
                        
                        self.world_data[id+bullet_index, 0] = 1
                        self.world_data[id+bullet_index, 1] = spawn_x
                        self.world_data[id+bullet_index, 2] = spawn_y
                        self.world_data[id+bullet_index, 3] = bullet_angle
                        # Set bullet speed from weapon
                        self.world_data[id+bullet_index, 4] = weapon.bullet_speed
                        # reset traveled distance
                        self.world_data[id+bullet_index, 5] = 0
                        # set bullet damage from weapon
                        self.world_data[id+bullet_index, 7] = weapon.damage
                        # set bullet owner for scoring
                        self.world_data[id+bullet_index, 9] = idx
                        bullets_spawned += 1
                
                if bullets_spawned > 0:
                    # Set cooldown based on weapon's rate of fire
                    self.player_fire_cooldown[idx] = weapon.rate_of_fire
                    # Immediately sync ammo to world_data after shooting
                    self.world_data[idx, 9] = weapon.current_ammo
                    self.world_data[idx, 10] = weapon.total_ammo
                    
                    # Update bullet_old_positions for newly spawned bullets to prevent false collision checks
                    for i in range(weapon.rpf):
                        bullet_slot = id + i
                        if bullet_slot < 48 and self.world_data[bullet_slot, 0] == 1:
                            # Set old position to current position (spawn position) so first frame doesn't check from (0,0)
                            bullet_old_positions[bullet_slot-8, 0] = self.world_data[bullet_slot, 1]
                            bullet_old_positions[bullet_slot-8, 1] = self.world_data[bullet_slot, 2]

            # detect collisions
            # BULLET -> TANK collisions: apply damage, credit score, respawn on death
            # Use interpolated path checking to prevent bullets from skipping over players
            for b in range(8, 48):
                if self.world_data[b, 0] == 0:
                    continue
                
                # Get bullet old and new positions
                old_bx, old_by = bullet_old_positions[b-8, 0], bullet_old_positions[b-8, 1]
                new_bx, new_by = self.world_data[b, 1], self.world_data[b, 2]
                damage = self.world_data[b, 7]
                owner = int(self.world_data[b, 9])
                
                bullet_hit = False
                # Check collision along the bullet's path with multiple interpolation steps
                # Increase steps for more accurate detection with fast bullets
                bullet_speed = self.world_data[b, 4]
                steps = max(15, int(bullet_speed / 1.5))  # Dynamic steps based on speed
                for step in range(steps + 1):
                    if bullet_hit:
                        break
                    
                    # Interpolate position along bullet path
                    t = step / steps
                    bx = old_bx + (new_bx - old_bx) * t
                    by = old_by + (new_by - old_by) * t
                    
                    # Check against all players
                    for tank in range(8):
                        if self.world_data[tank, 0] == 0:
                            continue
                        if tank == owner:
                            continue
                        
                        tx, ty = self.world_data[tank, 1], self.world_data[tank, 2]
                        dist = np.sqrt((tx - bx)**2 + (ty - by)**2)
                        
                        if dist < config.BULLET_HIT_RADIUS:
                            # hit - apply damage
                            self.world_data[tank, 7] -= damage
                            bullet_hit = True
                            
                            # check death
                            if self.world_data[tank, 7] <= 0:
                                # credit score to owner if owner is valid
                                if 0 <= owner < 8:
                                    self.world_data[owner, 8] += 1
                                self.respawn(tank)
                            break
                
                # remove bullet after processing all potential hits
                if bullet_hit:
                    self.world_data[b, 0] = 0
            
            # Sync all player ammo to world_data at end of frame (after all shooting/reloading)
            for i in range(8):
                if self.world_data[i, 0] == 1:
                    current_gun = self.player_inventories[i].get_current_gun()
                    self.world_data[i, 9] = current_gun.current_ammo
                    self.world_data[i, 10] = current_gun.total_ammo
            
            # Store current inputs for next frame's edge detection
            self.previous_inputs = self.player_inputs.copy()

    def respawn(self, tank_index):
        # spawn at a random x and find ground below
        spawn_x = np.random.randint(self.TANK_RADIUS, self.SCREEN_W - self.TANK_RADIUS)
        # Start from top and find first valid ground
        ground_y = self.find_ground_below(spawn_x, 0)
        self.world_data[tank_index, 1] = spawn_x
        self.world_data[tank_index, 2] = ground_y
        # reset vertical velocity
        if hasattr(self, 'player_vy'):
            self.player_vy[tank_index] = 0
        # reset fuel to full
        if hasattr(self, 'player_fuel'):
            self.player_fuel[tank_index] = self.MAX_FUEL
            self.world_data[tank_index, 6] = self.MAX_FUEL
        # reset health on respawn
        if hasattr(self, 'MAX_HEALTH'):
            self.world_data[tank_index, 7] = self.MAX_HEALTH

    def add_players(self):
        while True:
            conn, address = self.server_socket.accept()

            with self.player_lock:
                available_ids = np.where(self.world_data[:8, 0] == 0)[0]
                if len(available_ids) == 0:
                    print("server full")
                    continue

                player_id = available_ids[0]
                self.world_data[player_id, 0] = -1  # temporarily reserve slot

            thread = threading.Thread(
                target=self.player_handler,
                args=(conn, player_id),
                daemon=True
            )
            thread.start()
            self.player_count += 1
            

    def player_handler(self, conn, player_id):
        data = conn.recv(16)
        name = data.decode("utf-8")
        print("[LOG]", name, "connected to the server.")

        conn.send(int(player_id).to_bytes(4, byteorder='little'))
        
        # Send collision map dimensions and data
        map_info = np.array([self.GRID_W, self.GRID_H, self.GRID_SIZE], dtype=np.int32)
        conn.send(map_info.tobytes())
        conn.send(self.collision_map_bytes)
        
        self.world_data[player_id, 0] = 1
        self.respawn(player_id)

        while True:
            data = conn.recv(16)  # allow for up to 16 bytes (12 bools = 12 bytes, but allow extra)
            if not data:
                self.world_data[player_id, 0] = 0
                if hasattr(self, 'player_vy'):
                    self.player_vy[player_id] = 0
                break

            player_input = np.frombuffer(data, dtype=bool)
            # Robustly pad or truncate to 12 inputs
            if len(player_input) < 12:
                padded_input = np.zeros(12, dtype=bool)
                padded_input[:len(player_input)] = player_input
                player_input = padded_input
            elif len(player_input) > 12:
                player_input = player_input[:12]
            self.player_inputs[player_id] = player_input.astype(int)

            # Prepare extended game state
            world_data, spawn_data, inventory_data, gas_data, grenade_data = self.get_extended_game_state()

            # Send all data with explicit length header for robust client parsing
            world_bytes = world_data.tobytes()
            spawn_bytes = spawn_data.tobytes()
            gas_bytes = gas_data.tobytes()
            grenade_bytes = grenade_data.tobytes()
            inventory_bytes = inventory_data.tobytes()
            header_bytes = np.array([len(spawn_bytes), len(gas_bytes), len(grenade_bytes)], dtype=np.int32).tobytes()

            # Packet layout:
            # [world_data float64 fixed size]
            # [header int32*3 -> spawn_len, gas_len, grenade_len]
            # [spawn_data bytes]
            # [gas_data bytes]
            # [grenade_data bytes]
            # [inventory_data int32 fixed size]
            conn.sendall(world_bytes + header_bytes + spawn_bytes + gas_bytes + grenade_bytes + inventory_bytes)


            

a = Server()
print("program concluded")
