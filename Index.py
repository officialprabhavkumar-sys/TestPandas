from __future__ import annotations
from typing import Union, TypeAlias, Any, Literal
from collections.abc import Sequence as TypeSequence
import math

BasicTuple : TypeAlias = tuple[Union[str, int, float], ...]
Basic : TypeAlias = Union[int, str, float, BasicTuple]
SequenceNotStr : TypeAlias = Union[list[Any], tuple[Any, ...]]
BasicSequenceNotStr : TypeAlias = Union[list[Basic], tuple[Basic, ...]]

class Index(object):
    def __init__(self, sequence : BasicSequenceNotStr = None, cache : bool = True):
        self._index = []
        self._mapping = {}
        self._reverse_mapping = {}
        self._cache = None
        
        if sequence:
            self._extend_index(sequence)
            if cache:
                self._create_cache()
    
    @staticmethod
    def _verify_item(item : Basic) -> None:
        '''This method checks whether or not the inputted item is str, int, float or a tuple consisting of them.'''

        if item == ():
            raise IndexError("Index tuple cannot be empty.")
        if isinstance(item, tuple):
            Index._verify_tuple(item)
        elif not isinstance(item, (str, int, float)):
            raise TypeError(f"\"{type(item)}\" is not a valid Index type. It must be either str, int, float or a tuple consisting of them.")
        elif isinstance(item, float):
            if math.isnan(item):
                raise TypeError(f"Float of nan is not a valid Index type.")
    
    @staticmethod
    def _verify_tuple(tup : tuple[Basic, ...]) -> None:
        '''This method checks whether the inputted item is truly a tuple or not.
        It also checks whether the tuple is made up of anything other than str, int, float or another tuple containing them,
        If it is, it throws an error.'''
        
        if not isinstance(tup, tuple):
            raise TypeError(f"The item type was \"{type(tup)}\". It needs to be a tuple.")

        if not tup:
            raise IndexError("Index tuple cannot be empty.")
        else:
            for item in tup:
                Index._verify_item(item)
    
    @staticmethod
    def _verify_sequence(sequence : BasicSequenceNotStr) -> None:
        '''This method checks whether the items inside the sequence as well as the sequence itself is valid or not.
        The sequence must not be a string or bytes.'''
        
        if not isinstance(sequence, TypeSequence):
            raise TypeError("Input must be a sequence.")
        elif isinstance(sequence, (str, bytes)):
            raise TypeError("Sequence cannot be a string or bytes.")
        else:
            for item in sequence:
                Index._verify_item(item)
    
    def _update_mappings_with_single_item(self, new_mapping : Basic, verify_entry : bool = True) -> None:
        '''This method updates both the mappings (self._mapping & self._reverse_mapping) with a single new mapping.
        It has an optional argument "verify_entry" which is True by default but can be set to false,
        if you would like the method not to verify the new mapping.'''
        
        if verify_entry:
            self._verify_item(new_mapping)
        
        if new_mapping not in self._reverse_mapping:
            length = len(self._reverse_mapping)
            self._mapping[length] = new_mapping
            self._reverse_mapping[new_mapping] = length
    
    def _update_mappings_with(self, new_mappings : list[Basic] | Basic, verify_entries : bool = True) -> None:
        '''This method updates both the mappings (self._mapping & self._reverse mapping) with new mapping(s).
        This method internally called self._update_mappings_with_single_item to update the mappings.
        The only difference between the two methods is that this method can update with multiple new mappings instead of just one.'''
        
        if isinstance(new_mappings, list):
            if verify_entries:
                self._verify_sequence(new_mappings)

            new_mappings = set(new_mappings)
            for new_mapping in new_mappings:
                self._update_mappings_with_single_item(new_mapping, verify_entry = False)

        else:
            self._update_mappings_with_single_item(new_mappings)
        
    def _create_cache(self) -> None:
        '''The method creates an internal cache for faster (O(1)) lookups.'''
        
        self._cache = {}
        
        for index, item in enumerate(self._index):
            if item not in self._cache:
                self._cache[item] = [index]
            else:
                self._cache[item].append(index)
    
    def flush_cache(self) -> None:
        '''This method sets the cache to None, freeing up any space that might have been previously taken up by the cache.'''
        
        self._cache = None

    def _extend_index(self, sequence : BasicSequenceNotStr) -> None:
        '''This method is used to extend the index by multiple new indexes.
        Internally, it updates everything from mappings to cache (if cache exists.) perfectly for each and every new index.'''
        
        if not sequence:
            raise IndexError("Sequence cannot be empty.")
        
        self._verify_sequence(sequence)
        
        uniques = list(set(sequence))
        self._update_mappings_with(uniques, verify_entries=False)
        
        for item in sequence:
            self._index.append(self._reverse_mapping[item])

            if self._cache is not None:
                self._update_cache("add", {self._reverse_mapping[item] : [(len(self)-1)]}, by_internal_form = True)
    
    def get_loc(self, index : Basic, get_all : bool = True, give_error : bool = True) -> int | list[int] | None:
        '''This method returns the interger index location of the provided index.
        This method has a few optional arguments, namely:
        "get_all" - which is by default true and returns every integer index location of where the provided index if found,
        It can be set to false, in which case only the index of the first appearance of the provided index will be returned.
        "give_error" - which is by default true will raise an error if the provided index is not found anywhere in the index.
        It can be set to false to not give an error and instead return None if the provided index is not found anywhere in the index.'''
        
        self._verify_item(index)
        
        if index not in self._reverse_mapping:
            if give_error:
                raise KeyError(f"\"{index}\" is not present inside the index.")
            else:
                return None
            
        internal_form = self._reverse_mapping[index]
        
        if not get_all:
            if self._cache is not None:
                return self._cache[internal_form][0]
            return self._index.index(internal_form)

        else:
            if self._cache is not None:
                return self._cache[internal_form]
            return [i for i, key in enumerate(self._index) if key == internal_form]
        
    def _update_cache(self, operation : Literal["add", "remove"], operation_args : dict[int, list[int]], by_internal_form : bool = True) -> None:
        '''This method is used to update the cache (if it exists) with the provided operation_arguments. This method takes the following arguments:
        "operation" argument lets you define what type of operation you would like to perform on the index, namely "add" or "remove".
        "operation_args" argument must be a dictionary with key representing the index you would like to add or remove from,
        while the values must be a list representing the integer indexes where the value should be added or removed from.
        "by_internal_form" argument - which must be a bool, tells the method whether the key in operation_args dict is the index's internal representation or not.
        If False, the method automatically converts it to it's internal form and then applies the operation on the cache.'''
        
        if self._cache is None:
            return

        if not isinstance(operation, str):
            raise TypeError("Only strings are allowed as operation specifiers. eg: add or replace.")
        
        if not operation in ["add", "remove"]:
            raise ValueError("\"add\" or \"remove\" are the only valid operation specifiers.")
        
        if not by_internal_form:
            internal_forms = []
            for single_index in operation_args.keys():
                if single_index not in self._reverse_mapping:
                    raise KeyError(f"Mapping not found for {single_index}. Verify whether it is really inside of the Index. If it is, verify mapping and reverse mapping integrities.")
                else:
                    internal_forms.append(self._reverse_mapping[single_index])
        
        else:
            internal_forms = list(operation_args.keys())
        
        for i, index in enumerate(operation_args.keys()):
            rows = operation_args[index]
            for row in rows:
                if row >= len(self):
                    raise IndexError(f"Index \"{row}\" out of bounds.")
                if operation == "add":
                    if internal_forms[i] in self._cache:
                        self._cache[internal_forms[i]].append(row)
                    else:
                        self._cache[internal_forms[i]] = [row]
                else:
                    if row not in self._cache[internal_forms[i]]:
                        raise ValueError(f"\"{row}\" not found in cache for Index \"{internal_forms[i]}\". The index at {row} is {self[row]}.")
                    self._cache[internal_forms[i]].remove(row)
            self._cache[internal_forms[i]].sort()

    def to_list(self) -> list[Basic]:
        '''This method is to get the entire index in the form of a list, with its original values.'''
        
        return [self._mapping[key] for key in self._index]
    
    def is_unique(self) -> bool:
        '''This method returns True if all the values inside of the index are unique, else it returns False.'''
        
        if self._cache is not None:
            return len(self) == len(self._cache)
        
        return len(self) == len(set(self._index))
    
    def unique(self) -> list[Basic]:
        '''This method returns all the unique values in the index.'''
        
        uniques = []
        for key in self._index:
            original_value = self._mapping[key]
            if original_value not in uniques:
                uniques.append(original_value)
        return uniques
    
    def _get_correct_slice(self, index : slice) -> slice:
        '''This is a major method of the Index. This method corrects the slice provided in such a way that:
        The slice start and stop points are purely for selection, it doesn't matter if start is more than stop,
        The items inside between the start and stop will be selected regardless of whether start is more than stop while step is positive
        or whether start is less than stop while step is negative. It does. not. matter.
        The way the slice is returned is dependent on the step (so reverse or straight.)
        The slice also always contains both ends of the slice. Not like normal python where the stop is not included.
        That's it. Enjoy! Took me a hell of a long time and focus to make this specific method.'''
        
        if not isinstance(index, slice):
            raise TypeError(f"\"{type(index)}\" is not a valid type. Only slice type is accepted in get_row_by_slice method.")
        
        start, stop, step = index.start, index.stop, index.step
        if step == None:
            step = 1
        
        indexes = [start, stop]
        for i, index in enumerate(indexes):
            if index != None:
                if index < 0:
                    index = len(self) + index
                if 0 > index or index >= len(self):
                    raise IndexError(f"Index \"{indexes[i]}\" out of bounds.")
                else:
                    indexes[i] = index
        
        start, stop = indexes[0], indexes[1]
        
        if step > 0:
            if start != None and stop != None:
                if start > stop:
                    start, stop = stop, start
                if stop == len(self)-1:
                    stop = None
                else:
                    stop += 1
            elif stop != None:
                if stop == len(self)-1:
                    stop = None
                else:
                    stop += 1
        
        elif step < 0:
        
            if start != None and stop != None:
                if start < stop:
                    start, stop = stop, start
                if stop == 0:
                    stop = None
                else:
                    stop -= 1

            elif start == None and stop != None:
                start, stop = stop, start
                if start == len(self) -1:
                    start = None
                    
        return slice(start, stop, step)
    
    def _get_item_from_int_index(self, index : int) -> Basic:
        '''This is a helper method of __getitem__ dunder method.
        It returns the original value present at the provided integer index.'''
        
        if not isinstance(index, int):
            raise TypeError("_get_item_from_int_index only takes int as the index.")
        
        if index < 0:
            index = len(self) + index
        if index < 0 or index >= len(self):
            raise TypeError(f"Index out of bounds.")
        
        return self._mapping[self._index[index]]
    
    def _get_items_from_int_indexes(self, index : list) -> list[Basic]:
        '''This is a helper method of __getitem__ dunder method.
        It returns all the original values present at the integer indexes inside the provided list of indexes.'''
        
        if not isinstance(index, list):
            raise TypeError("_get_items_from_int_index only takes list of ints as the indexes.")
        
        items = []
        for i in index:
            items.append(self._get_item_from_int_index(i))
        return items
    
    def _get_int_indexes_from_mask(self, mask : list[bool]) -> list[int]:
        '''This method returns all the integer indexes where the boolean in the mask is True.'''
        
        if not isinstance(mask, list):
            raise TypeError("_get_int_indexes_from_mask only takes a list containing booleans.")
        
        if len(mask) != len(self):
            raise IndexError("Length of the mask must match the length of the index.")
        
        indexes = []
        
        for index, Bool in enumerate(mask):
            if not isinstance(Bool, bool):
                raise TypeError(f"All entries inside the mask need to be a boolean, not \"{type(Bool)}\".")
            if Bool:
                indexes.append(index)

        return indexes
    
    def _append(self, item : Basic) -> None:
        '''This method is used to add one new index to the end of the index.'''
        
        self._update_mappings_with_single_item(item)
        self._index.append(self._reverse_mapping[item])
        if self._cache is not None:
            self._update_cache("add", {item : (len(self) - 1)}, by_internal_form = False)
    
    def _get_items_from_slice(self, index : slice) -> list[Basic]:
        '''This method returns a list of all the original values of the index coming under the provided slice,
        according to my slice semantics.'''
        
        if not isinstance(index, slice):
            raise TypeError("_get_items_from_slice only takes a slice.")
        
        corrected_slice = self._get_correct_slice(index)
        return [self._mapping[item] for item in self._index[corrected_slice]]
    
    def _set_item_by_int_index(self, item : Basic, index : int, verify_item : bool = True) -> None:
        '''This method is used to replace the index with a new index at the provided index.
        This method takes an optional argument "verify_item" - which must be a bool,
        which determines whether the new item should be verified or not.'''
        
        if verify_item:
            self._verify_item(item)
        
        if not isinstance(index, int):
            raise TypeError("_set_item_by_int_index only takes integer indexes to be set.")
        
        if index < 0:
            index = len(self) + index
        if index >= len(self) or index < 0:
            raise IndexError("Index out of bounds.")

        if item not in self._reverse_mapping:
            self._update_mappings_with_single_item(item, verify_entry = False)
        
        internal_form = self._reverse_mapping[item]
        
        previous_item_internal_form = self._index[index]
        self._index[index] = internal_form
        
        if self._cache is not None:
            self._update_cache("remove", {previous_item_internal_form : [index]})
            self._update_cache("add", {internal_form : [index]})
    
    def _set_items_by_int_indexes(self, item : Basic, indexes : list[int]) -> None:
        '''This method is used to replace the indexes with a new index to multiple integer indexes.'''
        
        self._verify_item(item)
        
        if not isinstance(indexes, list):
            raise TypeError("_set_items_by_int_indexes only takes a list of integer indexes.")
        
        for index in indexes:
            self._set_item_by_int_index(item, index, verify_item = False)
    
    def _get_int_indexes_from_slice(self, index : slice) -> list[int]:
        '''This method is an internal helper method that returns a list consisting of all the valid numerical indexes
        that would fall under the slice according to my slice semantics.'''
        
        if not isinstance(index, slice):
            raise TypeError("_get_int_indexes_from_slice method only accepts a slice.")
        
        start, stop, step = index.start, index.stop, index.step
        
        if step is None:
            step = 1
        if start is None:
            if step > 0:
                start = 0
            else:
                start = len(self)-1
        if stop is None:
            if step > 0:
                stop = len(self)
            else:
                stop = -1
        
        int_indexes = []
        while (step > 0 and start < stop) or (step < 0 and start > stop):
            int_indexes.append(start)
            start += step

        return int_indexes
    
    def __setitem__(self, index : int | list[int] | list[bool] | slice, item : Basic) -> None:
        '''This method can be used to set new index(s) to multiple integer indexes.
        It takes a variety of inputs that are a single integer index, a list containing multiple integer indexes,
        a mask of booleans or a slice and the new index to be set on those integer indexes.'''
        
        if isinstance(index, int):
            self._set_item_by_int_index(item, index)
        elif isinstance(index, list):
            if isinstance(index[0], bool):
                self._set_items_by_int_indexes(item, self._get_int_indexes_from_mask(index))
            elif isinstance(index[0], int):
                self._set_items_by_int_indexes(item, index)
            else:
                raise TypeError(f"\"{type(index[0])}\" is not a valid type as index specifier for setting items. You can use int index, list of int indexes, mask of booleans or slice for setting items.")
        elif isinstance(index, slice):
            self._set_items_by_int_indexes(item, self._get_int_indexes_from_slice(index))
        else:
            raise TypeError(f"\"{type(index)}\" is not a valid type. You can use int index, list of int indexes, mask of booleans or slice for setting items.")
    
    def __getitem__(self, index : int | list[int] | list[bool] | slice) -> Basic | BasicSequenceNotStr:
        '''This method can be used to get the indexes coming under the provided input.
        This method can take a variety of inputs that are a single integer index, a list containing multiple integer indexes,
        a mask of booleans or a slice.'''
        
        if isinstance(index, int):
            return self._get_item_from_int_index(index)
        elif isinstance(index, list):
            if isinstance(index[0], bool):
                return self._get_items_from_int_indexes(self._get_int_indexes_from_mask(index))
            elif isinstance(index[0], int):
                return self._get_items_from_int_indexes(index)
        elif isinstance(index, slice):
            return self._get_items_from_slice(index)
        else:
            raise TypeError(f"\"{type(index)}\" is not a valid type. Index only supports ints, list of ints, mask of booleans or slice for getting items.")
        
    def __iter__(self):
        
        for key in self._index:
            yield self._mapping[key]
    
    def __len__(self):
        
        return len(self._index)

    def __str__(self) -> str:
        
        original_values = [self._mapping[key] for key in self._index]
        return str(original_values) + f"\n\ntype : {__class__.__name__}, length: {len(self)}"
    
if __name__ == "__main__":
    index = Index(["one", "two", "three", "four", "five", "six"])
    index._extend_index(["one", "two", "eight", "seven", 0])
    
    print(index.to_list())

    for i in index:
        print(i)
    
    print(index.get_loc("one"))
    
    index2 = Index([0,1,2,3,4,5,6,7,8,9])
    print(index2[0:9:-1])
    print(index.unique())