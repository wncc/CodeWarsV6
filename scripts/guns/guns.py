import time
import math

def spawn_bullet(x, y, angle, speed, damage):
    return {
        "x": x,
        "y": y,
        "vx": math.cos(angle) * speed,
        "vy": math.sin(angle) * speed,
        "damage": damage,
        "radius": 4
    }

class Gun(object):
    def __init__(self, name,damage,accuracy,reloadtime,melee, rpf,effective_range,dual_wielding, rate_of_fire, magazine_capacity,ammo_given,sprite,distancefactor=1.0, harm=False):
        self.name = name
        self.distancefactor = distancefactor   # multiplier for effective range
        self.effective_range = effective_range  # in meters
        self.damage=damage  # damage per shot
        self.rpf=rpf  # rounds per fire
        self.accuracy=accuracy  # accuracy percentage
        self.reload_time = reloadtime  # time to reload in seconds
        self.meleedamage=melee  # melee damage
        self.rate_of_fire = rate_of_fire  # rounds per minute
        self.magazine_capacity = magazine_capacity  # number of rounds
        self.current_ammo = magazine_capacity  # starts full
        self.ammo_given = ammo_given  # total ammo given
        self.sprite = sprite  # visual representation
        self.harm = harm  # damage potential
        self.dual_wielding = dual_wielding  # can be dual-wielded
        
    def display_info(self):
        info = f"Gun Name: {self.name}\n"
        info += f"Effective Range: {self.effective_range} meters\n"
        info += f"Rate of Fire: {self.rate_of_fire} rounds per minute\n"
        info += f"Magazine Capacity: {self.magazine_capacity}\n"
        info += f"Current Ammo: {self.current_ammo}\n"
        info += f"Ammo Given: {self.ammo_given}\n"
        info += f"Sprite: {self.sprite}\n"
        return info
    def reload(self):
        self.current_ammo = self.magazine_capacity
        print("Reloading...")
        time.sleep(self.reload_time)
        return f"{self.name} reloaded to full capacity."
    def shoot(self, x, y, angle):
        if self.current_ammo >= self.rpf:
            for i in range(self.rpf):
                bullet = spawn_bullet(x, y, angle, speed=50, damage=self.damage)
                # Here you would typically add the bullet to a game world or list
            self.current_ammo -= self.rpf
            return f"Fired {self.rpf} rounds from {self.name}."
        else:
            return "Not enough ammo to shoot."
        
        
guns = []

guns.append(Gun("AK47", 10, 4, 2, 30, 1, 800, False, 0.1, 35, 250, "ak47.png"))

guns.append(Gun("Desert Eagle", 8, 2, 1.25, 15, 1, 500, False, 0.25, 15, 75, "deagle.png"))

guns.append(Gun("Golden Deagle", 10, 2, 1.25, 25, 1, 600, False, 0.2, 15, 75, "gdeagle.png"))

guns.append(Gun("M14", 36, 0, 2.25, 35, 1, 1200, False, 0.55, 6, 36, "m14.png"))

guns.append(Gun("M4", 14, 2, 2, 30, 1, 1000, False, 0.5, 24, 300, "m4.png"))

guns.append(Gun("M93BA Sniper", 75, 0, 2.5, 35, 1, 1500, False, 0.8, 3, 20, "sniper.png"))

guns.append(Gun("Magnum", 30, 1, 2, 25, 1, 650, False, 0.6, 6, 36, "magnum.png"))

guns.append(Gun("MP5", 7, 5, 1.75, 30, 1, 700, True, 0.06, 50, 400, "mp5.png"))

guns.append(Gun("UZI", 7, 6, 1.5, 20, 1, 500, True, 0.1, 40, 400, "uzi.png"))

guns.append(Gun("TEC9", 10, 4, 1.5, 25, 1, 600, True, 0.15, 40, 400, "tec9.png"))

guns.append(Gun("SPAS-12", 25, 10, 2.5, 40, 5, 325, False, 0.75, 5, 24, "Shotgun.png"))

guns.append(Gun("SMAW", 1, 0, 4, 35, 1, 1, False, 1.25, 3, 6, "smaw.png"))

guns.append(Gun("TAVOR", 9, 2, 1.5, 30, 1, 750, False, 0.12, 35, 200, "tavor.png"))

guns.append(Gun("XM8", 8, 3.25, 1.9, 30, 1, 875, False, 0.085, 30, 200, "xm8.png"))

guns.append(Gun("MINIGUN", 30, 7, 4.25, 35, 1, 650, False, 0.08, 50, 200, "minigun.png"))

for gun in guns:
    print(gun.display_info())