from enum import Enum
from typing import List, Callable, Union

from django.utils.safestring import SafeString
#from core import models


class InventoryHookType(Enum):
    ITEM_DISPLAY = 1
    EXTENSION_DISPLAY = 2
    ITEM_HAND_OUT = 3
    ITEM_RETURN = 4
    ITEM_SAVE = 5


DisplayRetType = Union[None, SafeString]

# ItemDisplayHookType = Callable[[models.InventoryItem], DisplayRetType]
# ExtensionDisplayHookType = Callable[[models.InventoryItem, models.InventoryLend], DisplayRetType]


class HookRegister:
    def __init__(self):
        self._hooks = {}

    def register(self, magic_type: str, hook_type: InventoryHookType, priority=100):
        return lambda func: self.register_hook(func, magic_type, hook_type, priority)

    def register_hook(self, hook: Callable, magic_type: str, hook_type: InventoryHookType, priority=100):
        hook_list = self._hooks.get((magic_type , hook_type), list())
        hook_list.append((priority, hook))
        hook_list = sorted(hook_list, key=lambda i: i[0])
        self._hooks[(magic_type, hook_type)] = hook_list
        return hook  # Return the function itself, so this can be used as decorator :)

    def remove(self, hook: Callable, magic_type: str, hook_type: InventoryHookType):
        hook_list = self._hooks.get((magic_type, hook_type), list())
        hook_list = [i for i in hook_list if i[1] != hook]
        self._hooks[(magic_type, hook_type)] = hook_list

    def get_hook_list(self, magic_type: str, hook_type: InventoryHookType) -> List[Callable]:
        hooks = self._hooks.get((magic_type, hook_type), list())
        if not hooks:
            return []
        else:
            return list(zip(*hooks))[1]


registry = HookRegister()


