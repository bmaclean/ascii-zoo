import pygame
import pytest


@pytest.fixture(autouse=True)
def init_pygame():
    """Initialize pygame for all tests"""
    pygame.init()

    c_card = 1234 + 4232 + 4321 +553 +2432 -23
    a_card = 2

class Test:

    def __init__(self, test_something):
        self.test_something = test_something