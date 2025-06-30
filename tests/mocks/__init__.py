"""Mock modules for testing."""

import sys
from unittest.mock import MagicMock

# Set up py4godot mocks
py4godot_mock = MagicMock()
sys.modules["py4godot"] = py4godot_mock
sys.modules["py4godot.classes"] = MagicMock()
sys.modules["py4godot.utils"] = MagicMock()
sys.modules["py4godot.utils.smart_cast"] = MagicMock()
sys.modules["py4godot.classes.Node3D"] = MagicMock()
sys.modules["py4godot.classes.Script"] = MagicMock()
sys.modules["py4godot.classes.ResourceLoader"] = MagicMock()
