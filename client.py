import socket
import numpy as np
import config

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # default to localhost for local testing
        self.host = config.SERVER_HOST
        self.port = config.SERVER_PORT
        self.addr = (self.host, self.port)

    def connect(self, name):
        self.client.connect(self.addr)

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
            # expect 55 rows * 11 columns * 8 bytes per float64 = 4840 bytes (world_data)
            # + 12 bytes header (3 int32s)
            # + spawn_data (variable)
            # + gas_data (variable)
            # + grenade_data (8 * 4 * 8 = 256 bytes)
            # + inventory_data (8 * 3 * 4 = 96 bytes)
            # Total minimum: 4840 + 12 + 256 + 96 = 5204 bytes
            while len(reply) < 5204:
                chunk = self.client.recv(4096)
                if not chunk:
                    break
                reply += chunk
                if len(reply) >= 4840:  # At minimum we have world_data
                    break
                    
            # Parse world_data (first 4840 bytes - 55 entities including grenades)
            game_world = np.frombuffer(reply[:4840], dtype=np.float64).reshape((55, 11))
            
            # Parse header to get variable data sizes
            header = np.frombuffer(reply[4840:4852], dtype=np.int32)
            spawn_len, gas_len, grenade_len = header
            
            # Parse spawn, gas, and grenade data
            offset = 4852
            spawn_bytes = reply[offset:offset+spawn_len]
            offset += spawn_len
            gas_bytes = reply[offset:offset+gas_len]
            offset += gas_len
            grenade_bytes = reply[offset:offset+grenade_len]
            offset += grenade_len
            inventory_bytes = reply[offset:offset+96]
            
            # Decode spawn data
            gun_spawns = []
            if spawn_len >= 16:
                num_spawns = spawn_len // 16
                spawn_array = np.frombuffer(spawn_bytes[:num_spawns*16], dtype=np.float32).reshape((-1, 4))
                gun_spawns = spawn_array.tolist()
            
            # Decode inventory data
            inventory_data = np.frombuffer(inventory_bytes, dtype=np.int32).reshape((8, 3))
            
            # Decode gas data
            gas_data = np.zeros((0, 4), dtype=np.float64)
            if gas_len > 0:
                gas_data = np.frombuffer(gas_bytes, dtype=np.float64).reshape((-1, 4))
            
            # Decode grenade data
            grenade_data = np.frombuffer(grenade_bytes, dtype=np.float64).reshape((8, 4))
            
            return game_world, gun_spawns, inventory_data, gas_data, grenade_data
        except socket.error as e:
            print(e)
            return None, [], None, None, None

