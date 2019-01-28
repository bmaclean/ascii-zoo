import os
import numpy as np
import logging

from colour import Color
import pygame
import pygame.font as font

from app_config import root_dir


pygame.init()


def get_color_tuple(color_string):
    c = Color(color_string)
    return tuple([255 * x for x in c.rgb])


class AnimalImage:

    def __init__(self, shape, color, max_health, size):
        self.shape = font.Font(None, size).render(shape, False, color)
        self.health_bar = HealthBar(max_health)

        width = max(self.shape.get_width(), self.health_bar.get_width())
        height = self.shape.get_height() + self.health_bar.get_height()
        self._image = pygame.Surface((width, height), pygame.SRCALPHA, 32)

        self.num_death_frames = 20
        self.death_frames_executed = 0

        self.blit_animal()

    @property
    def image(self):
        return pygame.transform.rotozoom(self._image, self.angle, self.scale)

    @property
    def scale(self):
        return self.death_frames_executed/10 + 1

    @property
    def angle(self):
        return self.death_frames_executed*10

    @property
    def alpha(self):
        return 256 - self.death_frames_executed / self.num_death_frames * 256

    def death_animation_finished(self):
        return self.death_frames_executed > self.num_death_frames

    def blank_image(self):
        self._image.fill((0, 0, 0, 0))

    def blit_animal(self):
        self.blank_image()
        self.blit_health_bar()
        self.blit_shape()

    def blit_shape(self):
        """Draw the shape of the animal"""
        self._image.blit(self.shape, (self._image.get_width() / 2 - self.shape.get_width() / 2, 0))

    def blit_health_bar(self):
        """Draw the animal's health bar"""
        self._image.blit(self.health_bar, (0, self.shape.get_height()))

    def update(self):
        self.blank_image()
        self.blit_shape()
        if self.health_bar.is_dead:
            self.death_frames_executed += 1
        else:
            self.blit_health_bar()


class HealthBar(pygame.Surface):

    width_per_health_point = 3
    height = 5

    def __init__(self, max_health, *args, **kwargs):
        super().__init__((self.width_per_health_point * max_health, self.height), *args, **kwargs)
        self.max_health = max_health
        self.current_health = max_health
        self.update()

    @property
    def current_health_width(self):
        """Return the width of the current_health part of the health bar"""
        return self.current_health / self.max_health * self.get_width()

    @property
    def current_health_rect(self):
        return pygame.rect.Rect(0, 0, self.current_health_width, self.get_height())

    @property
    def is_dead(self):
        return self.current_health <= 0

    def reduce_health(self, amount):
        """Decrease the health by amount"""
        self.current_health -= amount
        self.update()

    def update(self):
        """Update the image"""
        self.fill((100, 0, 0))
        if self.current_health > 0:
            pygame.draw.rect(self, (0, 100, 0), self.current_health_rect)


