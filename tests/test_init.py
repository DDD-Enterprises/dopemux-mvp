"""
Tests for package initialization.
"""


def test_package_import():
    """Test that the package can be imported."""
    import dopemux

    assert dopemux is not None


def test_submodules_import():
    """Test that submodules can be imported."""
    from dopemux import adhd, claude, cli, config

    assert config is not None
    assert adhd is not None
    assert claude is not None
    assert cli is not None


def test_version_available():
    """Test that version is available."""
    from dopemux import __version__

    assert __version__ is not None
    assert isinstance(__version__, str)
