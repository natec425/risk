import util

def test_integer_compositions_right_number():
    'There are 2n−1 compositions of n >= 1'
    for n in range(1, 15):
        assert len([
            composition
            for k in range(1, n+1)
            for composition in util.integer_compositions(n, k)
        ]) == 2 ** (n - 1)

def test_integer_compositions_all_right_size():
    'All integer_compositions(n, k) are of length k'
    for n in range(1, 15):
        for k in range(1, n+1):
            for composition in util.integer_compositions(n, k):
                assert len(composition) == k

def test_integer_composition_of_three():
    'test integer compositions against known case of 3'
    actual = set(
        tuple(composition)
        for k in range(1, 3+1)
        for composition in util.integer_compositions(3, k)
    )
    expected = {
        (3,),
        (2, 1),
        (1, 2),
        (1, 1, 1)
    }
    assert actual == expected
