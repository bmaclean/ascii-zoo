import click
import pygame

from game.animal import Animal
from game.engine import Engine


engine = None
screen = None


def sample_1():
    animal1 = Animal(shape="E", color="red", size=45, mass=2, exertion_magnitude=40, max_health=50)
    animal2 = Animal(shape="W", color="orange", size=30, mass=1, exertion_magnitude=20, max_health=40,
                     damage_infliction_magnitude=.2)
    animal3 = Animal(shape="W", color="orange", size=30, mass=1, exertion_magnitude=20, max_health=40,
                     damage_infliction_magnitude=.2)

    animal1.put_relative(5, 5, screen)
    animal2.put_relative(95, 95, screen)
    animal3.put_relative(90, 90, screen)

    animal1.velocity = [0, 30]
    animal2.velocity = [0, -30]
    animal3.velocity = [0, -30]

    animal1.also_likes_to_eat(animal2, animal3)
    animal2.also_likes_to_eat(animal1)
    animal3.also_likes_to_eat(animal1)

    engine.add_animals(animal1, animal2, animal3)


@click.command()
@click.argument("sample_number")
@click.option("--resolution", nargs=2, type=int)
def run(sample_number, resolution):
    global engine, screen
    print("hi")
    screen = pygame.display.set_mode(resolution if resolution else (600, 600))
    engine = Engine(screen)
    globals()[f"sample_{sample_number}"]()
    engine.start()


if __name__ == "__main__":
    run()