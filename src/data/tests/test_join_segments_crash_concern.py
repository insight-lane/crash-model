from .. import join_segments_crash_concern


def test_make_schema():
    test_schema = {'X': 1, 'NAME': 'foo'}
    result_schema = join_segments_crash_concern.make_schema(
        'Point', test_schema)
    assert result_schema == {'geometry': 'Point', 'properties':
                             {'X': 'str', 'NAME': 'str'}}
