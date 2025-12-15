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

class Loc(object):
    def __init__(self, data : Series):
        self._data = data
    
    def _get_correct_slice_from_slice_of_items(self, index : slice[Basic, Basic, int]) -> slice:
        
        if not isinstance(index, slice):
            raise TypeError("_get_corrected_slice_from_slice_of_items only takes slice.")
        
        start, stop, step = index.start, index.stop, index.step

        if start is not None:
            start = self._data.index.get_loc(start, get_all = False)
        
        if stop is not None:
            stop = max(self._data.index.get_loc(stop))
        
        corrected_slice = self._data._get_correct_slice(slice(start, stop, step))
        
        return corrected_slice

    def __getitem__(self, index : Basic | list[Basic] | list[bool] | slice) -> Series:
        
        if isinstance(index, (int, str, float, tuple)):
            return self._data._get_data_from_iloc(self._data.index.get_loc(index))
        elif isinstance(index, list):
            if isinstance(index[0], bool):
                return self._data._get_data_from_iloc(index)
            else:
                locations = []
                for item in index:
                    locations.extend(self._data.index.get_loc(item))
                return self._data._get_data_from_iloc(locations)
        elif isinstance(index, slice):
            return self._data._get_data_from_iloc(self._get_correct_slice_from_slice_of_items(index))
        else:
            raise TypeError(f"\"{type(index)}\" is not supported.")
    
    def __setitem__(self, index : Basic | list[Basic] | list[bool] | slice, new_data : Any | list[Any]) -> None:
        
        if isinstance(index, (int, str, float, tuple)):
            indexes_to_change = self._data.index.get_loc(index)
            if isinstance(indexes_to_change, int):
                self._data._set_item_from_int_index(indexes_to_change, new_data)
            elif len(indexes_to_change) == 1:
                self._data._set_item_from_int_index(indexes_to_change[0], new_data)
            else:
                self._data._set_items_from_int_indexes(indexes_to_change, new_data)
        elif isinstance(index, list):
            if isinstance(index[0], bool):
                indexes_to_change = self._data._get_int_indexes_from_mask(index)
            else:
                indexes_to_change = []
                for single_index in index:
                    indexes_to_change.extend(self._data.index.get_loc(single_index))
            self._data._set_items_from_int_indexes(indexes_to_change, new_data)
        elif isinstance(index, slice):
            self._data._set_items_from_int_indexes(self._data._get_int_indexes_from_slice(self._get_correct_slice_from_slice_of_items(index)), new_data)
        else:
            raise TypeError(f"\"{type(index)}\" is not supported.")