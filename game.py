import pygame
import numpy as np
from client import Network
import time

class PlayerClient:
    def __init__(self, W=800, H=600):
        # Initial screen size, will be resized after connecting to server
        self.screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
        pygame.display.set_caption("PyTanks")
        self.font = pygame.font.SysFont(None, 24)

        self.get_player_name()
        self.join_server()
        # Resize screen based on map dimensions
        map_width = self.grid_w * self.grid_size
        map_height = self.grid_h * self.grid_size
        self.screen = pygame.display.set_mode((map_width, map_height), pygame.RESIZABLE)
        self.run_game()
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

    def run_game(self):
        clock = pygame.time.Clock()
        while self.running:
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # [W=jetpack, A=left, D=right, UP=aim up, DOWN=aim down, LEFT=aim left, RIGHT=aim right, SPACE=shoot]
            keyboard_input = np.zeros(8, dtype=bool)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:  # W for jetpack
                keyboard_input[0] = 1
            if keys[pygame.K_a]:  # A to move left
                keyboard_input[1] = 1
            if keys[pygame.K_d]:  # D to move right
                keyboard_input[2] = 1
            if keys[pygame.K_UP]:  # Up arrow for aim up
                keyboard_input[3] = 1
            if keys[pygame.K_DOWN]:  # Down arrow for aim down
                keyboard_input[4] = 1
            if keys[pygame.K_LEFT]:  # Left arrow for aim left
                keyboard_input[5] = 1
            if keys[pygame.K_RIGHT]:  # Right arrow for aim right
                keyboard_input[6] = 1
            if keys[pygame.K_SPACE]:  # Space to shoot
                keyboard_input[7] = 1
            if keys[pygame.K_ESCAPE]:
                self.running = False

            game_world = self.server.send(keyboard_input)
            self.render(game_world)

    def render(self, game_world):
        self.screen.fill((0,0,0))
        
        # Draw collision map obstacles (brown/gray blocks)
        for gy in range(self.grid_h):
            for gx in range(self.grid_w):
                if self.collision_map[gy, gx] == 0:  # obstacle
                    x = gx * self.grid_size
                    y = gy * self.grid_size
                    pygame.draw.rect(self.screen, (100, 100, 100), (x, y, self.grid_size, self.grid_size))
                    # Add border for visibility
                    pygame.draw.rect(self.screen, (70, 70, 70), (x, y, self.grid_size, self.grid_size), 1)
        
        for i in range(8):
            if game_world[i, 0] == 0:
                continue

            color = (255, 0, 0)
            if i == self.ID:
                    color = (0, 0, 255)
            # Draw player circle
            pygame.draw.circle(self.screen, color, (int(game_world[i, 1]), int(game_world[i, 2])), 12.5)
            # Draw aim direction line
            pygame.draw.line(self.screen, (0, 255, 0), ((int(game_world[i, 1]), int(game_world[i, 2]))), ((int(game_world[i, 1] + 12.5*np.cos(game_world[i, 3])), int(game_world[i, 2] + 12.5*np.sin(game_world[i, 3])))), 2)
            
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
            bar_width, bar_height = 200, 20
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
            hbar_x, hbar_y = 10, 40
            hbar_w, hbar_h = 200, 20
            pygame.draw.rect(self.screen, (50, 50, 50), (hbar_x, hbar_y, hbar_w, hbar_h))
            pygame.draw.rect(self.screen, (255, 0, 0), (hbar_x, hbar_y, int(hbar_w * health_percent), hbar_h))
            pygame.draw.rect(self.screen, (255, 255, 255), (hbar_x, hbar_y, hbar_w, hbar_h), 2)

            # Draw score at top-center (always visible)
            score = int(game_world[self.ID, 8])
            score_surf = self.font.render(f"Score: {score}", True, (255, 255, 255))
            sx = self.screen.get_width() // 2 - score_surf.get_width() // 2
            self.screen.blit(score_surf, (sx, 10))
        
        # Draw bullets
        for i in range(8, 48):
            if game_world[i, 0] == 0:
                continue
            pygame.draw.circle(self.screen, (255, 255, 255), (int(game_world[i, 1]), int(game_world[i, 2])), 2)

        pygame.display.update()


    def quit_game(self):
        self.server.disconnect()
        pygame.quit()
        quit()
	

if __name__ == "__main__":
    pygame.init()
    player_client = PlayerClient()
