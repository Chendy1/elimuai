from app.core.config import Settings


def test_cors_origins_are_split_and_trimmed():
    s = Settings(cors_origins="http://a.test, http://b.test ,")
    assert s.cors_origin_list == ["http://a.test", "http://b.test"]
