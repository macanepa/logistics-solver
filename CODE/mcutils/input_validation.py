def input_validation(user_input, return_type, valid_options):
    if(return_type == int):
        if(not user_input.isnumeric()):
            return False
        user_input = int(user_input)

    # /Contains/ validation
    if(len(valid_options)!=0):

        operators_list = list(filter(lambda x: str(x).startswith(('<','>','==')), valid_options))
        contains_list = list(set(valid_options)-set(operators_list))

        # /Complex/ validation
        # Special operators
        for operator in operators_list:
            if('<=' in operator):
                value = operator.replace('<=', '')
                if (return_type == int):
                    if(not user_input <= int(value)):
                       return False
                elif (return_type == str):
                    if(not len(user_input) <= int(value)):
                       return False

            elif ('>=' in operator):
                value = operator.replace('>=', '')
                if (return_type == int):
                    if (not user_input >= int(value)):
                        return False
                elif (return_type == str):
                    if(not len(user_input) >= int(value)):
                       return False

            elif ('<' in operator):
                value = operator.replace('<', '')
                if (return_type == int):
                    if (not user_input < int(value)):
                        return False
                elif (return_type == str):
                    if(not len(user_input) < int(value)):
                       return False

            elif ('>' in operator):
                value = operator.replace('>', '')
                if (return_type == int):
                    if (not user_input > int(value)):
                        return False
                elif (return_type == str):
                    if (not len(user_input) > int(value)):
                        return False

            elif ('==' in operator):
                value = operator.replace('==', '')
                if (return_type == int):
                    if (not user_input == int(value)):
                        return False
                elif (return_type == str):
                    if (not len(user_input) == int(value)):
                        return False

        # if contains in valid options
        if(len(contains_list) > 0):
            if(not user_input in contains_list):
                return False

    return True