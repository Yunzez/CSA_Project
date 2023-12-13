class ForwardingUnit:
    def __init__(self):
        pass

    def check_ex_id_forwarding(self, id_stage_state, ex_stage_state):
        """
        Check for and perform EX-to-ID forwarding.
        :param id_stage_state: The state of the ID stage.
        :param ex_stage_state: The state of the EX stage.
        :return: Forwarded values for Rs and Rt if forwarding is needed, else None.
        """
        forwarded_values = {}
        if ex_stage_state["wrt_enable"]:
            if "Rs" in id_stage_state and id_stage_state["Rs"] == ex_stage_state["Wrt_reg_addr"]:
                forwarded_values["Read_data1"] = ex_stage_state["ALUresult"]
            if "Rt" in id_stage_state and id_stage_state["Rt"] == ex_stage_state["Wrt_reg_addr"]:
                forwarded_values["Read_data2"] = ex_stage_state["ALUresult"]
        return forwarded_values if forwarded_values else None

    def check_mem_id_forwarding(self, id_stage_state, mem_stage_state, wb_next_stage_state, forwardType):
        """
        Check for and perform MEM-to-ID forwarding.
        :param id_stage_state: The state of the ID stage.
        :param mem_stage_state: The state of the MEM stage.
        :return: Forwarded values for Rs and Rt if forwarding is needed, else None.
        """
        forwarded_values = {}
        if mem_stage_state["wrt_enable"]:
            print("mem foward check type", forwardType)
            if "rs1" in id_stage_state and id_stage_state["rs1"] == mem_stage_state["Wrt_reg_addr"]:
                if forwardType == "wrt":
                    forwarded_values["Read_data1"] = wb_next_stage_state["Wrt_data"]
                elif forwardType == "str":
                    print("store operation, no forwarding")
                elif forwardType == "alu":
                     forwarded_values["Read_data1"] = mem_stage_state["ALUresult"] 
                # Assume Data holds the result
            if "rs2" in id_stage_state and id_stage_state["rs2"] == mem_stage_state["Wrt_reg_addr"]:
                if forwardType == "wrt":
                    forwarded_values["Read_data2"] = wb_next_stage_state["Wrt_data"]
                elif forwardType == "str":
                    print("store operation, no forwarding")
                elif forwardType == "alu":
                     forwarded_values["Read_data2"] = mem_stage_state["ALUresult"]

            if "Rs" in id_stage_state and id_stage_state["Rs"] == mem_stage_state["Wrt_reg_addr"]:
                if forwardType == "wrt":
                    forwarded_values["Read_data1"] = wb_next_stage_state["Wrt_data"]
                elif forwardType == "str":
                    print("store operation, no forwarding")
                elif forwardType == "alu":
                     forwarded_values["Read_data1"] = mem_stage_state["ALUresult"] 
            
            if "Rt" in id_stage_state and id_stage_state["Rt"] == mem_stage_state["Wrt_reg_addr"]:
                if forwardType == "wrt":
                    forwarded_values["Read_data2"] = wb_next_stage_state["Wrt_data"]
                elif forwardType == "str":
                    print("store operation, no forwarding")
                elif forwardType == "alu":
                     forwarded_values["Read_data2"] = mem_stage_state["ALUresult"]
        return forwarded_values if forwarded_values else None
