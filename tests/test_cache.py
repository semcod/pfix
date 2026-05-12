from pfix.cache import FixCache


class TestCache:
    def test_cache_initialization(self, tmp_path) -> None:
        cache_dir = tmp_path / '.pfix_cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache = FixCache(cache_dir=cache_dir)
        stats = cache.stats()
        assert stats['backend'] in ['sqlite', 'diskcache']