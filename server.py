import socket
import threading
import time
import numpy as np
import pygame
import os

class Server:
    def __init__(self):
        PORT = 5555
        if not self._start_server(PORT):
            return

        self.setup_game()

        thread = threading.Thread(target=self.add_players, daemon=True)
        thread.start()

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
        self.player_count = 0
        self.load_map("wncc2")
        # world_data columns (per row):
        # 0:is_alive, 1:x, 2:y, 3:theta, 4:v, 5:omega_or_traveled, 6:fuel, 7:health_or_damage, 8:score, 9:owner_id
        # for tanks: column 6 = fuel, 7 = health, 8 = score
        # for bullets: column 5 = distance traveled, 7 = damage, 9 = owner id
        self.world_data = np.zeros((48, 10), dtype=np.float64)
        self.player_inputs = np.zeros((8, 8), dtype=np.int32)  # 8 inputs now

        TANK_V = 3.0
        TANK_OMEGA = 0.04
        BULLET_V = 10.0

        self.world_data[:8, 4] = TANK_V
        self.world_data[:8, 5] = TANK_OMEGA
        self.world_data[8:, 4] = BULLET_V
        # per-player vertical velocity for gravity (tanks only)
        self.player_vy = np.zeros(8, dtype=np.float64)
        # screen and tank constants for ground handling
        self.SCREEN_W = 800
        self.SCREEN_H = 600
        self.TANK_RADIUS = 7.5  # visual radius
        self.COLLISION_RADIUS = 6  # smaller collision radius to prevent getting stuck
        self.GROUND_Y = self.SCREEN_H - self.COLLISION_RADIUS
        self.GRAVITY = 0.8
        
        # Jetpack system
        self.player_fuel = np.full(8, 100.0, dtype=np.float64)  # start with full fuel
        self.MAX_FUEL = 100.0
        self.FUEL_CONSUMPTION = 0.5  # fuel consumed per frame when jetpack active
        self.FUEL_RECHARGE = 0.5     # fuel recharged per frame when not in use
        self.JETPACK_THRUST = 0.9    # upward velocity applied by jetpack (reduced for better control)
        
        # Use column 6 (info) to store fuel for tanks
        self.world_data[:8, 6] = self.player_fuel

        # Health and score per tank
        self.MAX_HEALTH = 200.0
        self.world_data[:8, 7] = self.MAX_HEALTH  # health
        self.world_data[:8, 8] = 0.0  # score

        # per-player gun damage (can be changed later when switching weapons)
        # damage is absolute hit points (default 10 = 10% of 100)
        self.player_gun_damage = np.full(8, 10.0, dtype=np.float64)
        
        # Fire rate cooldown (frames between shots)
        self.FIRE_COOLDOWN = 10  # 10 frames = ~167ms at 60fps
        self.player_fire_cooldown = np.zeros(8, dtype=np.int32)
        
        # Collision map system - grid-based obstacles
        self.GRID_SIZE = 20  # each cell is 20x20 pixels
        self.GRID_W = self.SCREEN_W // self.GRID_SIZE  # 40 cells wide
        self.GRID_H = self.SCREEN_H // self.GRID_SIZE  # 30 cells tall
        
        # Load map from file or create default
        
        
        # Convert map to bytes for transmission
        self.collision_map_bytes = self.collision_map.tobytes()
    
    def load_map(self, map_name):
        """Load map from maps/ folder or create default if not found"""
        map_path = os.path.join("maps", f"{map_name}.npy")
        
        if os.path.exists(map_path):
            try:
                self.collision_map = np.load(map_path)
                print(f"[SERVER] Loaded map: {map_name}")
                return True
            except Exception as e:
                print(f"[SERVER] Error loading map {map_name}: {e}")
        
        # Create default map if file not found
        print(f"[SERVER] Map '{map_name}' not found, creating default map")
        self.collision_map = np.ones((self.GRID_H, self.GRID_W), dtype=np.int32)
        
        # Simple default layout
        self.collision_map[-1, :] = 0  # Ground floor
        self.collision_map[20, 5:15] = 0  # Left platform
        self.collision_map[15, 25:35] = 0  # Right platform
        self.collision_map[10, 10:20] = 0  # Top platform
        
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

    def run_game(self):
        MAX_BULLET_DIST = 1200

        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
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
            AIM_ROTATION_SPEED = 0.08  # radians per frame
            
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
                    
                    # Check if bullet hit obstacle (only if it has moved from spawn)
                    if self.world_data[b, 5] > self.world_data[b, 4]:  # traveled more than one step
                        new_x, new_y = self.world_data[b, 1], self.world_data[b, 2]
                        
                        # Check multiple points along the path
                        steps = 5
                        hit = False
                        for i in range(steps + 1):
                            t = i / steps
                            check_x = old_x + (new_x - old_x) * t
                            check_y = old_y + (new_y - old_y) * t
                            if self.is_colliding_with_obstacle(check_x, check_y, 2):
                                hit = True
                                break
                        
                        if hit:
                            self.world_data[b, 0] = 0  # deactivate bullet

            # Deactivate bullets that traveled too far
            self.world_data[8:, 0] = np.where(self.world_data[8:, 5] > MAX_BULLET_DIST, 0, self.world_data[8:, 0])

            # create bullets (space = index 7)
            shooting_id = np.where(self.player_inputs[:, 7] == 1)[0]
            for idx in shooting_id:
                # Check fire cooldown
                if self.player_fire_cooldown[idx] > 0:
                    continue
                    
                id = idx * 5 + 8
                free_slots = np.where(self.world_data[id:id+5, 0] == 0)[0]
                if len(free_slots) > 0:
                    bullet_index = free_slots[0]
                    self.world_data[id+bullet_index, 0] = 1
                    self.world_data[id+bullet_index, 1] = self.world_data[idx, 1] + np.cos(self.world_data[idx, 3]) * 15
                    self.world_data[id+bullet_index, 2] = self.world_data[idx, 2] + np.sin(self.world_data[idx, 3]) * 15
                    self.world_data[id+bullet_index, 3] = self.world_data[idx, 3]
                    # reset traveled distance
                    self.world_data[id+bullet_index, 5] = 0
                    # set bullet damage from player's current gun
                    self.world_data[id+bullet_index, 7] = self.player_gun_damage[idx]
                    # set bullet owner for scoring
                    self.world_data[id+bullet_index, 9] = idx
                    # Set cooldown
                    self.player_fire_cooldown[idx] = self.FIRE_COOLDOWN
            
            # Decrease all cooldowns
            self.player_fire_cooldown = np.maximum(0, self.player_fire_cooldown - 1)

            # detect collisions
            # BULLET -> TANK collisions: apply damage, credit score, respawn on death
            for b in range(8, 48):
                if self.world_data[b, 0] == 0:
                    continue
                # bullet position
                bx, by = self.world_data[b, 1], self.world_data[b, 2]
                damage = self.world_data[b, 7]
                owner = int(self.world_data[b, 9])
                
                bullet_hit = False
                for t in range(8):
                    if self.world_data[t, 0] == 0:
                        continue
                    if t == owner:
                        continue
                    tx, ty = self.world_data[t, 1], self.world_data[t, 2]
                    dist = np.sqrt((tx - bx)**2 + (ty - by)**2)
                    if dist < 25:
                        # hit - apply damage
                        self.world_data[t, 7] -= damage
                        bullet_hit = True
                        
                        # check death
                        if self.world_data[t, 7] <= 0:
                            # credit score to owner if owner is valid
                            if 0 <= owner < 8:
                                self.world_data[owner, 8] += 1
                            self.respawn(t)
                        break
                
                # remove bullet after processing all potential hits
                if bullet_hit:
                    self.world_data[b, 0] = 0

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

            available_ids = np.where(self.world_data[:8, 0] == 0)[0]
            if len(available_ids) == 0:
                print("server full")
                continue

            thread = threading.Thread(target=self.player_handler, args=(conn, available_ids[0]), daemon=True)
            thread.start()
            self.player_count += 1
            

    def player_handler(self, conn, player_id):
        data = conn.recv(16)
        name = data.decode("utf-8")
        print("[LOG]", name, "connected to the server.")

        conn.send(str.encode(str(player_id)))
        
        # Send collision map dimensions and data
        map_info = np.array([self.GRID_W, self.GRID_H, self.GRID_SIZE], dtype=np.int32)
        conn.send(map_info.tobytes())
        conn.send(self.collision_map_bytes)
        
        self.world_data[player_id, 0] = 1
        self.respawn(player_id)

        while True:
            data = conn.recv(8)  # now receiving 8 inputs
            if not data:
                self.world_data[player_id, 0] = 0
                if hasattr(self, 'player_vy'):
                    self.player_vy[player_id] = 0
                break

            player_input = np.frombuffer(data, dtype=bool)
            self.player_inputs[player_id] = player_input.astype(int)
            conn.send(self.world_data.tobytes())


            

a = Server()
print("program concluded")
