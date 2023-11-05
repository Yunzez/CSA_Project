class ALU:
    def __init__(self):
        self.ALU_CONTROL_CODES = {
            '0010': self.add,
            '0110': self.sub,
            '0000': self.and_op,
            '0001': self.or_op,
            '0111': self.xor_op,
        }

    def add(self, a, b):
        print("ALU add: ", a, b)
        return a + b

    def sub(self, a, b):
        print("ALU sub: ", a, b)
        return a - b

    def and_op(self, a, b):
        return a & b

    def or_op(self, a, b):
        return a | b

    def xor_op(self, a, b):
        return a ^ b

    def operate(self, control_code, a, b):
        operation = self.ALU_CONTROL_CODES.get(control_code)
        if operation:
            return operation(a, b)
        else:
            raise ValueError(f"Invalid ALU control code: {control_code}")