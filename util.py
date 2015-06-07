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
    if k > n:
        return 0
    return fact(n) / (fact(k) * fact(n - k))

def kth_n_combination(items, n, k):
    if n == 0:
        return []
    total_combos = choose(len(items), n)
    if k >= total_combos:
        raise IndexError("There aren't {} {}-combinations of {}.".format(
            k+1, n, items
        ))
    combos_without_first = choose(len(items) - 1, n)
    combos_with_first = total_combos - combos_without_first
    if k < combos_with_first:
        return [items[0]] + kth_n_combination(items[1:], n - 1, k)
    else:
        return kth_n_combination(items[1:], n, k - combos_with_first)

