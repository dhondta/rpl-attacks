# -*- coding: utf-8 -*-
import os
from cmd import Cmd
from termcolor import cprint


__all__ = [
    'Console',
]


def no_arg_command(f):
    """
    This small decorator is aimed to invalidate some badly formatted console commands, accepted by the base
     Cmd class' methods as these do not handler special characters. E.g. 'clear$erlgihsevg' makes 'clear' apply.

    :param f: the decorated console method
    """
    @wraps(f)
    def wrapper(console, line):
        if line != '':
            console.default(console.lastcmd)
        else:
            return f(console, line)
    return wrapper


class Console(Cmd, object):
    """ Simple command processor with standard commands. """
    file = None
    ruler = None
    badcmd_msg = " [!] {} command: {}"
    max_history_entries = 10

    def __init__(self, *args, **kwargs):
        super(Console, self).__init__(*args, **kwargs)
        self.__history = []
        self.pid = os.getpid()
        self.already_running = os.path.isfile(PIDFILE)
        if not self.already_running:
            try:
                with open(PIDFILE, 'w') as f:
                    f.write(str(self.pid))
            except IOError:
                pass

    def cmdloop(self, intro=None):
        try:
            import readline
            readline.set_completer_delims(' ')
            super(Console, self).cmdloop()
        except (KeyboardInterrupt, EOFError):
            print('')
            self.cmdloop()

    def precmd(self, line):
        if len(self.__history) == 0 or (not line.startswith('history') and line != self.__history[-1] and line != ''):
            if len(self.__history) >= self.max_history_entries:
                del self.__history[0]
            self.__history.append(line)
        return line

    def default(self, line):
        print(self.badcmd_msg.format(["Unknown", "Invalid"][len(line.split()) > 1], line.lstrip('_')))

    @no_arg_command
    def do_clear(self, line):
        """
    Clear the screen.
        """
        os.system("clear")
        cprint(BANNER, 'cyan', 'on_grey')
        print(self.welcome)

    @no_arg_command
    def do_EOF(self, line):
        """
    Exit the console by hitting Ctrl+D.
        """
        print('')
        return True

    @no_arg_command
    def do_exit(self, line):
        """
    Exit the console.
        """
        return True

    @no_arg_command
    def do_history(self, line):
        """
    Print the history of commands.
        """
        print('Last {} commands'.format(len(self.__history)))
        print(' > ' + '\n > '.join(self.__history))
