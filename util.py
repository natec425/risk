from math import factorial as fact
from array import array

def integer_compositions(total, n):
    """Generates all n-length partitions of total"""
    if n == 1:
        yield array('H', (total,))
    else:
        for i in range(1, total):
            for sub_partition in integer_compositions(total-i, n-1):
                sub_partition.append(i)
                yield sub_partition


def choose(n, k):
    return fact(n) * (fact(k) * fact(n - k))
