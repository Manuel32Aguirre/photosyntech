from ui.modules.GraphsModule import GraphsModule
from ui.modules.MainModule import MainModule
from ui.modules.Module import Module

def get_all_modules() -> list[Module]:
    """
    This functions provides a list of all available modules in the system.
    There could be need that we need to add dependency injection for each module.

    We can add any DI tool before returning the list of modules.
    """
    return [
        MainModule(),
        GraphsModule()
    ]