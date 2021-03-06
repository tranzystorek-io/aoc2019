import operator
from functools import partial


def _reverse_digits(n):
    current = n
    while True:
        yield current % 10
        current //= 10


class Args:
    def __init__(self, args):
        self.__dict__.update(args)

    def __len__(self):
        return len(self.__dict__)


class Machine:
    def __init__(self, program, input_func, output_func=lambda v: print(v)):
        self.__memory = program
        self.__output = 0
        self.__in_f = input_func
        self.__out_f = output_func
        self.__running = False
        self.__halted = False
        self.__pc = 0
        self.__jump_flag = False
        self.__jump_addr = 0
        self.__relative_base = 0
        self.__breakpoints = []
        self.__break_on_output_flag = False
        self.__output_interrupted = False

        self.__opcode_map = {
            1: self.__arithmetic_op(operator.add),
            2: self.__arithmetic_op(operator.mul),
            3: self.__in,
            4: self.__out,
            5: self.__jump_op(partial(operator.ne, 0)),
            6: self.__jump_op(partial(operator.eq, 0)),
            7: self.__comp_op(operator.lt),
            8: self.__comp_op(operator.eq),
            9: self.__rel_base_op,
            99: self.__terminate
        }

    @property
    def last_output(self):
        return self.__output

    @property
    def halted(self):
        return self.__halted

    @property
    def breakpoints(self):
        return self.__breakpoints

    @breakpoints.setter
    def breakpoints(self, values):
        self.__breakpoints = values

    @property
    def break_on_output(self):
        return self.__break_on_output_flag

    @break_on_output.setter
    def break_on_output(self, value):
        self.__break_on_output_flag = value

    def run(self):
        while not self.__halted:
            self.__run()

    def start_or_resume(self):
        if not self.__halted:
            self.__run()

    def step(self):
        if not self.__halted:
            self.__step()

    def read(self, pos):
        return self.__memory[pos]

    def __run(self):
        self.__running = True
        while True:
            if self.__pc in self.__breakpoints:
                self.__running = False
                break

            self.__step()

            if self.__output_interrupted:
                self.__running = False
                self.__output_interrupted = False
            if not self.__running:
                break

    def __step(self):
        opcode, args = self.__parse_instruction()
        self.__exec(opcode, args)

        if self.__jump_flag:
            self.__pc = self.__jump_addr
            self.__jump_flag = False
        else:
            self.__pc += len(args) + 1

    def __exec(self, opcode, args):
        self.__opcode_map[opcode](args)

    def __parse_instruction(self):
        opcode = self.__memory[self.__pc]
        op = opcode % 100
        names = []
        if op == 1 or op == 2 or op == 7 or op == 8:
            names = ['a', 'b', 'dst']
        elif op == 5 or op == 6:
            names = ['cond', 'addr']
        elif op == 3 or op == 4 or op == 9:
            names = ['addr']

        return op, self.__get__args(names, opcode // 100)

    def __get__args(self, names, mode_code):
        modes = _reverse_digits(mode_code)
        arg_begin = self.__pc + 1
        args = {name: (mode, value) for name, mode, value in zip(names, modes, self.__memory[arg_begin:])}
        return Args(args)

    def __terminate(self, args):
        self.__running = False
        self.__halted = True

    def __arithmetic_op(self, op):
        def ret_op(args):
            m_a, v_a = args.a
            a = self.__get_value_from_mode(m_a, v_a)
            m_b, v_b = args.b
            b = self.__get_value_from_mode(m_b, v_b)
            result = op(a, b)
            m_dst, v_dst = args.dst
            dst = self.__get__address_from_mode(m_dst, v_dst)
            self.__mem_access_resize(dst, result)
        return ret_op

    def __comp_op(self, op):
        def ret_op(args):
            m_a, v_a = args.a
            a = self.__get_value_from_mode(m_a, v_a)
            m_b, v_b = args.b
            b = self.__get_value_from_mode(m_b, v_b)
            m_dst, v_dst = args.dst
            dst = self.__get__address_from_mode(m_dst, v_dst)
            self.__mem_access_resize(dst, 1 if op(a, b) else 0)
        return ret_op

    def __jump_op(self, pred):
        def ret_op(args):
            m_cond, v_cond = args.cond
            cond = self.__get_value_from_mode(m_cond, v_cond)
            m_addr, v_addr = args.addr
            self.__jump_addr = self.__get_value_from_mode(m_addr, v_addr)
            self.__jump_flag = pred(cond)
        return ret_op

    def __rel_base_op(self, args):
        m, v = args.addr
        adjust_value = self.__get_value_from_mode(m, v)
        self.__relative_base += adjust_value

    def __in(self, args):
        m, v = args.addr
        addr = self.__get__address_from_mode(m, v)
        self.__mem_access_resize(addr, self.__in_f())

    def __out(self, args):
        m, v = args.addr
        output_value = self.__get_value_from_mode(m, v)
        self.__out_f(output_value)
        self.__output = output_value

        if self.__break_on_output_flag:
            self.__output_interrupted = True

    def __get__address_from_mode(self, mode, v):
        if mode == 0:
            return v

        return self.__relative_base + v

    def __get_value_from_mode(self, mode, v):
        if mode == 0:
            return self.__mem_access_resize(v)

        if mode == 1:
            return v

        rel_addr = self.__relative_base + v
        return self.__mem_access_resize(rel_addr)

    def __mem_access_resize(self, pos, value=None):
        l = len(self.__memory)
        if pos >= l:
            self.__memory.extend(0 for _ in range(l, pos + 1))

        if value is None:
            return self.__memory[pos]

        self.__memory[pos] = value
