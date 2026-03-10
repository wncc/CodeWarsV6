"""
Weapon Visual Effects System
Provides muzzle flashes, impact particles, and enhanced visuals
"""
import pygame
import numpy as np
import random
import math

class Particle:
    """Single particle for effects"""
    def __init__(self, x, y, vx, vy, color, size, lifetime):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alive = True
    
    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
    
    def draw(self, screen):
        if not self.alive:
            return
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        color_with_alpha = (*self.color[:3], alpha)
        size = max(1, int(self.size * (self.lifetime / self.max_lifetime)))
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)


class MuzzleFlash:
    """Muzzle flash effect when shooting"""
    def __init__(self, x, y, angle, weapon_id):
        self.x = x
        self.y = y
        self.angle = angle
        self.weapon_id = weapon_id
        self.lifetime = 0.05  # 50ms flash
        self.max_lifetime = 0.05
        self.alive = True
        
        # Weapon-specific flash properties
        self.size, self.color = self._get_flash_properties(weapon_id)
    
    def _get_flash_properties(self, weapon_id):
        """Get flash size and color based on weapon"""
        # Pistols (1, 2, 6)
        if weapon_id in [1, 2, 6]:
            size = 12 if weapon_id == 6 else 10  # Magnum bigger
            color = (255, 215, 0) if weapon_id == 2 else (255, 200, 100)  # Golden for Golden Deagle
            return size, color
        
        # Assault Rifles (0, 4, 12, 13)
        elif weapon_id in [0, 4, 12, 13]:
            size = 10
            color = (255, 180, 50) if weapon_id == 13 else (255, 150, 50)  # XM8 slightly blue-ish
            return size, color
        
        # SMGs (7, 8, 9)
        elif weapon_id in [7, 8, 9]:
            size = 7
            color = (255, 200, 100)
            return size, color
        
        # Snipers (3, 5)
        elif weapon_id in [3, 5]:
            size = 15 if weapon_id == 5 else 12
            color = (255, 255, 200)
            return size, color
        
        # Shotgun (10)
        elif weapon_id == 10:
            size = 14
            color = (255, 150, 50)
            return size, color
        
        # SMAW (11)
        elif weapon_id == 11:
            size = 20
            color = (255, 100, 0)
            return size, color
        
        # Minigun (14)
        elif weapon_id == 14:
            size = 8
            color = (255, 200, 150)
            return size, color
        
        # Default
        return 10, (255, 200, 100)
    
    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
    
    def draw(self, screen):
        if not self.alive:
            return
        
        alpha_factor = self.lifetime / self.max_lifetime
        current_size = int(self.size * (0.5 + 0.5 * alpha_factor))
        
        # Draw outer glow
        outer_color = (self.color[0] // 2, self.color[1] // 2, self.color[2] // 2)
        pygame.draw.circle(screen, outer_color, (int(self.x), int(self.y)), current_size + 3)
        
        # Draw main flash
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), current_size)
        
        # Draw bright center
        center_color = (255, 255, 255)
        pygame.draw.circle(screen, center_color, (int(self.x), int(self.y)), max(2, current_size // 2))


class ImpactEffect:
    """Impact effect when bullet hits something"""
    def __init__(self, x, y, weapon_id):
        self.x = x
        self.y = y
        self.weapon_id = weapon_id
        self.particles = []
        self.alive = True
        
        # Create particles based on weapon type
        num_particles = self._get_particle_count(weapon_id)
        colors = self._get_impact_colors(weapon_id)
        
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice(colors)
            size = random.randint(2, 4)
            lifetime = random.uniform(0.1, 0.3)
            
            self.particles.append(Particle(x, y, vx, vy, color, size, lifetime))
    
    def _get_particle_count(self, weapon_id):
        """Number of particles based on weapon"""
        if weapon_id in [3, 5]:  # Snipers
            return 12
        elif weapon_id == 10:  # Shotgun
            return 8
        elif weapon_id == 11:  # SMAW
            return 20
        elif weapon_id in [7, 8, 9]:  # SMGs
            return 4
        else:
            return 6
    
    def _get_impact_colors(self, weapon_id):
        """Impact colors based on weapon"""
        if weapon_id == 2:  # Golden Deagle
            return [(255, 215, 0), (255, 255, 100), (255, 200, 50)]
        elif weapon_id == 11:  # SMAW
            return [(255, 100, 0), (255, 150, 0), (255, 200, 0)]
        else:
            return [(255, 255, 200), (255, 200, 100), (200, 200, 200)]
    
    def update(self, dt):
        for particle in self.particles:
            particle.update(dt)
        
        # Remove dead particles
        self.particles = [p for p in self.particles if p.alive]
        
        if len(self.particles) == 0:
            self.alive = False
    
    def draw(self, screen):
        for particle in self.particles:
            particle.draw(screen)


class GrenadeExplosionEffect:
    """Animated grenade explosion effect with burst particles and shockwave ring."""
    def __init__(self, x, y, grenade_type):
        self.x = x
        self.y = y
        self.grenade_type = grenade_type
        self.particles = []
        self.lifetime = 0.45
        self.max_lifetime = 0.45
        self.alive = True

        burst_colors, particle_count, max_ring_radius = self._get_grenade_style(grenade_type)
        self.max_ring_radius = max_ring_radius

        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2.5, 6.5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice(burst_colors)
            size = random.randint(2, 5)
            lifetime = random.uniform(0.15, 0.4)
            self.particles.append(Particle(x, y, vx, vy, color, size, lifetime))

    def _get_grenade_style(self, grenade_type):
        if grenade_type == 2:  # Proxy
            return ([(255, 255, 220), (255, 120, 80), (255, 200, 120)], 28, 44)
        if grenade_type == 3:  # Gas
            return ([(180, 255, 180), (90, 220, 90), (220, 255, 220)], 24, 52)
        # Frag/default
        return ([(255, 230, 130), (255, 170, 70), (255, 255, 220)], 32, 50)

    def update(self, dt):
        self.lifetime -= dt
        for particle in self.particles:
            # Light gravity to make the burst feel natural.
            particle.vy += 0.08
            particle.update(dt)

        self.particles = [p for p in self.particles if p.alive]
        if self.lifetime <= 0 and len(self.particles) == 0:
            self.alive = False

    def draw(self, screen):
        life_ratio = max(0.0, self.lifetime / self.max_lifetime)
        ring_progress = 1.0 - life_ratio
        ring_radius = max(1, int(self.max_ring_radius * ring_progress))

        # Shockwave ring
        ring_color = (255, 230, 180) if self.grenade_type != 3 else (140, 255, 140)
        ring_thickness = max(1, int(4 * life_ratio))
        pygame.draw.circle(screen, ring_color, (int(self.x), int(self.y)), ring_radius, ring_thickness)

        # Bright core flash
        core_radius = max(1, int(10 * life_ratio))
        core_color = (255, 255, 240) if self.grenade_type != 3 else (220, 255, 220)
        pygame.draw.circle(screen, core_color, (int(self.x), int(self.y)), core_radius)

        for particle in self.particles:
            particle.draw(screen)


class WeaponEffectsManager:
    """Manages all weapon visual effects"""
    def __init__(self):
        self.muzzle_flashes = []
        self.impact_effects = []
        self.grenade_explosions = []
        self.last_shot_time = {}  # Track last shot per player for effects
    
    def add_muzzle_flash(self, x, y, angle, weapon_id):
        """Add a muzzle flash effect"""
        flash = MuzzleFlash(x, y, angle, weapon_id)
        self.muzzle_flashes.append(flash)
    
    def add_impact_effect(self, x, y, weapon_id):
        """Add an impact effect"""
        effect = ImpactEffect(x, y, weapon_id)
        self.impact_effects.append(effect)

    def add_grenade_explosion(self, x, y, grenade_type):
        """Add a grenade explosion effect."""
        effect = GrenadeExplosionEffect(x, y, grenade_type)
        self.grenade_explosions.append(effect)
    
    def update(self, dt):
        """Update all effects"""
        # Update muzzle flashes
        for flash in self.muzzle_flashes:
            flash.update(dt)
        self.muzzle_flashes = [f for f in self.muzzle_flashes if f.alive]
        
        # Update impact effects
        for effect in self.impact_effects:
            effect.update(dt)
        self.impact_effects = [e for e in self.impact_effects if e.alive]

        # Update grenade explosion effects
        for effect in self.grenade_explosions:
            effect.update(dt)
        self.grenade_explosions = [e for e in self.grenade_explosions if e.alive]
    
    def draw(self, screen):
        """Draw all effects"""
        # Draw impact effects first (behind bullets)
        for effect in self.impact_effects:
            effect.draw(screen)
        
        # Draw muzzle flashes on top
        for flash in self.muzzle_flashes:
            flash.draw(screen)

        # Draw grenade explosions on top for visibility
        for effect in self.grenade_explosions:
            effect.draw(screen)
    
    def clear(self):
        """Clear all effects"""
        self.muzzle_flashes.clear()
        self.impact_effects.clear()
        self.grenade_explosions.clear()
