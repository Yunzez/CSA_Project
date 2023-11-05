class Decoder:
    def __init__(self):
        pass

    def decode(self, instruction):
        print("decoder decode: " , instruction)
        decoded_fields = {}
        opcode = int(instruction, 16) & 0x7F  # Assuming instruction is a hex string

        if int(instruction, 16) == 0:
            decoded_fields["type"] = "NOP"
            return decoded_fields

        if int(instruction, 16) == 0xFFFFFFFF:
            decoded_fields["type"] = "HALT"
            return decoded_fields
        # R-Type Instructions
        decoded_fields["opcode"] = opcode
        if opcode == 0x33:
            decoded_fields["type"] = "R"
            decoded_fields["funct3"] = (int(instruction, 16) >> 12) & 0x7
            decoded_fields["rs2"] = (int(instruction, 16) >> 20) & 0x1F
            decoded_fields["rs1"] = (int(instruction, 16) >> 15) & 0x1F
            decoded_fields["rd"] = (int(instruction, 16) >> 7) & 0x1F
            decoded_fields["funct7"] = (int(instruction, 16) >> 25) & 0x7F

        # I-Type Instructions
        elif opcode  in [0x13, 0x3]:
            decoded_fields["type"] = "I"
            decoded_fields["Imm"] = (int(instruction, 16) >> 20) & 0xFFF
            decoded_fields["rs1"] = (int(instruction, 16) >> 15) & 0x1F
            decoded_fields["rd"] = (int(instruction, 16) >> 7) & 0x1F
            decoded_fields["funct3"] = (int(instruction, 16) >> 12) & 0x7

        # S-Type Instructions
        elif opcode == 0x23:
            decoded_fields["type"] = "S"
            decoded_fields["Imm"] = ((int(instruction, 16) >> 25) & 0x7F) | ((int(instruction, 16) >> 7) & 0x1F)
            decoded_fields["rs1"] = (int(instruction, 16) >> 15) & 0x1F
            decoded_fields["rs2"] = (int(instruction, 16) >> 20) & 0x1F
            decoded_fields["funct3"] = (int(instruction, 16) >> 12) & 0x7

        # B-Type Instructions
        elif opcode == 0x63:
            decoded_fields["type"] = "B"
            instruction_int = int(instruction, 16)
            imm = int(instruction, 16)

                    # Extract the parts of the immediate value
            imm12 = (instruction_int >> 31) & 0x1
            imm105 = (instruction_int >> 25) & 0x3F
            imm41 = (instruction_int >> 8) & 0xF
            imm11 = (instruction_int >> 7) & 0x1
            
            # Reconstruct the immediate value
            imm = (imm12 << 12) | (imm11 << 11) | (imm105 << 5) | (imm41 << 1)
            print('imm:', imm)

            decoded_fields["Imm"] = imm
            decoded_fields["rs2"] = (int(instruction, 16) >> 20) & 0x1F
            decoded_fields["rs1"] = (int(instruction, 16) >> 15) & 0x1F
            decoded_fields["funct3"] = (int(instruction, 16) >> 12) & 0x7

        # J-Type Instructions
        elif opcode == 0x6F:
            decoded_fields["type"] = "J"
            decoded_fields["Imm"] = (
                ((int(instruction, 16) >> 31) & 0x1)
                | ((int(instruction, 16) >> 12) & 0xFF)
                | ((int(instruction, 16) >> 20) & 0x1)
                | ((int(instruction, 16) >> 21) & 0x3FF)
            )
            decoded_fields["rd"] = (int(instruction, 16) >> 7) & 0x1F

        else:
            print("Invalid instruction")
            return None

        for field, value in decoded_fields.items():
            if field in ['funct3', 'rs2', 'rs1', 'rd', 'funct7', 'opcode']:
                bit_size = {'funct3': 3, 'rs2': 5, 'rs1': 5, 'rd': 5, 'funct7': 7, 'opcode': 7}[field]
                decoded_fields[field] = format(value, '0{}b'.format(bit_size))
            elif field == 'Imm':
            # Determine bit size based on instruction type
                instr_type = decoded_fields["type"]
                if instr_type in ['I', 'S']:  # I-Type and S-Type have 12-bit immediates
                    bit_size = 12
                elif instr_type == 'B':  # B-Type also has 12-bit immediates
                    bit_size = 12
                elif instr_type == 'J':  # J-Type has 20-bit immediates
                    bit_size = 20
                else:
                    raise ValueError("Unknown instruction type for immediate field")
                decoded_fields[field] = format(value, '0{}b'.format(bit_size))
        return decoded_fields
