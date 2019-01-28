from string import Template

import numpy as np

from app_config import *
from game.animal import Animal
from game.collision import Collision
from game.movement import find_collisions, collide_animals, find_wall_collisions, collide_animal_into_wall

import pygame
import pygame.font as font


pygame.init()


BLACK = (20, 20, 20)
WHITE = (255, 255, 255)
FONT_SIZE = 30
FONT = font.SysFont('MorePerfectDOSVGA', FONT_SIZE)


class GameBoard:
    """
    Attributes;
        screen (Surface): The screen surface.
    """

    def __init__(self, screen):
        self.screen = screen
        self.walls = {
            "top": Wall([0, 1], lambda pos: pos[1] - 35),
            "left": Wall([1, 0], lambda pos: pos[0] - 30),
            "bottom": Wall([0, -1], lambda pos: screen.get_height() - pos[1] - 4),
            "right": Wall([-1, 0], lambda pos: screen.get_width() - pos[0] - 30),
        }

    def collided_with_wall(self, animal):
        for name, wall in self.walls.items():
            if wall.distance_to(animal) < 0:
                return wall


class Wall:

    def __init__(self, normal, implicit_line_equation):
        self.normal = normal / np.linalg.norm(normal)
        self.implicit_line_equation = implicit_line_equation

    def distance_to(self, animal):
        """The distance of the animal from the wall. Positive distances mean the animal is inside the wall,
        negative means that it's outside the wall."""
        return self.implicit_line_equation(animal.position + animal.radius)

class TextLine:

    def __init__(self, text):
        self.text = text
        self.text_index = 0 # index of the current char in the iteration
        self.complete = False

    def next(self):
        if self.text_index < len(self.text):
            current_text, self.text_index = self.text[:self.text_index], self.text_index + 1
            return current_text
        else:
            self.complete = True
            return self.text

    @property
    def is_complete(self):
        return self.complete


class EndText:

    def __init__(self, errors):
        self.errors = errors
        self.text_index = 0 # index of the current char in the iteration
        self.line_index = 0 # index of the current text line
        self.text = self.set_error_text(errors)

    def set_error_text(self, errors):
        if len(errors) == 0:
            return [TextLine("All errors were killed during the simulation.")]
        first_line = Template('Simulation complete. The prevailing $error_grammar:')
        error_grammar = "error is" if len(errors) == 1 else "errors are"
        end_text = [TextLine(first_line.substitute(error_grammar = error_grammar))]
        for error in errors:
            text_line = TextLine(error.error_string_code + " in " + error.filepath + " line " + str(error.line_number))
            end_text.append(text_line)
        return end_text

    def update_and_draw(self, screen):
        lines_to_draw = self.get_lines_to_draw(self.text)
        line_height = 0
        for line in lines_to_draw:
            line_text = line.next()
            text_surface = FONT.render(line_text, True, WHITE)
            text_rect = text_surface.get_rect()
            text_rect.center = (screen.get_width() / 2, screen.get_height() / 2 + line_height)
            screen.blit(text_surface, text_rect)
            line_height += FONT_SIZE

    def get_lines_to_draw(self, text_lines):
        lines_to_draw = list(filter(lambda x: x.is_complete, text_lines))
        if len(lines_to_draw) < len(text_lines):
            lines_to_draw.append(text_lines[len(lines_to_draw)])
            return lines_to_draw
        return lines_to_draw



class Engine:

    def __init__(self, screen):
        pygame.init()
        pygame.mixer.set_num_channels(4)
        self.screen = screen
        self.live_animals = pygame.sprite.Group()
        self.dying_animals = pygame.sprite.Group()
        self._play_death_sound = False
        self._play_collision_sound = False

    def start(self):
        """Start the event loop!"""
        time_step = 0.3
        clock = pygame.time.Clock()
        gameboard = GameBoard(self.screen)
        end_text = None

        running = True
        while running:
            self.screen.fill(BLACK)
            clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            for collision in find_collisions(self.live_animals):
                collide_animals(*collision.animals)
                collision.injure_animals_if_prey()
                if collision.animals_were_injured():
                    self.delayed_collision_sound()

            for wall_collision in find_wall_collisions(self.live_animals, gameboard):
                collide_animal_into_wall(*wall_collision)

            for animal in self.live_animals:
                if animal.is_dead:
                    animal.velocity = animal.velocity / animal.speed * 200
                    self.kill_animal(animal)
                    self.delayed_death_sound()

            for animal in self.dying_animals:
                if animal.death_animation_finished() or animal.off_screen(self.screen):
                    self.remove_animal(animal)

            for animal in self.all_animals:
                animal.update_subject_animal(self.live_animals)
                animal.update_position(time_step)
                animal.animal_image.update()

            if self.simulation_completed(self.all_animals):
                if end_text is None:
                    end_text = EndText([a.error for a in self.live_animals if a.error is not None])
                end_text.update_and_draw(self.screen)

            self.play_delayed_sounds()
            self.all_animals.draw(self.screen)
            pygame.display.update()
        pygame.quit()

    def delayed_death_sound(self):
        self._play_death_sound = True

    def delayed_collision_sound(self):
        self._play_collision_sound = True

    def play_delayed_sounds(self):
        """Play all the sounds then reset the flags so they don't play next loop"""
        if self._play_death_sound:
            Animal.death_sound.play()
        if self._play_collision_sound:
            Collision.sound.play()
        self._play_collision_sound, self._play_death_sound = False, False

    @property
    def all_animals(self):
        all_animals = pygame.sprite.Group()
        all_animals.add(self.live_animals)
        all_animals.add(self.dying_animals)
        return all_animals

    def remove_animal(self, animal):
        """Remove an animal from the game entirely"""
        self.live_animals.remove(animal)
        self.dying_animals.remove(animal)

    def kill_animal(self, animal):
        self.live_animals.remove(animal)
        self.dying_animals.add(animal)

    def add_animals(self, *animals):
        """Add an animal to the game"""
        for animal in animals:
            if animal.is_dead:
                self.dying_animals.add(animal)
            else:
                self.live_animals.add(animal)

    def simulation_completed(self, animals):
        if len(animals) is 0:
            return True
        else:
            for animal in animals:
                if animal.subject_animal is not None:
                    return False
            return True
