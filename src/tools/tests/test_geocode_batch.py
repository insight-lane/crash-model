from .. import geocode_batch


def mockreturn(address):
    return "Brisbane, Australia", -27.4697707, 153.0251235, 'S'


def test_initialize_city_brisbane_no_supplemental(tmpdir, monkeypatch):

    monkeypatch.setattr(geocode_batch, 'lookup_address', mockreturn)
    pass
