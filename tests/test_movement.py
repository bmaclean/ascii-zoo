import numpy as np
from numpy.testing import assert_array_almost_equal
import pygame
from pygame.sprite import Group

from game.animal import Animal
from game.engine import GameBoard
from game.movement import collide, find_collisions, collide_animal_into_wall, snap_to_grid_in_direction, collide_animals


def test_collision():
    # Collision along X-axis
    u1, u2 = collide([1, 0], [1, 0], [-1, 0], 1, 1)
    assert np.all(u1 == (-1, 0))
    assert np.all(u2 == (1, 0))

    # Collision along X-axis with one stationary animal
    u1, u2 = collide([1, 0], [1, 0], [0, 0], 1, 1)
    assert np.all(u1 == (0, 0))
    assert np.all(u2 == (1, 0))

    # Collision along X-axis where the center-to-center line is diagonal
    u1, u2 = collide([1, 1], [1, 0], [-1, 0], 1, 1)
    assert_array_almost_equal(u1, (0, -1))
    assert_array_almost_equal(u2, (0, 1))

    # Collision with heavy mass
    u1, u2 = collide([0, 1], [0, -1], [0, 0], 1, 10**15)
    assert_array_almost_equal(u1, [0, 1])
    assert_array_almost_equal(u2, [0, 0])

    # Collision on a diagonal directly approaching each other
    u1, u2 = collide([1, 1], [1, 1], [-1, -1], 1, 1)
    assert_array_almost_equal(u1, [-1, -1])
    assert_array_almost_equal(u2, [1, 1])


def test_find_collisions():
    group = Group()
    animal1 = Animal()
    animal2 = Animal()
    animal1.put(30, 30)
    animal2.put(50, 50)
    group.add(animal1, animal2)
    collisions = find_collisions(group)
    assert not collisions
    assert group

    animal1.put(50, 50)
    animal2.put(50, 50)
    collisions = find_collisions(group)
    assert len(collisions) == 1
    collision = collisions[0]
    np.testing.assert_array_equal((collision.animal1, collision.animal2), (animal1, animal2))
    assert group.has(animal1, animal2) and len(group) == 2


def test_collide_animals():
    """Collide two animals together"""
    animal1 = Animal()
    animal2 = Animal()

    animal1.velocity = [1, 1]
    animal2.velocity = [-1, -1]

    animal1.put(0, 0)
    animal2.put(1, 1)

    collide_animals(animal1, animal2)

    assert_array_almost_equal(animal1.velocity, [-1, -1])
    assert_array_almost_equal(animal2.velocity, [1, 1])


def test_collide_animal_into_wall():
    animal = Animal()
    screen = pygame.Surface((600, 600))
    gameboard = GameBoard(screen)

    # Send the animal shooting into the top left corner
    animal.velocity = [-10, -10]
    collide_animal_into_wall(animal, gameboard.walls["top"])
    assert_array_almost_equal(animal.velocity, [-10, 10])

    # Toward the left wall now
    collide_animal_into_wall(animal, gameboard.walls["left"])
    assert_array_almost_equal(animal.velocity, [10, 10])

    # Toward the bottom wall now
    collide_animal_into_wall(animal, gameboard.walls["bottom"])
    assert_array_almost_equal(animal.velocity, [10, -10])

    # Toward the right wall now
    collide_animal_into_wall(animal, gameboard.walls["right"])
    assert_array_almost_equal(animal.velocity, [-10, -10])


def test_snap_to_grid_in_direction():
    point = (10.1, 10.1)
    assert np.array_equal(snap_to_grid_in_direction(point, [-1, -1]), [10, 10])
    assert np.array_equal(snap_to_grid_in_direction(point, [-1, 1]), [10, 11])
    assert np.array_equal(snap_to_grid_in_direction(point, [1, 1]), [11, 11])
    assert np.array_equal(snap_to_grid_in_direction(point, [1, -1]), [11, 10])
