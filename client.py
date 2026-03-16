import socket
import numpy as np
import config

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.timeout = 5.0
        self.client.settimeout(self.timeout)
        # default to localhost for local testing
        self.host = config.SERVER_HOST
        self.port = config.SERVER_PORT
        self.addr = (self.host, self.port)

    def connect(self, name):
        try:
            self.client.connect(self.addr)
        except (socket.timeout, OSError) as e:
            if self.host not in ("127.0.0.1", "localhost"):
                # Retry once against localhost for local dev setups.
                self.client.close()
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.settimeout(self.timeout)
                fallback_addr = ("127.0.0.1", self.port)
                try:
                    self.client.connect(fallback_addr)
                    self.host, self.addr = fallback_addr[0], fallback_addr
                    print(f"[CLIENT] Falling back to {self.host}:{self.port} after connect failure: {e}")
                except (socket.timeout, OSError):
                    raise
            else:
                raise

        # inform server of username - pad to exactly 16 bytes
        name_bytes = name.encode('utf-8')[:16]  # Truncate if too long
        name_bytes = name_bytes.ljust(16, b'\x00')  # Pad with null bytes to 16 bytes
        self.client.send(name_bytes)

        # receive user ID from server
        data = self.client.recv(4)
        player_id = int.from_bytes(data, byteorder='little')
        
        # receive collision map info
        map_info_bytes = self.client.recv(12)  # 3 int32s
        map_info = np.frombuffer(map_info_bytes, dtype=np.int32)
        self.grid_w, self.grid_h, self.grid_size = map_info
        
        # receive collision map data
        map_size = self.grid_w * self.grid_h * 4  # int32 = 4 bytes
        map_bytes = bytes()
        while len(map_bytes) < map_size:
            map_bytes += self.client.recv(4096)
        self.collision_map = np.frombuffer(map_bytes[:map_size], dtype=np.int32).reshape((self.grid_h, self.grid_w))
        print("Got player ID:", player_id)
        print("Map info:", self.grid_w, self.grid_h, self.grid_size)
        print("Map bytes received:", len(map_bytes))
        return player_id 

    def disconnect(self):
        self.client.close()
    
    def get_collision_map(self):
        """Return the collision map and grid info"""
        return self.collision_map, self.grid_w, self.grid_h, self.grid_size

    def send(self, keyboard_input):
        try:
            client_msg = keyboard_input.tobytes()
            self.client.send(client_msg)
            reply = bytes()
            
            # First, receive the fixed 4864 bytes (world_data + header)
            while len(reply) < 4864:
                chunk = self.client.recv(4096)
                if not chunk:
                    break
                reply += chunk
            
            # Now we can read the header to know variable sizes
            if len(reply) < 4864:
                print(f"Error: Not enough data for header. Got {len(reply)} bytes, need 4864")
                return None
            
            # Parse world_data (first 4840 bytes)
            game_world = np.frombuffer(reply[:4840], dtype=np.float64).reshape((55, 11))
            
            # Parse header to get variable data sizes
            header = np.frombuffer(reply[4840:4864], dtype=np.int32)
            spawn_len, medkit_len, gas_len, grenade_len, leaderboard_len, timer_len = header
            
            # Calculate total variable data needed
            var_data_size = spawn_len + medkit_len + gas_len + grenade_len + 96 + 128 + leaderboard_len + timer_len
            total_needed = 4864 + var_data_size
            
            # Receive remaining variable data
            while len(reply) < total_needed:
                chunk = self.client.recv(4096)
                if not chunk:
                    print(f"Warning: Socket closed. Got {len(reply)}/{total_needed} bytes")
                    break
                reply += chunk
            
            # Parse spawn, medkit, gas, and grenade data
            offset = 4864
            spawn_bytes = reply[offset:offset+spawn_len]
            offset += spawn_len
            medkit_bytes = reply[offset:offset+medkit_len]
            offset += medkit_len
            gas_bytes = reply[offset:offset+gas_len]
            offset += gas_len
            grenade_bytes = reply[offset:offset+grenade_len]
            offset += grenade_len
            inventory_bytes = reply[offset:offset+96]
            offset += 96

            # Decode player names
            names_bytes = reply[offset:offset+128]
            offset += 128

            names_str = names_bytes.decode().strip("\x00")
            player_names = names_str.split("|")
            
            # Decode spawn data
            gun_spawns = []
            if spawn_len > 0 and len(spawn_bytes) >= spawn_len:
                num_spawns = spawn_len // 16
                if num_spawns > 0:
                    spawn_array = np.frombuffer(spawn_bytes[:num_spawns*16], dtype=np.float32).reshape((-1, 4))
                    gun_spawns = spawn_array.tolist()
            
            # Decode medkit data
            medkit_spawns = []
            if medkit_len > 0 and len(medkit_bytes) >= medkit_len:
                num_medkits = medkit_len // 12
                if num_medkits > 0:
                    medkit_array = np.frombuffer(medkit_bytes[:num_medkits*12], dtype=np.float32).reshape((-1, 3))
                    medkit_spawns = medkit_array.tolist()
            
            # Decode inventory data
            inventory_data = np.zeros((8, 3), dtype=np.int32)
            if len(inventory_bytes) >= 96:
                inventory_data = np.frombuffer(inventory_bytes[:96], dtype=np.int32).reshape((8, 3))
            
            # Decode gas data
            gas_data = np.zeros((0, 4), dtype=np.float64)
            if gas_len > 0 and len(gas_bytes) >= gas_len:
                gas_data = np.frombuffer(gas_bytes[:gas_len], dtype=np.float64).reshape((-1, 4))
            
            # Decode grenade data
            grenade_data = np.zeros((8, 4), dtype=np.float64)
            if len(grenade_bytes) >= 256:
                grenade_data = np.frombuffer(grenade_bytes[:256], dtype=np.float64).reshape((8, 4))

            # Decode leaderboard data: [player_idx, kills, deaths, kills_minus_deaths]
            leaderboard_bytes = reply[offset:offset+leaderboard_len]
            offset += leaderboard_len  # always increment even if 0

            if leaderboard_len >= 16:
                row_count = leaderboard_len // 16
                leaderboard_data = np.frombuffer(leaderboard_bytes[:row_count*16], dtype=np.int32).reshape((-1, 4))
            else:
                leaderboard_data = np.zeros((0, 4), dtype=np.int32)
            
            timer_bytes = reply[offset:offset+timer_len]
            if len(timer_bytes) == 8:
                time_remaining = np.frombuffer(timer_bytes, dtype=np.float64)[0]
            else:
                time_remaining = 0.0
            return game_world, gun_spawns, medkit_spawns, inventory_data, gas_data, grenade_data, player_names, leaderboard_data, time_remaining
        except socket.error as e:
            print(e)
            return None

