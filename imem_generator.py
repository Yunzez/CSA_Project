
def reg(register):
    val = int(register[1:] if register[0] == 'x' else register)
    return '{:05b}'.format(val)


def imm(val):
    return '{:012b}'.format(int(val))


def parse_instruction(instruction):
    # instruction = "sw x3 256(x28)"
    params = instruction.split()
    # R type
    if params[0] == "add":
        return f"0000000{reg(params[3])}{reg(params[2])}000{reg(params[1])}0110011"
    if params[0] == "sub":
        return f"0100000{reg(params[3])}{reg(params[2])}000{reg(params[1])}0110011"
    if params[0] == "xor":
        return f"0000000{reg(params[3])}{reg(params[2])}100{reg(params[1])}0110011"
    if params[0] == "or":
        return f"0000000{reg(params[3])}{reg(params[2])}110{reg(params[1])}0110011"
    if params[0] == "and":
        return f"0000000{reg(params[3])}{reg(params[2])}111{reg(params[1])}0110011"
    # I type
    if params[0] == "addi":
        return f"{imm(params[3])}{reg(params[2])}000{reg(params[1])}0010011"
    if params[0] == "xori":
        return f"{imm(params[3])}{reg(params[2])}100{reg(params[1])}0010011"
    if params[0] == "ori":
        return f"{imm(params[3])}{reg(params[2])}110{reg(params[1])}0010011"
    if params[0] == "andi":
        return f"{imm(params[3])}{reg(params[2])}111{reg(params[1])}0010011"
    if params[0] == "lw":
        im, rs1 = params[2].split('(x')
        return f"{imm(im)}{reg(rs1[:-1])}000{reg(params[1])}0000011"
    # UJ type
    # TODO: jal instruction
    # B type
    if params[0] == "beq":
        im = imm(params[3])
        return f"{im[0]}{im[2:8]}{reg(params[2])}{reg(params[1])}000{im[8:12]}{im[1]}1100011"
    if params[0] == "bne":
        im = imm(params[3])
        return f"{im[0]}{im[2:8]}{reg(params[2])}{reg(params[1])}001{im[8:12]}{im[1]}1100011"
    # S type
    if params[0] == "sw":
        im, rs1 = params[2].split('(x')
        im = imm(im)
        return f"{im[0:7]}{reg(params[1])}{reg(rs1[:-1])}010{im[7:]}0100011"
    raise NotImplementedError(f"Unknown instruction {instruction}")


"""
add x4 x5 x6
sub x7 x8 x9
addi x12 x31 897
"""

while True:
    inst = input()
    if len(inst) == 0:
        break
    inst = parse_instruction(inst)
    print(inst[0:8])
    print(inst[8:16])
    print(inst[16:24])
    print(inst[24:32])