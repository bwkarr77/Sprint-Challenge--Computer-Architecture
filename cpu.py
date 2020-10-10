"""CPU functionality."""
# to run in terminal, type: py ls8.py sctest.ls8

import sys

"""""GLOBAL VARIABLES"""""
"""COMMAND OPERATORS:"""
HALT    = 0b00000001    # 1     = HALT

PUSH    = 0b01000101    # 69    = PUSH ONTO STACK
POP     = 0b01000110    # 70    = POP OFF THE STACK
PRN     = 0b01000111    # 71    = PRINT
PRA     = 0b01001000    # 72    =


LOAD    = 0b10000010    # 130   = LOAD IMMEDIATE
LD      = 0b10000011    # 131   = LOADS INTO REGISTER_A THE VALUE IN REGISTER_B
ST      = 0b10000100    # 131   = LOADS INTO REGISTER_B THE VALUE IN REGISTER_A

"""PC MUTATORS:"""
RET     = 0b00010001    # 17    = RET

CALL    = 0b01010000    # 80    = CALL

INT     = 0b01010010    # 82    = ISSUE THE INTERRUPT NUMBER STORED IN REGISTER
IRET    = 0b00010011    # 83    = RETURN FROM AN INTERRUPT HANDLER
JMP     = 0b01010100    # 84    = JUMP
JEQ     = 0b01010101    # 85    = VALUE IF EQUAL FLAS IS TRUE
JNE     = 0b01010110    # 86    = VALUE IF GREATER_THAN FLAG OR EQUAL FLAG IS TRUE
JGT     = 0b01010111    # 87    = VALUE IF GREATER_THAN FLAG IS TRUE
JLT     = 0b01011000    # 88    = VALUE IF LESS_THAN FLAG
JLE     = 0b01011001    # 89    = VALUE IF LESS-THEN FLAG OR EQUAL FLAG IS TRUE

"""ALU OPERATORS:"""
"math:"
ADD     = 0b10100000    # 160   = ADD NUMBERS TOGETHER
SUB     = 0b10100001    # 161   = SUBTRACT 2 NUMBER
MULT    = 0b10100010    # 162   = MULTIPLY NUMBERS TOGETHER
DIV     = 0b10100011    # 163   = DIVIDE 2 NUMBERS
MOD     = 0b10100100    # 164   = DIVIDE 2 NUMBERS, RETURN REMAINDER
INC     = 0b01100101    # 165   = INCREMENT VALUE IN REGISTER BY 1
DEC     = 0b01100110    # 166   = DECREMENT VALUE IN REGISTER BY 1
CMP     = 0b10100111    # 167   = COMPARE THE VALUES IN MULTIPLE REGISTERS

"logic:"
NOT     = 0b01101001    # 105

AND     = 0b10101000    # 168

OR      = 0b10101010    # 170
XOR     = 0b10101011    # 171
SHL     = 0b10101100    # 172
SHR     = 0b10101101    # 173

