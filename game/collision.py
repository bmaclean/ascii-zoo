import os
from app_config import root_dir
import pygame


class Collision:
    sound_filepath = os.path.join(root_dir, 'assets/zapsplat_cartoon_punch_002_17900.wav')
    sound = pygame.mixer.Sound(sound_filepath)

    def __init__(self, animal1, animal2):
        self.animal1 = animal1
        self.animal2 = animal2

    @property
    def animals(self):
        return self.animal1, self.animal2

    def injure_animals_if_prey(self):
        if self.animal1.wants_to_eat(self.animal2):
            self.animal1.inflict_damage(self.animal2)
        if self.animal2.wants_to_eat(self.animal1):
            self.animal2.inflict_damage(self.animal1)

    def animals_were_injured(self):
        return self.animal1.wants_to_eat(self.animal2) or self.animal2.wants_to_eat(self.animal1)

