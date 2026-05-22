from scripts import check_mcps


def test_check_mcps_mock_suite_passes():
    assert check_mcps.run_suite("mock", check_mcps.MOCK_CASES) is True


def test_check_mcps_real_missing_config_suite_passes():
    assert check_mcps.run_suite("real-missing-config", check_mcps.REAL_MISSING_CONFIG_CASES) is True
