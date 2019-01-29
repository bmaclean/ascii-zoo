from cmd import Cmd
from threading import Thread

import click

from language.tokenizer import tokenize
from language.ast_nodes import evaluate
from game.engine import start_engine


class MyPrompt(Cmd):

    prompt = ">>> "

    def onecmd(self, string):
        try:
            evaluate(tokenize(string))
        except Exception as e:
            print(e)


@click.command()
@click.argument('input_file', type=click.File("r"))
@click.option("--repl", is_flag=True)
def run_program(input_file, repl):
    if repl:
        engine_thread = Thread(target=start_engine)
        evaluate_thread = Thread(target=run_program_then_repl, args=(input_file,))
        engine_thread.start()
        evaluate_thread.start()
    else:
        evaluate(tokenize(input_file.read()))
        start_engine()


def run_program_then_repl(input_file):
    evaluate(tokenize(input_file.read()))
    prompt = MyPrompt()
    prompt.cmdloop('Starting prompt...')


if __name__ == '__main__':
    run_program()
