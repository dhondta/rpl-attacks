from core.commands import setup, update

update(silent=True)
setup(silent=True)

from .setup import Test1Config, Test2CoojaSetup
from .experiment import Test3Make, Test4Remake, Test5Clean
from .campaign import Test6Prepare, Test7Drop
