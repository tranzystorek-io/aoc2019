from utils.parse import Parser
from aoc.intcode import Machine

parser = Parser("Day 5: Sunny with a Chance of Asteroids - Part 2")
parser.parse()
with parser.input as input:
    line = input.readline()
    program = [int(el) for el in line.split(',')]

program_input = lambda: 5
program_output = lambda v: None
computer = Machine(program, program_input, program_output)
computer.run()

print(computer.last_output)
