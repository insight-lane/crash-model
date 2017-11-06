from shapely.geometry import Point, LineString
from ..make_segments import extract_intersections


def test_generate_intersections():
    lines = [
        (0, LineString([
            Point(-1, -1),
            Point(0, 0)
        ])),
        (1, LineString([
            Point(1, 0),
            Point(3, 1),
        ])),
        (2, LineString([
            Point(0, 5),
            Point(3, 5),
        ])),
        (3, LineString([
            Point(2, -1),
            Point(2, 10)
        ]))
    ]
    result = extract_intersections.generate_intersections(lines)

    assert result == [
        (Point(2.0, 0.5), {'id_1': 1, 'id_2': 3}),
        (Point(2.0, 5.0), {'id_1': 2, 'id_2': 3})
    ]

