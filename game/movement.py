import math
import logging
import numpy as np
import random

from game.collision import Collision
from pygame.sprite import Group, collide_circle

logger = logging.getLogger(__name__)


def find_collisions(animal_group):
    """Find all collisions in the group. Three way collisions can't be found because once a collision pair is found,
    we stop looking for collisions for those two."""
    animal_group = animal_group.copy()
    collisions = []
    while animal_group:
        animal = animal_group.sprites()[0]
        animal_group.remove(animal)
        collision = find_collision(animal, animal_group.copy())
        if collision:
            animal_group.remove(collision.animals)
            collisions.append(collision)
    return collisions


def find_collision(animal, animal_group):
    """Return the first collision found between animal and the group"""
    for other_animal in animal_group:
        if collide_circle(animal, other_animal):
            collision = Collision(animal, other_animal)
            return collision


def find_wall_collisions(animal_group, gameboard):
    for animal in animal_group:
        wall = gameboard.collided_with_wall(animal)
        if wall:
            yield animal, wall


def collide_animal_into_wall(animal, wall):
    """Collide the animal into the wall, the collision is a bit different because the wall is very heavy compared to
    the animal."""

    distance = wall.distance_to(animal)
    if distance < 0:
        position = animal.position + wall.normal * math.ceil(abs(distance))
        animal.position = snap_to_grid_in_direction(position, wall.normal)

    animal.velocity, _ = collide(
        wall.normal,
        # Wall has zero velocity
        animal.velocity, [0, 0],
        # Wall is much heavier than the animal
        1, 10 ** 15
    )


def snap_to_grid_in_direction(p1, direction):
    """Snap p1 to the nearest grid point as long as it makes it go further away from p2"""
    array = np.array([np.ceil(p1[0]) if direction[0] > 0 else np.floor(p1[0]),
                      np.ceil(p1[1]) if direction[1] > 0 else np.floor(p1[1])])
    array.astype("int")
    return array


def collide_animals(animal, other_animal):
    """Collide two animals into each other, setting their appropriate velocities after the collision"""
    distance = animal.distance_to(other_animal)

    if distance == 0:
        # This is a really tricky case because the animals are exactly on top of each other. How do we choose the
        # axis of their collision in this case? There's no clear to pick it and the wrong choice for a particular
        # collision could result in major bugs, so just let them go through each other
        return

    # Compute vector that joins the animal centers
    center_to_center = animal.normalized_vector_to(other_animal)

    # If the animals are within each other's bounding circles, we can't have that so move them apart a bit
    if distance < animal.radius + other_animal.radius:
        too_close_by = int(np.ceil(animal.radius + other_animal.radius - distance))
        p1 = animal.position - center_to_center * too_close_by / 2
        p2 = other_animal.position + center_to_center * too_close_by / 2
        animal.position = snap_to_grid_in_direction(p1, -center_to_center)
        other_animal.position = snap_to_grid_in_direction(p2, center_to_center)

    animal.velocity, other_animal.velocity = collide(
        center_to_center,
        animal.velocity, other_animal.velocity,
        animal.mass, other_animal.mass
    )


def collide(center_to_center, v1, v2, m1, m2):
    """Collide two masses with mass m1 and m2, and velocities v1 and v2. The direction vector between their centers is
    given by center_to_center."""

    if np.linalg.norm(center_to_center) == 0:
        raise ValueError("Center to center distance for the collision is zero. There's no way to determine the "
                         "directionality of the collision when the two masses are exactly on top of each other.")

    # Find the angle between the i vector and the center_to_center line
    phi = np.arccos(center_to_center[0] / np.linalg.norm(center_to_center))
    # Align the x-coordinate with center_to_center line
    rotation_matrix = np.array([[np.cos(phi),  np.sin(phi)],
                                [-np.sin(phi), np.cos(phi)]])
    v1 = rotation_matrix.dot(v1)
    v2 = rotation_matrix.dot(v2)

    u1x = ((m1 - m2) * v1[0] + (m2 + m2) * v2[0]) / (m1 + m2)
    u2x = ((m1 + m1) * v1[0] + (m2 - m1) * v2[0]) / (m1 + m2)

    u1 = (u1x, v1[1])
    u2 = (u2x, v2[1])

    rotation_matrix_inverse = np.linalg.inv(rotation_matrix)

    return rotation_matrix_inverse.dot(u1), rotation_matrix_inverse.dot(u2)
