import pytest


@pytest.fixture
def save_and_clean(db):
    def _save(obj):
        obj.full_clean()
        obj.save()
        return obj

    return _save
