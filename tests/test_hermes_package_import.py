import importlib
import sys


def test_hermes_package_imports_without_optional_browser_adapter():
    sys.modules.pop("adapters.hermes", None)
    module = importlib.import_module("adapters.hermes")
    assert module is not None


def test_fleet_installer_module_imports_without_optional_browser_adapter():
    module = importlib.import_module("adapters.hermes.fleet.install")
    assert hasattr(module, "install")
