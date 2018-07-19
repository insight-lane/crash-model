from .. import ATR_util


def test_is_readable_ATR():
    bad = '7147_NA_NA_53_CLAPP-ST_DORCHESTER_24-HOURS_SPEED_02-25-2013.XLS'
    assert not ATR_util.is_readable_ATR(bad)

    bad = '8652_NA_NA_0_SOUTHWEST-CORRIDOR_ROXBURY_48-HOURS_XXX_09-27-2016.XLS'
    assert not ATR_util.is_readable_ATR(bad)

    good = '8811_NA_NA_83_PEARL-ST_CHARLESTOWN_24-HOURS_XXX_01-11-2017.XLSX'
    assert ATR_util.is_readable_ATR(good)


def test_clean_ATR_fname():
    file = '7362_NA_NA_147_TRAIN-ST_DORCHESTER_24-HOURS_XXX_03-19-2014.XLSX'
    assert ATR_util.clean_ATR_fname(file) == '147 TRAIN ST Boston, MA'
