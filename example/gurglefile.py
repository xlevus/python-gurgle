#: ft=python

from gurgle import Process


class Repeater(Process):
    command = ['./repeat', '{name}', '1']


ying = Repeater('ying')
yang = Repeater('yang')