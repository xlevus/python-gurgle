#: ft=python

from gurgle import Process


class Repeater(Process):
    command = ['./repeat', '{name}', '{delay}']


ying = Repeater('ying', delay=1)
yang = Repeater('yang', delay=2)
