import os
from .. import geocode_batch
import shutil

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def mockreturn(address, cached, mapboxtoken):
    if address in cached:
        return cached[address]
    else:
        return ["216 Savin Hill Ave, Dorchester, MA 02125",
                42.3092288, -71.0480357, 'S']


def test_parse_addresses(tmpdir, monkeypatch):

    monkeypatch.setattr(geocode_batch, 'lookup_address', mockreturn)

    path = tmpdir.strpath + '/processed'
    os.makedirs(path)
    shutil.copyfile(
        os.path.join(TEST_FP, 'data', 'geocoded_addresses.csv'),
        os.path.join(path, 'geocoded_addresses.csv')
    )

    datadir = os.path.join(TEST_FP, 'data')
    geocode_batch.parse_addresses(
        tmpdir.strpath,
        os.path.join(datadir, 'to_geocode.csv'),
        "Boston, MA",
        'Location'
    )
    print(path)

    # check that the resulting geocoded file is correct
    with open(os.path.join(path,
                           'geocoded_addresses.csv'), 'r') as test_file:
        test_file_contents = test_file.read()
    assert test_file_contents == """Input Address,Output Address,Latitude,Longitude,Status
"21 GREYCLIFF RD Boston, MA","21 Greycliff Rd, Brighton, MA 02135, USA",42.3408948,-71.16084219999999,S
"216 SAVIN HILL AVE Boston, MA Boston, MA","216 Savin Hill Ave, Dorchester, MA 02125",42.3092288,-71.0480357,S
"""

