from gurgle import Process, Environ, Argument, Wrapper


class Repeater(Process):
    command = ['./repeat', '{name}', '{delay}']


# keyword arguments are formatted into the command
ying = Repeater('ying', delay=1)
yang = Repeater('yang', delay=1)

# Environ objects passed in through args set env vars in the process
envion = Repeater('environ', Environ(STRING='FAST'), delay=0.1)


# Argument objects passed in through args append to the command
arg = Repeater('arg', Argument('--test'), delay=1)


# Wrapper objects passed in through args prefix the command
arg = Repeater('wrapper', Wrapper('echo'), delay=1)
