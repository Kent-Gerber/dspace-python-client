import pytest

from dspace_client.version import VersionCompatibility


def test_check_server_version_compatibility_accepts_prefixed_version():
    """
    Server version strings like 'DSpace 7.6' should be normalized to '7.6'
    and treated as an exact match when target_versions includes '7.6'.
    """
    is_compatible, warning = VersionCompatibility.check_server_version_compatibility(
        "DSpace 7.6", ["7.6", "8.0"]
    )
    assert is_compatible is True
    assert warning is None

