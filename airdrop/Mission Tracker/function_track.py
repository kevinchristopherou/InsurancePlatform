def get_insure(arg):
    if len(arg)<4:  
        return False
    return arg[0][0] == 'uint256' and arg[0][1] == '_amount' and arg[1][0] == 'uint256' and arg[1][1] == '_maxCost' and arg[2][0] == 'uint256' and arg[2][1] == '_span' and arg[3][0] == 'bytes32' and arg[3][1] == '_target'

def get_deposit_template(arg):
    if len(arg)<1:  
        return False
    return arg[0][0] == 'uint256' and arg[0][1] == '_amount'

def get_deposit_gauge(arg):
    if len(arg)<2:  
        return False
    return arg[0][0] == 'uint256' and arg[0][1] == '_value' and arg[1][0] == 'address' and arg[1][1] == 'addr'

def get_create_lock(arg):
    if len(arg)<2:  
        return False
    return arg[0][0] == 'uint256' and arg[0][1] == '_value' and arg[1][0] == 'uint256' and arg[1][1] == '_unlock_time'

def get_apply_cover(arg):
    if len(arg)<6:  
        return False
    return arg[0][0] == 'uint256' and arg[0][1] == '_pending' and arg[1][0] == 'uint256' and arg[1][1] == '_payoutNumerator' and arg[2][0] == 'uint256' and arg[2][1] == '_payoutDenominator' and arg[3][0] == 'uint256' and arg[3][1] == '_incidentTimestamp' and arg[4][0] == 'bytes32[]' and arg[4][1] == '_targets' and arg[5][0] == 'string' and arg[5][1] == '_memo'
    