from pfix.env_diagnostics.serialization import SerializationDiagnostic


class TestSerializationDiagnostic:
    def test_initialization(self) -> None:
        diag = SerializationDiagnostic()
        assert diag.category == "serialization"

    def test_pickle_protocol_check(self) -> None:
        diag = SerializationDiagnostic()
        results = diag._check_pickle_protocol()
        assert isinstance(results, list)
        if results:
            assert results[0].check_name == "pickle_protocol"
            assert "protocol" in results[0].message.lower()
