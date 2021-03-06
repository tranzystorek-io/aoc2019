from utils.parse import Parser
from aoc.intcode import Machine
from copy import deepcopy

parser = Parser("Day 9: Sensor Boost - Part 2")
parser.parse()
with parser.input as input:
    line = input.readline()
    program = [int(el) for el in line.split(',')]

program_input = lambda: 2
computer = Machine(deepcopy(program), program_input)
computer.run()
