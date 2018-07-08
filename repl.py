from threading import Thread
from os import execv, system
from sys import executable, argv, exc_info
from traceback import print_exception


def capture_trace():
    exc_type, exc_value, exc_traceback = exc_info()
    print_exception(exc_type, exc_value, exc_traceback)


class Repl(Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self):
        print(
            "REPL started. Type in Python code to introspect. "
            "(^D to rebuild and restart)"
        )
        while True:
            try:
                exec(input(""))
            except Exception as e:
                if type(e) is EOFError:
                    rebuild()
                    restart()
                else:
                    capture_trace()


def rebuild():
    system("make uglify")


def restart():
    execv(executable, ["python3"] + argv)
