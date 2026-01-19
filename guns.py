class guns(object):
    def __init__(self, name, effective_range,dual_wielding, rate_of_fire, magazine_capacity,ammo_given,sprite,distancefactor=1.0, harm=False):
        self.name = name
        self.distancefactor = distancefactor   # multiplier for effective range
        self.effective_range = effective_range  # in meters
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
