from .. import analyze_features


def test_get_bin():
    assert analyze_features.get_bin(0, [10, 20, 30]) == 0
    assert analyze_features.get_bin(6, [10, 20, 30]) == 1
    assert analyze_features.get_bin(16, [10, 20, 30]) == 2
    assert analyze_features.get_bin(21, [10, 20, 30]) == 3
    assert analyze_features.get_bin(33, [10, 20, 30]) == 4