"""FLAGS (FL), bits = 00000LGE"""
FL_E = 0b001
FL_G = 0b010
FL_L = 0b100

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256  # 256 bytes of RAM/memory
        self.registers = [0] * 8  # registers 0:7 are saved for quick access
        self.registers[7] = 0xF4  # 244
        self.pc = 0  # program counter/pointer
        self.flag_E = 0
        self.flag_G = 0
        self.flag_L = 0
        self.running = False

        # ____Branch Tables____
        self.branchtable = {
            LOAD: self.ldi,
            PRN: self.prn,
            HALT: self.hlt,
            # MULT: self.mul,
            PUSH: self.push,
            POP: self.pop,
            # ADD: self.add,
            CALL: self.call,
            RET: self.ret,
            # CMP: self.cmp,
            JMP: self.jmp,
            JNE: self.jne,
            JEQ: self.jeq
        }

    def load(self):
        """Load a program into memory."""
        if len(sys.argv) != 2:
            print("Usage: py ls8.py <filename.py>")
            sys.exit(1)

        address = 0
        try:
            with open(sys.argv[1]) as f:
                # print(sys.argv)  # sys.argv = ['ls8.py', 'examples/<filename>']
                for line in f:
                    # separate each line into the binary code from the file
                    code_number = line.split('#')[0].strip()   # ex: 100000010
                    code_number = line[:line.find('#')]

                    if code_number == "":
                        continue  # skips to the next iteration

                    try:
                        code_number = int(code_number, 2)

                    except ValueError:
                        print(f"Invalid Number: {code_number}")
                        sys.exit(1)

                    self.ram_write(address, code_number)
                    address += 1

        except FileNotFoundError:
            print(f"{sys.argv[1]} file not found")
            sys.exit(2)


    def alu(self, op, op_a, op_b):
        """ALU operations."""

        # MATH OPERATOR:
        if op == ADD:
            self.registers[op_a] += self.registers[op_b]
        elif op == MULT:
            self.registers[op_a] *= self.registers[op_b]
        elif op == SUB:
            self.registers[op_a] -= self.registers[op_b]
        elif op == DIV:
            try:
                self.registers[op_a] /= self.registers[op_b]
            except ZeroDivisionError:
                print('You cannot divide by zero')
                sys.exit(1)
        elif op == MOD:
            try:
                self.registers[op_a] = self.registers[op_a] % self.registers[op_b]
            except ZeroDivisionError:
                print('You cannot divide by zero')
                sys.exit(1)
        elif op == INC:
            self.registers[op_a] -= self.registers[op_b]
        elif op == DEC:
            self.registers[op_a] -= self.registers[op_b]

        # COMPARING REGISTERS:
        elif op == CMP:
            reg_a = self.registers[op_a]
            reg_b = self.registers[op_b]
            self.flag_E = 0
            self.flag_G = 0
            self.flag_L = 0
            if reg_a < reg_b:
                self.flag_L = 1
            elif reg_a > reg_b:
                self.flag_G = 1
            elif reg_a == reg_b:
                self.flag_E = 1

        # LOGICAL OPERATORS:
        elif op == AND:
            self.registers[op_a] = (self.registers[op_a] & self.registers[op_b])
        elif op == OR:
            self.registers[op_a] = (self.registers[op_a] | self.registers[op_b])
        elif op == XOR:
            self.registers[op_a] = (self.registers[op_a] ^ self.registers[op_b])
        elif op == NOT:
            self.registers[op_a] = (self.registers[op_a] != self.registers[op_b])
        elif op == SHL:
            # shift the value in registerA by bits in registerB, left:
            self.registers[op_a] = (self.registers[op_a] << self.registers[op_b])
        elif op == AND:
            # shift the value in registerA by bits in registerB, to the right:
            self.registers[op_a] = (self.registers[op_a] >> self.registers[op_b])

        else:
            raise Exception(f"Unsupported ALU operation: {op}")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.registers[i], end='')

        print()

    def ram_read(self, MAR):
        # MAR (Memory Address Register) = address this is read/written to
        # print('ram_read: ', self.ram[MAR])
        # returns the data that is stored inside RAM at the MAR (memory access) location (typically pc)
        return self.ram[MAR]

    def ram_write(self, MAR, MDR):
        # MAR (Memory Address Register) = address this is read/written to
        # MDR (Memory Data Register) = data to read/write
        self.ram[MAR] = MDR

    def run(self):
        """Run the CPU."""
        self.running = True

        while self.running:
            # Instruction Register (IR) is the COMMAND/action we are doing
            # operand_a is the register index, operand_b is the value
            IR = self.ram_read(self.pc)  # should be the "command"/instructions
            operand_a = self.ram_read(self.pc + 1)
            operand_b = self.ram_read(self.pc + 2)

            # masking
            sets_pc_directly = ((IR >> 4) & 0b0001) == 1
            num_args = IR >> 6
            is_alu_op = ((IR >> 5) & 0b001) == 1

            # BranchTable implementation
            if is_alu_op:
                self.alu(IR, operand_a, operand_b)
            else:
                try:
                    self.branchtable[IR](operand_a, operand_b)
                except KeyError:
                    print(f'KeyError at {self.registers[IR]}')
                    sys.exit(1)

            # skip this IF setting pc directly:
            if not sets_pc_directly:
                # print('change pc: ', self.pc, num_args)
                self.pc += 1 + num_args

    # Branch Table Commands
    def ld(self, operand_a, operand_b):
        self.registers[operand_a] = self.registers[operand_b]

    def ldi(self, operand_a, operand_b):   # LOAD
        # LOAD the value into the register location
        self.registers[operand_a] = operand_b

    def prn(self, operand_a, operand_b):  # PRINT values at register
        # PRINT the value at the given register location
        print(self.registers[operand_a])

    def hlt(self, operand_a, operand_b):
        # Exit Loop
        self.running = False
        # print('ram: ', self.ram)

    def push(self, operand_a, operand_b):
        # **SP = Stack Pointer, similar to self.pc but with different function
        # 1. Decrement the 'SP'
        self.registers[7] -= 1  # decrement the 'SP' by 1 (change location SP is pointing to by -1)

        # 2. Copy the value in the given register
        value = self.registers[operand_a]

        # 3. Save the value into the location SP (to be referenced in POP)
        SP = self.registers[7]
        self.ram_write(SP, value)

    def pop(self, operand_a, operand_b):
        # 1. Copy the value from the address pointed to by "SP" to given register
        # (value should be saved into register during the push function)
        SP = self.registers[7]
        value = self.ram_read(SP)

        # place value into the register idx
        self.registers[operand_a] = value

        self.registers[7] += 1

    def call(self, operand_a, operand_b):
        # # save the register/return address to "return" back to after CALL
        # save the return address
        return_address = self.pc + 2

        # push command address after CALL onto stack
        self.registers[7] -= 1
        # get SP location, and store return_address at SP address:
        SP = self.registers[7]
        self.ram_write(SP, return_address)

        # look into register to find address
        subroutine_address = self.registers[operand_a]

        self.pc = subroutine_address

    def ret(self, operand_a, operand_b):
        SP = self.registers[7]
        return_address = self.ram_read(SP)

        self.pc = return_address

        self.registers[7] += 1

    def jmp(self, operand_a, operand_b):
        self.pc = self.registers[operand_a]

    def jeq(self, operand_a, operand_b):
        if self.flag_E == 1:
            self.pc = self.registers[operand_a]
        else:
            self.pc += 2

    def jne(self, operand_a, operand_b):
        if self.flag_E == 0:
            self.pc = self.registers[operand_a]
        else:
            self.pc += 2

    def jgt(self, operand_a, operand_b):
        # if greater-than flag is true: jump
        pass

    def jlt(self, operand_a, operand_b):
        # if less-than flag is true: jump
        pass

    def jle(self, operand_a, operand_b):
        # if less-than flag, or equal flag is true: jump
        pass

    def jge(self, operand_a, operand_b):
        # if greater-than flag, or equal flag is true: jump
        pass