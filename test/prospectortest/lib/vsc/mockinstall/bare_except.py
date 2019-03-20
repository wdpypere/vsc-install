"""Test bare_except"""


def divide(a_a, b_b):
    """Function divide"""
    try:
        result = a_a / b_b
    except:
        result = None

    return result
