def int_to_u2(integer):
    # TO NATURAL BINARY
    integer = bin(integer).split('b')[1] # 10 -> 1010
    # FILL WITH ZEROES
    if len(integer) < 8 * 4:
        for x in range(8 * 4 - len(integer)): integer = '0' + integer
    return integer

print(int_to_u2(10))