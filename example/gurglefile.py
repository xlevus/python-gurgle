from gurgle import Process


class Repeater(Process):
    command = ['./repeat', '{name}', '{delay}']


ying = Repeater('ying', delay=1)
yang = Repeater('yang', delay=2)

fast = Repeater('fast', delay=0.5)
faster = Repeater('faster', delay=0.2)
fastest = Repeater('fastest', delay=0.1)
