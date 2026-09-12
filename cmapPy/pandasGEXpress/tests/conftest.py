import pytest
import cmapPy.pandasGEXpress.mini_gctoo_for_testing as mini_gctoo_for_testing


@pytest.fixture
def mini_gctoo():
    """A small representative GCToo instance, with -666 converted to NaN."""
    return mini_gctoo_for_testing.make()


@pytest.fixture
def mini_gctoo_unconverted():
    """A small representative GCToo instance, with -666 left unconverted."""
    return mini_gctoo_for_testing.make(convert_neg_666=False)
