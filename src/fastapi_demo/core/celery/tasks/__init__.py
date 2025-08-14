import importlib
import os
import pkgutil

package_dir = os.path.dirname(__file__)
for _finder, name, _ispkg in pkgutil.iter_modules([package_dir]):
    importlib.import_module(f"{__name__}.{name}")
