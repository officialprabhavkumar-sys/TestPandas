from __future__ import annotations
from typing import Sequence, Union, TypeAlias, Any, Generator, Literal, TYPE_CHECKING
from collections.abc import Sequence as TypeSequence
from Index import Index
from MultiIndex import MultiIndex

BasicTuple : TypeAlias = tuple[Union[str, int, float], ...]
Basic : TypeAlias = Union[int, str, float, BasicTuple]
SequenceNotStr : TypeAlias = Union[list[Any], tuple[Any, ...]]
BasicSequenceNotStr : TypeAlias = Union[list[Basic], tuple[Basic, ...]]

if TYPE_CHECKING:
    from Series import Series

class iLoc(object):
    def __init__(self, data : Series):
        self._data = data
    
    def __getitem__(self, index : int | list[int] | list[bool] | slice) -> Series:
        
        return self._data._get_data_from_iloc(index)
    
    def __setitem__(self, index : int | list[int] | list[bool] | slice, new_data : Any) -> None:
        
        if isinstance(index, int):
            self._data._set_item_from_int_index(index, new_data)
        elif isinstance(index, list):
            if isinstance(index[0], bool):
                self._data._set_items_from_mask(index, new_data)
            elif isinstance(index[0], int):
                self._data._set_items_from_int_indexes(index, new_data)
            else:
                raise TypeError("iLoc only takes list of integeres or a mask of booleans.")
        elif isinstance(index, slice):
            self._data._set_items_from_int_slice(index, new_data)
        else:
            raise TypeError("iLoc only takes either int, list of ints, mask of booleans or slice made up of int indexes.")