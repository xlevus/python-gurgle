from gurgle import Process, Environ, Argument, Wrapper


class Repeater(Process):
    command = ['./repeat', '{name}', '{delay}']


# keyword arguments are formatted into the command
Repeater('ying', delay=1)
Repeater('yang', delay=1)

# Environ objects passed in through args set env vars in the process
Repeater('environ', Environ(STRING='FAST'), delay=0.1)


# Argument objects passed in through args append to the command
Repeater('arg', Argument('--test'), delay=1)


# Wrapper objects passed in through args prefix the command
Repeater('wrapper', Wrapper('echo'), delay=1)


# You don't even need to define a process class
Process('no_class', Argument('echo', 'Hello', 'World'))
