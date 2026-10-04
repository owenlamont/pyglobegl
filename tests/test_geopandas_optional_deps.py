from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from pyglobegl.geopandas import _require_geopandas, _require_pandas, _require_pandera


if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.mark.parametrize(
    ("require", "module"),
    [
        (_require_geopandas, "geopandas"),
        (_require_pandera, "pandera.pandas"),
        (_require_pandas, "pandas"),
    ],
)
def test_require_keeps_missing_module_name(
    monkeypatch: pytest.MonkeyPatch, require: Callable[[], None], module: str
) -> None:
    monkeypatch.setitem(sys.modules, module, None)

    with pytest.raises(ModuleNotFoundError, match="pyglobegl\\[geopandas\\]") as info:
        require()

    assert info.value.name == module
