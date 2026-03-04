import pygame
import math
import os

class WeaponRenderer:
    """Handles visual representation of weapons"""
    
    def __init__(self):
        self.gun_sprites = {}  # Cache for loaded gun sprites
        self.gun_directory = os.path.join("assets", "guns")
        
        # Create directory if it doesn't exist
        if not os.path.exists(self.gun_directory):
            os.makedirs(self.gun_directory)
            print(f"[WeaponRenderer] Created directory: {self.gun_directory}")
            print(f"[WeaponRenderer] Please add gun PNG files to: {self.gun_directory}")
        
        # Map weapon IDs to their bullet/ammo sprites
        self.weapon_bullet_sprites = {
            11: "saw_ammo.png",           # SAW uses saw_ammo
            15: "rocket_launcher_ammo.png", # Rocket Launcher uses rocket_launcher_ammo
            # All other weapons use default bullet.png
        }
    
    def get_bullet_sprite(self, weapon_id):
        """Get the appropriate bullet sprite for a weapon"""
        sprite_file = self.weapon_bullet_sprites.get(weapon_id, "bullet.png")
        return self.load_gun_sprite(sprite_file)
    
    def load_gun_sprite(self, sprite_file):
        """Load and cache a gun sprite"""
        if sprite_file in self.gun_sprites:
            return self.gun_sprites[sprite_file]
        
        sprite_path = os.path.join(self.gun_directory, sprite_file)
        
        if os.path.exists(sprite_path):
            try:
                sprite = pygame.image.load(sprite_path).convert_alpha()
                self.gun_sprites[sprite_file] = sprite
                return sprite
            except Exception as e:
                print(f"[WeaponRenderer] Error loading {sprite_file}: {e}")
                return None
        else:
            # Return None if sprite doesn't exist (will draw fallback)
            return None
    
    def draw_gun(self, screen, x, y, angle, gun, tank_radius=7.5):
        """
        Draw a gun sprite at the given position and angle
        
        Args:
            screen: pygame surface
            x, y: tank center position
            angle: aim angle in radians
            gun: Gun object
            tank_radius: radius of tank
        """
        if gun is None:
            return
        
        # Try to load the sprite
        sprite = self.load_gun_sprite(gun.sprite_file)
        
        if sprite:
            # Scale down the sprite to be proportional to tank size
            # Target gun length should be about 20-25 pixels
            target_length = 25
            scale_factor = target_length / max(sprite.get_width(), sprite.get_height())
            scaled_width = int(sprite.get_width() * scale_factor)
            scaled_height = int(sprite.get_height() * scale_factor)
            
            # Scale the sprite
            scaled_sprite = pygame.transform.scale(sprite, (scaled_width, scaled_height))
            
            # Normalize angle to 0-2π range
            angle_normalized = angle % (2 * math.pi)
            angle_degrees = math.degrees(angle_normalized)
            
            # Flip sprite vertically if pointing backwards (90° to 270°)
            if math.pi / 2 < angle_normalized < 3 * math.pi / 2:
                scaled_sprite = pygame.transform.flip(scaled_sprite, False, True)
            
            # Rotate sprite to match angle
            rotated_sprite = pygame.transform.rotate(scaled_sprite, -angle_degrees)
            
            # Calculate position (gun extends from tank)
            offset_distance = tank_radius + scaled_width / 2
            gun_x = x + math.cos(angle) * offset_distance - rotated_sprite.get_width() / 2
            gun_y = y + math.sin(angle) * offset_distance - rotated_sprite.get_height() / 2
            
            screen.blit(rotated_sprite, (gun_x, gun_y))
        else:
            # Fallback: draw simple line if sprite not found
            gun_length = 15
            gun_start_x = x + math.cos(angle) * tank_radius
            gun_start_y = y + math.sin(angle) * tank_radius
            gun_end_x = gun_start_x + math.cos(angle) * gun_length
            gun_end_y = gun_start_y + math.sin(angle) * gun_length
            
            # Use white for fallback
            pygame.draw.line(screen, (255, 255, 255), 
                           (gun_start_x, gun_start_y), 
                           (gun_end_x, gun_end_y), 3)
            pygame.draw.circle(screen, (200, 200, 0), 
                             (int(gun_end_x), int(gun_end_y)), 2)
    
    @staticmethod
    def draw_ammo_counter(screen, gun, x, y, font):
        """
        Draw ammo counter for a gun
        
        Args:
            screen: pygame surface
            gun: Gun object
            x, y: position to draw counter
            font: pygame font object
        """
        if gun is None:
            return
        
        ammo_text = f"{gun.current_ammo}/{gun.total_ammo}"
        color = (255, 255, 255)
        
        # Red if low ammo
        if gun.current_ammo == 0:
            color = (255, 0, 0)
        elif gun.current_ammo < gun.magazine_capacity * 0.3:
            color = (255, 255, 0)
        
        text_surface = font.render(ammo_text, True, color)
        screen.blit(text_surface, (x, y))
    
    def draw_weapon_icon(self, screen, gun, x, y, size=20):
        """
        Draw a small weapon icon (for HUD or inventory)
        
        Args:
            screen: pygame surface
            gun: Gun object
            x, y: center position
            size: icon size
        """
        if gun is None:
            return
        
        # Try to load and draw mini sprite
        sprite = self.load_gun_sprite(gun.sprite_file)
        if sprite:
            scaled_sprite = pygame.transform.scale(sprite, (size, int(size * 0.6)))
            screen.blit(scaled_sprite, (x - size/2, y - size/3))
        else:
            # Fallback: draw colored rectangle
            rect = pygame.Rect(x - size/2, y - size/4, size, size/2)
            pygame.draw.rect(screen, (150, 150, 150), rect)
    
    def draw_grenade(self, screen, x, y, grenade_type, sprite_file, is_armed):
        """
        Draw a grenade sprite at the given position
        
        Args:
            screen: pygame surface
            x, y: grenade position
            grenade_type: grenade type ID (1=frag, 2=proxy, 3=gas)
            sprite_file: grenade sprite filename
            is_armed: whether proximity grenade is armed
        """
        grenade_directory = os.path.join("assets", "grenades")
        
        if sprite_file:
            sprite_path = os.path.join(grenade_directory, sprite_file)
            
            if os.path.exists(sprite_path):
                try:
                    sprite = pygame.image.load(sprite_path).convert_alpha()
                    # Scale grenade sprite to reasonable size (10x10 pixels)
                    scaled_sprite = pygame.transform.scale(sprite, (10, 10))
                    screen.blit(scaled_sprite, (x - 5, y - 5))
                    
                    # Draw indicator for armed proximity grenades
                    if is_armed and grenade_type == 2:
                        pygame.draw.circle(screen, (255, 0, 0), (int(x), int(y)), 12, 1)
                    return
                except Exception as e:
                    pass
        
        # Fallback: draw colored circle
        color_map = {
            1: (200, 50, 50),   # Frag - red
            2: (50, 200, 50),   # Proximity - green
            3: (200, 200, 50)   # Gas - yellow
        }
        color = color_map.get(grenade_type, (150, 150, 150))
        pygame.draw.circle(screen, color, (int(x), int(y)), 5)
    
    def draw_grenade_counter(self, screen, grenade_data, player_id, x, y, font):
        """
        Draw grenade inventory counter
        
        Args:
            screen: pygame surface
            grenade_data: numpy array with grenade counts
            player_id: player ID (row index in grenade_data)
            x, y: position to draw counter
            font: pygame font object
        """
        if grenade_data is None or len(grenade_data) == 0:
            return
        
        if player_id >= len(grenade_data):
            return
        
        # Get player's grenade data
        selected_type = int(grenade_data[player_id, 0])  # Column 0: selected grenade type
        frag_count = int(grenade_data[player_id, 1])     # Column 1: frag count
        proxy_count = int(grenade_data[player_id, 2])    # Column 2: proxy count
        gas_count = int(grenade_data[player_id, 3])      # Column 3: gas count
        
        grenade_names = {
            1: "Frag",
            2: "Proximity",
            3: "Gas"
        }
        
        grenade_counts = {
            1: frag_count,
            2: proxy_count,
            3: gas_count
        }
        
        # Draw selected grenade type and count
        selected_name = grenade_names.get(selected_type, "Grenade")
        selected_count = grenade_counts.get(selected_type, 0)
        
        grenade_text = f"{selected_name}: {selected_count}"
        
        # Color based on count
        color = (255, 255, 255)  # White
        if selected_count == 0:
            color = (255, 0, 0)  # Red if empty
        elif selected_count <= 1:
            color = (255, 255, 0)  # Yellow if low
        
        text_surface = font.render(grenade_text, True, color)
        screen.blit(text_surface, (x, y))
    