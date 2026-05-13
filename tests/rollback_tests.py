from pfix.rollback import find_backup_dir, list_backups


class TestRollback:
    def test_find_backup_dir(self, tmp_path):
        source = tmp_path / "src" / "main.py"
        backup_dir = find_backup_dir(source)
        assert backup_dir == tmp_path / "src" / ".pfix_backups"

    def test_list_backups_empty(self, tmp_path):
        backups = list_backups(tmp_path / "nonexistent.py")
        assert backups == []
