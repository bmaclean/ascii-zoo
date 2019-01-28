import math
import random
from subprocess import run, PIPE
import logging
import re

import click
import pandas as pd
import pygame
import numpy as np

from game.engine import Engine
from game.animal import Animal


def lint(pylint_args):
    """Run pylint"""
    logging.info("Starting the linter!")
    command = list(pylint_args)
    command.insert(0, "pylint")
    command.append("--output-format=parseable")
    result = run(command, stdout=PIPE)
    pylint_output = result.stdout.decode("utf8")
    print(pylint_output)
    lines = pylint_output.split("\n")
    return lines


def parse_line(line):
    """Use regex to parse out the important info from a pylint output line"""
    m = re.match(r"(.*?):(\d+): \[([CRWEF])(\d{4})\((.*)\), (.+?)?(?:\.(.*?))?\].*", line)
    if m:
        return {
            "filepath": m.group(1),
            "line_number": int(m.group(2)),
            "error_category": m.group(3),
            "error_code": int(m.group(4)),
            "error_string_code": m.group(5),
            "offending_object": m.group(6) if m.group(6) is not None else "",
            "offending_method": m.group(7) if m.group(7) is not None else "",
        }


def parse(pylint_output):
    """Parse the given pylint output and return a pandas DataFrame"""
    parsed_lines = []
    for line in pylint_output:
        parsed_line = parse_line(line)
        if parsed_line is None:
            # If the parse_line returns None, that means it couldn't parse the line because it didn't fit into the
            # expected regex. In this case it's probably because we got one of these lines:
            #     ------------------------------------------------------------------
            #     Your code has been rated at 6.68/10 (previous run: 6.68/10, +0.00)
            # So just continue along
            continue
        parsed_lines.append(parsed_line)
    logging.info(f"{len(parsed_lines)} errors reported.")
    return pd.DataFrame(parsed_lines)


def pin_groups_against_each_other(animal_groups):
    for animal_group in animal_groups:
        for other_animal_group in animal_groups:
            if animal_group == other_animal_group:
                continue
            for animal in animal_group:
                animal.also_likes_to_eat(*other_animal_group)


def create_animals(df):
    """Create some animals given a list of LintErrorGroups and add them to global set of animals"""

    map = pd.DataFrame([
        ["C", "Convention", "green",   0.2, 0.3, 0.1, 0.1, 0.1],
        ["R", "Refactor", "magenta", 0.3, 0.1, 0.2, 0.3, 0.5],
        ["W", "Warning", "yellow",  0.4, 0.2, 0.4, 0.3, 0.5],
        ["E", "Error", "orange",  0.8, 0.8, 0.8, 1.0, 1.0],
        ["F", "Fatal", "red",     1.0, 4.0, 1.0, 1.0, 1.0],
    ], columns=["error_category", "shape", "color", "size", "max_health", "mass", "exertion_magnitude",
                "damage_infliction_magnitude"])
    map = map.set_index("error_category")

    animal_groups = []
    for name, group in df.groupby(["error_category"]):
        animals = []
        for i, row in group.iterrows():
            animals.append(Animal(
                error=row,
                shape=map.loc[row.error_category, "shape"],
                color=map.loc[row.error_category, "color"],
                max_health=math.ceil(map.loc[row.error_category, "max_health"] * 50) + 1,
                size=math.ceil(map.loc[row.error_category, "size"] * 40) + 15,
                mass=map.loc[row.error_category, "mass"] * 10 + 0.3,
                exertion_magnitude=map.loc[row.error_category, "exertion_magnitude"] * 100 + 10,
                damage_infliction_magnitude=map.loc[row.error_category, "damage_infliction_magnitude"],
            ))
        animal_groups.append(animals)

    pin_groups_against_each_other(animal_groups)

    return animal_groups


def organize_groups(screen, animal_groups):
    coords = evenly_spaced_coords(screen.get_width(), screen.get_height(), len(animal_groups))
    for animal_group, coords in zip(animal_groups, coords):
        organize_group(animal_group, coords)


def organize_group(animal_group, center):
    """Put the animals on the game board in a randomly spaced out way"""
    center = np.array(center)
    max_width = max([a.width for a in animal_group])
    max_height = max([a.height for a in animal_group])
    num_x = math.ceil(math.sqrt(len(animal_group)))
    num_y = math.ceil(math.sqrt(len(animal_group)))
    coords = evenly_spaced_rects(max_width, max_height, len(animal_group))
    coords = shift_rects_to_center(coords, center, num_x*max_width, num_y*max_height)
    for animal, coord in zip(animal_group, coords):
        animal.put(*coord)


def shift_rects_to_center(coords, center, width, height):
    center = np.array(center)
    new_coords = []
    for coord in coords:
        coord = np.array(coord)
        new_coords.append(coord + center - center/np.linalg.norm(center)*np.sqrt(width**2 + height**2)/2)
    return new_coords


def evenly_spaced_rects(rect_width, rect_height, num_rects):
    num_x = math.ceil(math.sqrt(num_rects))
    num_y = math.ceil(math.sqrt(num_rects))

    coords = []
    for i in range(num_x):
        for j in range(num_y):
            coords.append([rect_width*i, rect_height*j])
    return coords


def evenly_spaced_coords(x, y, np):
    """Evenly space out num_points points on the given screen"""
    npy = math.ceil(np/(1 + x/y))
    npx = math.ceil(np - npy)

    coords = []
    for i in range(npx):
        for j in range(npy):
            coords.append([x/npx/2 + i*x/npx, y/npy/2 + j*y/npy])
    return coords


def lint_and_run_game(pylint_args, fullscreen, resolution):
    """Run pylint, get the output, parse it, initialize the game and run it."""
    animal_groups = create_animals(parse(lint(pylint_args)))
    flags = pygame.FULLSCREEN if fullscreen else 0
    if not resolution and not fullscreen:
        resolution = (600, 600)
    screen = pygame.display.set_mode((0, 0) if fullscreen else resolution, flags)
    organize_groups(screen, animal_groups)
    engine = Engine(screen)
    for animal_group in animal_groups:
        engine.add_animals(*animal_group)
    engine.start()


@click.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('pylint_args', nargs=-1, type=click.UNPROCESSED)
@click.option('--fullscreen', is_flag=True)
@click.option('--resolution', nargs=2, type=int)
def lint_and_run_game_command(pylint_args, fullscreen, resolution):
    lint_and_run_game(pylint_args, fullscreen, resolution)