class Animal(pygame.sprite.Sprite):

    death_sound_filepath = os.path.join(root_dir, 'assets/wilhelm_scream.wav')
    death_sound = pygame.mixer.Sound(death_sound_filepath)

    def __init__(self, shape=".", eats=None, color="white", max_health=10, max_speed=50, mass=1, size=20,
                 exertion_magnitude=20, damage_infliction_magnitude=1, error=None):
        pygame.sprite.Sprite.__init__(self)

        self.error = error
        self.eats = set() if eats is None else eats

        self.animal_image = AnimalImage(shape, get_color_tuple(color), max_health, size)
        self.rect = self.animal_image.shape.get_rect()
        # This is useful for collisions
        self.radius = min(self.rect.width, self.rect.height)

        # Give the animal zero velocity initially
        self._velocity = [0, 0]
        self.max_speed = max_speed

        self.damage_infliction_magnitude = damage_infliction_magnitude

        self.mass = mass
        self.propulsion_force_magnitude = exertion_magnitude
        self.slow_down_force_magnitude = exertion_magnitude

        # Initial propulsion force should be zero because there's no subject yet
        self.propulsion_force = np.array([0, 0])
        self.slow_down_force = np.array([0, 0])

        self._subject_animal = None

    def also_likes_to_eat(self, *animals):
        """Add the given animals to the list of animals this animal like to eat."""
        for animal in animals:
            if animal == self:
                raise ValueError("Animals shouldn't want to eat themselves!")
            self.eats.add(animal)

    def wants_to_eat(self, animal):
        """Return true if this animal wants to eat the given animal"""
        return animal in self.eats

    @property
    def image(self):
        """Used by pygame to get the image corresponding to this animal"""
        return self.animal_image.image

    def inflict_damage(self, animal):
        """Inflict some damage on the given animal"""
        animal.reduce_health(self.damage_infliction_magnitude)

    @property
    def subject_animal(self):
        """
        This is the animal that this animal has its attention on. It could either want to run away or chase it.
        """
        return self._subject_animal

    @subject_animal.setter
    def subject_animal(self, animal):
        self._subject_animal = animal
        if animal is None or self.on_top(animal):
            self.propulsion_force = np.array([0, 0])
        elif self.wants_to_eat(animal):
            self.propulsion_force = self.normalized_vector_to(animal) * self.propulsion_force_magnitude
        elif animal.wants_to_eat(self):
            self.propulsion_force = -self.normalized_vector_to(animal) * self.propulsion_force_magnitude
        else:
            raise ValueError("The given subject animal is neither prey nor hunter, this is probably a bug.")

    def on_top(self, animal):
        """Return true if the given animal is on top of this one"""
        return np.array_equal(self.position, animal.position)

    @property
    def width(self):
        return self.rect.width

    @property
    def height(self):
        return self.rect.height

    @property
    def speed(self):
        """Scalar magnitude of velocity"""
        return np.linalg.norm(self.velocity)

    @property
    def velocity(self):
        return self._velocity

    @velocity.setter
    def velocity(self, velocity):
        if self.speed > self.max_speed:
            self.slow_down_force = -self.velocity / self.speed * self.slow_down_force_magnitude
        else:
            self.slow_down_force = np.array([0, 0])
        self._velocity = np.array(velocity)

    @property
    def position(self):
        return np.array(self.rect.center)

    @position.setter
    def position(self, value):
        self.rect.center = value

    @property
    def x(self):
        return self.position[0]

    @property
    def y(self):
        return self.position[1]

    @property
    def is_dead(self):
        return self.animal_image.health_bar.is_dead

    @property
    def health(self):
        return self.animal_image.health_bar.current_health

    def reduce_health(self, amount=1):
        """Reduce the health of the animal and update the health bar"""
        self.animal_image.health_bar.reduce_health(amount)

    def off_screen(self, screen):
        return (
                self.x < -self.width or
                self.y < -self.height or
                self.x > screen.get_width() + self.width or
                self.y > screen.get_height() + self.height
        )

    def put_relative(self, x_relative_position, y_relative_position, screen):
        """
        Put the animal at an absolute coordinate on our screen.

        Args:
            {x,y}_relative_position: See the documentation for PutNode.
        """
        self.position = (screen.get_width() * x_relative_position / 100,
                         screen.get_height() * y_relative_position / 100)

    def put(self, x, y):
        self.position = (x, y)

    def distance_to(self, animal):
        """Return the distance to the other animal"""
        return np.linalg.norm(self.vector_to(animal))

    def vector_to(self, animal):
        """Return a vector pointing to the other animal"""
        return animal.position - self.position

    def normalized_vector_to(self, animal):
        """Return a normalized vector pointing to the other animal"""
        vector = self.vector_to(animal)
        distance = self.distance_to(animal)
        if distance == 0:
            raise ValueError("Can't calculate the direction vector pointing toward the other animal when the other "
                             "animal is exactly on top of this one.")
        return vector / distance

    def death_animation_finished(self):
        return self.animal_image.death_animation_finished()

    def update_subject_animal(self, animal_group):
        """Given a group of animals, find the most interesting animal."""

        # NOTE: This does not take into a account other animals that want to eat this one. Since if a given animal is
        # the prey of another, the other animal must also be the prey of this one so this is fine for now

        # Intersect the animals this animal wants to eat, with the given animal group
        self.eats = self.eats.intersection(animal_group.sprites())

        self.subject_animal = None

        if self.is_dead:
            return

        animals = list(self.eats)
        animals.sort(key=lambda x: self.distance_to(x))

        for animal in animals:
            # Take the first animal
            self.subject_animal = animal
            return

    def update_position(self, time_step):
        """Given a time_step, apply the forces the animal is currently experiencing for the given time_step to
        compute its new position and velocity"""
        acceleration = (self.propulsion_force + self.slow_down_force) / self.mass
        self.velocity = self.velocity + acceleration * time_step
        self.position = self.position + self.velocity * time_step
