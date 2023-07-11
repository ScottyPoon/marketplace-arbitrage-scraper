def parse_numeric_array(string):
    """
    Parses a string representation of an array and converts it into a numeric array.

    :param string: A string containing comma-separated numeric values.
    :return: list: A list of numeric values parsed from the input string.
    Example:
        Input: '1, 2, 3.5, 4.2'
        Output: [1, 2, 3.5, 4.2]
    """
    contains_ints = False
    contains_floats = False

    my_array = string.split(",")
    my_array = [(x.strip('"')) for x in my_array]

    # Check the elements in the array to determine if it contains integers or floats
    for elem in my_array:
        if elem.isdigit():
            contains_ints = True
        elif elem.isnumeric() or (elem.count('.') == 1 and all(c.isdigit() or c == '.' for c in elem)):
            contains_floats = True

    # Convert the array elements to the appropriate numeric type
    if contains_floats:
        my_array = [float(x.strip('"')) for x in my_array]
    elif contains_ints:
        my_array = [int(x.strip('"')) for x in my_array]

    return my_array