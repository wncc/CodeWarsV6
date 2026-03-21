import math
import sys
import os
import numpy as np

# Add project root to path so root-level modules are importable
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config import WEAPON_STATS

class Gun:
    def __init__(self, gun_id, name, damage, accuracy, reload_time, melee, rpf, 
                 scope,effective_range, dual_wielding, rate_of_fire, magazine_capacity, 
                 ammo_given, sprite_file, bullet_speed=50):
        self.gun_id = gun_id
        self.name = name
        self.scope = scope # scope multiplier for visiblity
        self.damage = damage  # damage per shot
        self.accuracy = accuracy  # accuracy spread in degrees
        self.reload_time = reload_time  # time to reload in seconds
        self.melee_damage = melee  # melee damage
        self.rpf = rpf  # rounds per fire (bullets per shot)
        self.effective_range = effective_range  # in pixels
        self.dual_wielding = dual_wielding  # can be dual-wielded
        self.rate_of_fire = rate_of_fire  # time between shots in seconds
        self.magazine_capacity = magazine_capacity  # number of rounds
        self.ammo_given = ammo_given  # total ammo given
        self.sprite_file = sprite_file  # PNG filename in assets/guns/
        self.bullet_speed = bullet_speed  # bullet velocity
        
        # Runtime state (per player)
        self.current_ammo = magazine_capacity
        self.total_ammo = ammo_given
        
    def can_shoot(self):
        """Check if gun has ammo to shoot"""
        return self.current_ammo >= self.rpf
    
    def shoot(self):
        """Consume ammo for shooting"""
        if self.can_shoot():
            self.current_ammo -= self.rpf
            return True
        return False
    
    def reload(self):
        """Reload the gun from total ammo"""
        ammo_needed = self.magazine_capacity - self.current_ammo
        if self.total_ammo > 0:
            ammo_to_reload = min(ammo_needed, self.total_ammo)
            self.current_ammo += ammo_to_reload
            self.total_ammo -= ammo_to_reload
            return True
        return False
    
    def get_bullet_angle_with_spread(self, base_angle):
        """Calculate bullet angle with accuracy spread"""
        if self.accuracy > 0:
            spread = (np.random.random() - 0.5) * self.accuracy * (math.pi / 180)
            return base_angle + spread
        return base_angle


# Define all weapons with IDs from config
WEAPONS = {}

# Initialize weapons from config
for weapon_id, stats in WEAPON_STATS.items():
    WEAPONS[weapon_id] = Gun(
        gun_id=weapon_id,
        name=stats["name"],
        damage=stats["damage"],
        accuracy=stats["accuracy"],
        reload_time=stats["reload_time"],
        melee=stats["melee"],
        rpf=stats["rpf"],
        scope=stats["scope"],
        effective_range=stats["effective_range"],
        dual_wielding=stats["dual_wielding"],
        rate_of_fire=stats["rate_of_fire"],
        magazine_capacity=stats["magazine_capacity"],
        ammo_given=stats["ammo_given"],
        sprite_file=stats["sprite_file"],
        bullet_speed=stats["bullet_speed"],
    )


def get_weapon(weapon_id):
    """Get a fresh copy of a weapon"""
    if weapon_id in WEAPONS:
        weapon = WEAPONS[weapon_id]
        return Gun(
            weapon.gun_id, weapon.name, weapon.damage, weapon.accuracy,
            weapon.reload_time, weapon.melee_damage, weapon.rpf, weapon.scope,
            weapon.effective_range, weapon.dual_wielding, weapon.rate_of_fire,
            weapon.magazine_capacity, weapon.ammo_given, weapon.sprite_file,
            weapon.bullet_speed
        )
    return None


def get_all_weapon_names():
    """Get list of all weapon names"""
    return [WEAPONS[i].name for i in sorted(WEAPONS.keys())]

class Grenade:
    def __init__(self, grenade_id, name, damage, blast_radius, fuse_time, sprite_file, effect_time, proxy):
        self.grenade_id = grenade_id
        self.name = name
        self.damage = damage
        self.blast_radius = blast_radius
        self.effect_time = effect_time
        self.fuse_time = fuse_time
        self.sprite_file = sprite_file
        self.is_proxy = proxy

grenades = {
    1: Grenade(1, "Frag Grenade", damage=1000, blast_radius=100, fuse_time=3, effect_time=1, sprite_file="frag_grenade.png", proxy=False),
    2: Grenade(2, "Proximity Grenade", damage=800, blast_radius=80, fuse_time=5, effect_time=1.5, sprite_file="prox_grenade.png", proxy=True),
    3: Grenade(3, "Gas Grenade", damage=750, blast_radius=100, fuse_time=2, effect_time=10, sprite_file="gas_grenade.png", proxy=False)
}

def get_grenade(grenade_id):
    """Get a fresh copy of a grenade"""
    if grenade_id in grenades:
        grenade = grenades[grenade_id]
        return Grenade(
            grenade.grenade_id, grenade.name, grenade.damage, grenade.blast_radius,
            grenade.fuse_time, grenade.sprite_file, grenade.effect_time, grenade.is_proxy
        )
    return None

def get_all_grenade_names():
    """Get list of all grenade names"""
    return [grenades[i].name for i in sorted(grenades.keys())]
