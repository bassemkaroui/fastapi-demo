import importlib
import os
import pkgutil

from sqlmodel import SQLModel

# Dynamically import every module in this package
package_dir = os.path.dirname(__file__)
for _finder, name, _ispkg in pkgutil.iter_modules([package_dir]):
    importlib.import_module(f"{__name__}.{name}")

metadata = SQLModel.metadata
