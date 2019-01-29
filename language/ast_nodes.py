"""
This module handles creation of an AST from the tokenized program and execution of the resulting AST.
"""

from contextlib import contextmanager

from game.animal import AnimalType, Animal
from language.tokenizer import Token, InvalidSyntax


class SymbolMap(dict):
    """
    Used to keep track of variable/symbols that the user has defined using our DSL

    Example:
        animals = SymbolMap()
        animal_types = SymbolMap()
    """

    def get(self, symbol_name):
        try:
            return self[symbol_name]
        except KeyError:
            raise NameError("'{}' hasn't been defined yet".format(symbol_name))


class Animals(SymbolMap):

    @property
    def animal_names(self):
        """Return the names of all the animals that have been created so far."""
        return self.keys()

    @property
    def active_animals(self):
        """Return all the animals that have a defined coordinate on the game board"""
        for animal in list(self.values()):
            if animal.x is not None and animal.y is not None:
                yield animal

    def __iter__(self):
        return self.values().__iter__()

    def remove(self, animal):
        for key, other_animal in list(self.items()):
            if other_animal == animal:
                self.pop(key)


animal_types = SymbolMap()
animals = Animals()


def evaluate(tokens):
    """Evalute the given tokens"""
    define = "define"
    create = "create"
    put = "put"

    token = tokens.get()
    while tokens.get() is not None:
        if token == define:
            DefineNode.parse(tokens).evaluate()
        elif token == create:
            CreateNode.parse(tokens).evaluate()
        elif token == put:
            PutNode.parse(tokens).evaluate()
        elif token in animals.animal_names:
            OverrideNode.parse(tokens).evaluate()
        else:
            raise InvalidSyntax("Unexpected input at '{}'".format(token.value), token)
        token = tokens.get()


@contextmanager
def curly_braces(tokens):
    tokens.get_check_and_step("{")
    yield
    tokens.get_check_and_step("}")


class OverrideNode:

    speed = "speed"
    eats = "eats"
    color = "color"
    shape = "shape"
    valid_attributes = [speed, eats, color, shape]

    @classmethod
    def parse(cls, tokens):
        self = cls()
        self.animal_name = tokens.get_symbol_and_step().value
        self.attribute_node = AttributeNode.parse(tokens)
        return self

    def evaluate(self):
        setattr(
            animals.get(self.animal_name),
            self.attribute_node.attribute_name,
            self.attribute_node.attribute_value,
        )


class DefineNode:
    """
    Represents the define statement.

    Here's an example of what a define node would like in our DSL:
        
        define Frog {
            shape { >.> }
            color { black }
            speed { fast }
            eats { Snake, Bug }
        }
    """

    def __init__(self):
        self.attribute_nodes = []

    @classmethod
    def parse(cls, tokens):
        self = cls()
        define_token = tokens.get_check_and_step("define")
        self.animal_type_name = tokens.get_symbol_and_step().value
        tokens.get_check_and_step("{")
        while tokens.get() is not None:
            if tokens.get() == "}":
                tokens.step()
                break
            self.attribute_nodes.append(AttributeNode.parse(tokens))
        else:
            raise InvalidSyntax(
                "Hit end of input before finding a closing brace '}' for the define block.", define_token
            )
        return self
                
    def evaluate(self):
        """Create an animal type object using Brendan's API"""
        kwargs = {}
        for attribute_node in self.attribute_nodes:
            kwargs[attribute_node.attribute_name] = attribute_node.attribute_value
        animal_types[self.animal_type_name] = AnimalType(**kwargs)


class AttributeNode:

    speed = "speed"
    eats = "eats"
    color = "color"
    shape = "shape"
    valid_attributes = [speed, eats, color, shape]

    @classmethod
    def parse(cls, tokens):
        self = cls()
        token = tokens.get_and_step()

        if token.token_type == Token.shape:
            # Shape is a special case and has it's own type of token
            self.attribute_name = self.shape
            self.attribute_value = token.value
        elif token.value in self.valid_attributes:
            self.attribute_name = token.value
            if token == self.speed:
                with curly_braces(tokens):
                    self.attribute_value = tokens.get_check_type_and_step([Token.symbol, Token.number])
            elif token == self.color:
                with curly_braces(tokens):
                    self.attribute_value = tokens.get_symbol_and_step().value
            elif token == self.eats:
                animal_types_to_eat = []
                tokens.get_check_and_step("{")
                for token in tokens.stop_after("}"):
                    if token == ",":
                        continue
                    animal_types_to_eat.append(animal_types.get(token.value))
                self.attribute_value = animal_types_to_eat
        else:
            raise InvalidSyntax(
                "Expected one of {}, instead got '{}'".format(self.valid_attributes, token.value), token
            )
        return self


class CreateNode:
    """
    Example:
        Suppose the user writes this program:

            >>> create Frog named frog1

        then the animal type is "Frog" and the variable name is "frog1". If "Frog isn't defined in the symbol table
        then we should raise a RuntimeError or something"
    """

    @classmethod
    def parse(cls, tokens):
        self = cls()
        tokens.get_check_and_step("create")
        self.animal_type_name = tokens.get_symbol_and_step().value
        tokens.get_check_and_step("named")
        self.animal_name = tokens.get_symbol_and_step().value
        return self

    def evaluate(self):
        animal_type = animal_types.get(self.animal_type_name)
        animals[self.animal_name] = Animal(animal_type)


class PutNode:
    """
    Attributes:
        {x,y}_relative_position: A number in [1,100] that defines the position of the x and y coordinate as a
            percentage of the max coordinate value of the resolution. For example, if I would like to put a frog at the
            bottom right, I would write. Assuming a (x,y) = (0,0) in the top left.
                >>> put froggy at {100,100}

    Example:
        User could write

            >>> put froggy at {1,2}
    """

    @classmethod
    def parse(cls, tokens):
        self = cls()
        tokens.get_check_and_step("put")
        self.animal_name = tokens.get_symbol_and_step()
        tokens.get_check_and_step("at")
        tokens.get_check_and_step("{")
        self.x_relative_position = self.get_relative_position(tokens)
        # This comma separates the x and y relative positions
        tokens.get_check_and_step(",")
        self.y_relative_position = self.get_relative_position(tokens)
        tokens.get_check_and_step("}")
        return self

    def get_relative_position(self, tokens):
        token = tokens.get_number_and_step()
        if not 0 <= token.value <= 100:
            raise InvalidSyntax("Relative position must be between 0-100. Instead got {}.".format(token.value), token)
        return token.value

    def evaluate(self):
        animal = animals.get(self.animal_name)
        animal.put(self.x_relative_position, self.y_relative_position)
