import pygame
import pytest

from game.animal import Animal
from game.engine import Engine


@pytest.mark.skip(reason="Skip this because it opens the pygame window and we don't want that")
def test_game():
    animal1 = Animal(shape="Y", max_health=2, size=40)
    animal2 = Animal(shape="X", max_health=2, size=40)

    animal1.also_likes_to_eat(animal2)
    animal2.also_likes_to_eat(animal1)

    screen = pygame.display.set_mode((600, 600))

    animal1.put_relative(30, 30, screen)
    animal2.put_relative(60, 60, screen)

    engine = Engine(screen)
    engine.add_animals(animal1, animal2)
    engine.start()


def test_off_screen():
    screen = pygame.Surface((100, 100))
    animal = Animal()
    animal.put(100, 100)
    assert animal.off_screen(screen) == False
    animal.put(100, 101 + animal.height + 1)
    assert animal.off_screen(screen) == True
    animal.put(101 + animal.width, 50)
    assert animal.off_screen(screen) == True
    animal.put(-1 - animal.width, 50)
    assert animal.off_screen(screen) == True
    animal.put(50, -1 - animal.height)
    assert animal.off_screen(screen) == True
    animal.put(50, 50)
    assert animal.off_screen(screen) == False
    animal.put(0, 0)
    assert animal.off_screen(screen) == False
