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
    """Test that version is available through one of the standard mechanisms."""
    import dopemux
    
    ver = None
    # 1. Try attribute on package
    if hasattr(dopemux, "__version__"):
        ver = dopemux.__version__
        if not isinstance(ver, str):
            # If shadowed by a module, try attribute on that module
            ver = getattr(ver, "__version__", None)
            
    # 2. Try explicit submodule import if attribute failed
    if ver is None:
        try:
            from dopemux import __version__ as ver_mod
            ver = getattr(ver_mod, "__version__", ver_mod)
        except ImportError:
            pass
            
    # 3. Last resort: check if we can get it from the package-level __version__ module
    if ver is None:
        try:
            import dopemux.__version__
            ver = dopemux.__version__.__version__
        except (ImportError, AttributeError):
            pass

    assert ver is not None, "Could not resolve version through any standard import mechanism"
    assert isinstance(ver, str)
    assert len(ver.split(".")) >= 2  # Sanity check for version format
