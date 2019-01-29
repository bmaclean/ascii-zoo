import re
import pytest


class InvalidSyntax(Exception):
    """Using this instead of the builtin SyntaxError because the builtin version has some additional attributes such as
    filename and line number that aren't easily accessible for us."""

    def __init__(self, message, token=None): 
        if token:
            message = "Line number {}: {}".format(token.line_number, message)
        super().__init__(message)


class Chars:

    def __init__(self, chars):
        self.chars = chars
        self.position = 0
        self.line = 1

    def has_more_chars(self):
        return self.position < len(self.chars)

    @property
    def current(self):
        return self.chars[self.position]

    def step_back(self):
        self.position -= 1
        if self.current is "\n":
            self.line -= 1

    def view_all_following_chars(self):
        return self.chars[self.position:]

    def __iter__(self):
        return self

    def __next__(self):
        if not self.has_more_chars():
            raise StopIteration()
        char = self.chars[self.position]
        if char is "\n":
            self.line += 1
        self.position += 1
        return char

    def __repr__(self):
        return super().__repr__() + "\n" + self.chars[self.position:]


class Token:

    separator = "separator"
    symbol = "symbol"
    number = "number"
    shape = "shape"
    keyword = "keyword"

    def __init__(self, value, token_type, line_number=None):
        self.value = value
        self.token_type = token_type
        self.line_number = line_number

    def __repr__(self):
        return "<Token object '{} {}'>".format(self.token_type, self.value)

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, obj):
        """Check if the value of the token is equal to the value of the other token, or simply the string if a string
        is given."""
        if obj is self:
            return True
        if isinstance(obj, Token):
            return obj.value == self.value
        elif isinstance(obj, str):
            return self.value == obj
        else:
            return False


class Tokens:

    def __init__(self):
        self.tokens = []
        self.position = 0

    def append(self, token):
        self.tokens.append(token)

    def __repr__(self):
        return str(self.tokens)

    def __iter__(self):
        return self

    def __next__(self):
        token = self.get()
        if token is None:
            raise StopIteration()
        self.position += 1
        return token

    def get(self, relative_position=None):
        """Add the given relative position to the current position and return the corresponding token."""
        try:
            index = self.position + relative_position if relative_position else self.position
            return self.tokens[index]
        except IndexError:
            return None

    def step(self):
        self.position += 1

    def get_and_step(self):
        token = self.get()
        self.position += 1
        return token

    def get_check_and_step(self, regex):
        token = self.get()
        if not re.match(regex, token.value):
            raise InvalidSyntax("Expected token matching pattern '{}', instead got '{}'".format(regex, token.value))
        return self.get_and_step()

    def get_check_type_and_step(self, expected_types):
        token = self.get()
        if token.token_type in expected_types:
            return self.get_and_step()
        else:
            raise InvalidSyntax("Expected token of type '{}', instead got type '{}' with value '{}'".format(
                expected_type, token.token_type, token.value
            ))

    def get_symbol_and_step(self):
        return self.get_check_type_and_step([Token.symbol])

    def get_number_and_step(self):
        return self.get_check_type_and_step([Token.number])

    def stop_after(self, regex):
        while self.get() is not None:
            if re.match(regex, self.get().value):
                # Step because we want to stop *after* the matching regex is reached, as implied by the method name
                self.step()
                break
            yield self.get_and_step()
        else:
            raise InvalidSyntax("Hit end of input before reaching the expected '{}' token".format(self.get().value))


def tokenize(string):
    """
    Inspired by Andy Balaam, who wrote a similar lexer in python for his own DSL named Cell.
        https://www.youtube.com/watch?v=TG0qRDrUPpA
    """
    chars = Chars(string)
    tokens = Tokens()
    for char in chars:
        if char in " \n":
            # Ignore spaces and newlines; they are not important in our DSL
            continue
        elif char in "[]{}(),":
            tokens.append(Token(char, Token.separator, chars.line))
        elif ShapeTokenizer.matches(chars):
            tokens.append(ShapeTokenizer(chars).token)
        elif re.match("[0-9]", char):
            tokens.append(Token(int(read(char, chars, "[0-9]")), Token.number, chars.line))
        elif re.match("[_a-zA-Z]", char):
            tokens.append(Token(read(char, chars, "[_a-zA-Z0-9]"), Token.symbol, chars.line))
        else:
            raise InvalidSyntax("Unexpected character '{}' at line {}".format(char, chars.line))
    return tokens


class ShapeTokenizer:

    def __init__(self, chars):
        self.chars = chars

    @classmethod
    def matches(cls, chars):
        return re.match("shape[ \n]*{", chars.chars[chars.position-1:])

    @property
    def token(self):
        for char in self.chars:
            if char is "{":
                break
        shape = ""
        for char in self.chars:
            if char is "}":
                break
            shape += char
        else:
            raise InvalidSyntax("Reached end of program before encountering a closing brace '}' for this shape block.")
        return Token(shape.strip(), Token.shape, self.chars.line)


def read(first_char, chars, allowed_regex):
    return_value = first_char
    for char in chars:
        if not re.match(allowed_regex, char):
            chars.step_back()
            break
        return_value += char
    return return_value
