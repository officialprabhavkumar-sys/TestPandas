from __future__ import annotations
from typing import Sequence, Union, TypeAlias, Any, Generator, Literal
from collections.abc import Sequence as TypeSequence
from itertools import product
import math

BasicTuple : TypeAlias = tuple[Union[str, int, float], ...]
Basic : TypeAlias = Union[int, str, float, BasicTuple]
SequenceNotStr : TypeAlias = Union[list[Any], tuple[Any, ...]]
BasicSequenceNotStr : TypeAlias = Union[list[Basic], tuple[Basic, ...]]

class MultiIndex(object):
    def __init__(self, index : list[BasicSequenceNotStr] = None, cache : bool = True, names : BasicSequenceNotStr = None, memory_efficient : bool = False):
        self._multiindex, self._mapping, self._reverse_mapping = self._create_multiindex(index, memory_efficient = memory_efficient)
        self._levels = len(self._multiindex)
        self._cache = None
        self.names = names
        if cache:
            self._create_cache()

    @property
    def names(self) -> list:
        return self._names
    
    @names.setter
    def names(self, names : BasicSequenceNotStr) -> None:
        '''This property setter method verifies whether or not the names are a valid sequence,
        whether they are unique or not and also whether the number of names actually matches the number of MultiIndex levels or not.
        If everything is in order, it sets the _names internal attribute to the names provided.'''
        
        if names:
            self._verify_sequence(names)

            if not len(names) == self._levels:
                raise IndexError("Length of names and number of levels must be the same.")

            if len(names) != len(set(names)):
                raise ValueError("Names need to be unique. Duplicates are not allowed.")
            
            names = tuple(names)
                       
        self._names = names

    @staticmethod
    def _verify_item(item : Basic) -> None:
        '''This method checks whether or not the inputted item is str, int, float or a tuple consisting of them.'''

        if item == ():
            raise IndexError("MultiIndex item cannot be empty.")
        if isinstance(item, tuple):
            MultiIndex._verify_tuple(item)
        elif not isinstance(item, (str, int, float)):
            raise TypeError(f"\"{type(item)}\" is not a valid MultiIndex type. It must be either str, int, float or a tuple consisting of them.")
        elif isinstance(item, float):
            if math.isnan(item):
                raise TypeError(f"Float of nan is not a valid MultiIndex type.")
        
    @staticmethod
    def _verify_tuple(tup : tuple[Basic, ...]) -> None:
        '''This method checks whether the inputted item is truly a tuple or not.
        It also checks whether the tuple is made up of anything other than str, int, float or another tuple containing them,
        If it is, it throws an error.'''
        
        if not isinstance(tup, tuple):
            raise TypeError(f"The item type was \"{type(tup)}\". It needs to be a tuple.")

        if not tup:
            raise IndexError("MultiIndex tuple cannot be empty.")
        else:
            for item in tup:
                MultiIndex._verify_item(item)
    
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
                MultiIndex._verify_item(item)
                
    @staticmethod
    def _verify_length_of_sequences(sequences : Sequence[BasicSequenceNotStr]) -> None:
        '''This method checks whether all the sequences are of the same length or not.'''
        
        first_length = len(sequences[0])
        for sequence in sequences:
            if not len(sequence) == first_length:
                raise IndexError("All sequences must be the same length.")

    @staticmethod
    def _verify_sequences(sequences : Sequence[BasicSequenceNotStr], check_len = True) -> None:
        '''This method invokes two methods: _verify_sequence and _verify_length_of_sequences,
        that check whether items inside the sequence as well as the sequence itself
        are valid or not and whether the sequences are of same length or not respectively.'''
        
        for sequence in sequences:
            MultiIndex._verify_sequence(sequence)
        
        if check_len:
            MultiIndex._verify_length_of_sequences(sequences)
    
    @staticmethod
    def _verify_tuples(tuples : list[BasicTuple], verify_len = True) -> None:
        '''This method passes the tuples to ._verify_tuple method to get the multiple tuples checked.
        It also checks whether all the tuples are the same length or not if the verify_len option is True.'''
        
        for tup in tuples:
            MultiIndex._verify_tuple(tup)
        if verify_len:
            MultiIndex._verify_length_of_sequences(tuples)
    
    @staticmethod
    def _create_multiindex(sequences : list[BasicSequenceNotStr], memory_efficient : bool = False) -> tuple[list[list], dict, dict]:
        '''This method is one of the main workhorses of the class. It returns 3 items.
        First is a list of lists that contain numerical keys pointing to the unique original values that were in the original lists.
        Second is a dictionary of numerical keys mapping to the unique original values that were in the original lists.
        Third is also a dictionary of keys mapping unique original values (as keys) to their numerical keys
        in the second dictionary.'''
        
        mapping = {}
        reverse_mapping = {}
        if memory_efficient:
            for sequence in sequences:
                for item in sequence:
                    if item not in reverse_mapping:
                        numerical_index = len(mapping)
                        mapping[numerical_index] = item
                        reverse_mapping[item] = numerical_index
        else:
            unique_items = set()
            for sequence in sequences:
                unique_items.update(sequence)
            for item in unique_items:
                numerical_index = len(mapping)
                mapping[numerical_index] = item
                reverse_mapping[item] = numerical_index
        
        data = [[] for _ in range(len(sequences))]
        for sequence_number, sequence in enumerate(sequences):
            for item in sequence:
                data[sequence_number].append(reverse_mapping[item])
        
        return (data, mapping, reverse_mapping)
    
    def _pretty_row_view(self, no_of_rows = 50) -> list[list]:
        '''This method returns a nested list with all the original values filled in to allow for easy debugging
        and a view that is pleasing to look at.'''
        
        pretty_row_view = []
        
        if no_of_rows > len(self):
            no_of_rows = len(self)
        
        for row_index in range(no_of_rows):
            row = []
            for index in range(self._levels):
                row.append(self._mapping[self._multiindex[index][row_index]])
            pretty_row_view.append(tuple(row))
        return pretty_row_view
    
    def _create_cache(self) -> None:
        '''This method creates a mapping that maps internal state (made up of ints as keys mapping to original data) rows
        to their positions in the MultiIndex. It allows for faster lookups (O(1)) of rows.
        It is also used to verify data integrity.'''
        
        cache = {}
        for row_index in range(len(self)):
            row = []
            for level in range(self._levels):
                row.append(self._multiindex[level][row_index])
            row = tuple(row)
            if row not in cache:
                cache[row] = [row_index]
            else:
                cache[row].append(row_index)
        self._cache = cache
    
    def _flush_cache(self) -> None:
        '''This method sets cache to None, freeing up memory that might have been used by the cache.'''
        
        self._cache = None
    
    @staticmethod
    def rows_to_long_columns(rows : Sequence[Sequence[Basic]]) -> list[BasicSequenceNotStr]:
        '''This is a simple but very important method that returns a list of lists.
        each list in the nested list contains all the items at a specific index of each row.
        That also means that the number of lists is directly proportional to the length of a single row
        (all rows need to be equal length).
        eg: if each row contains 4 items, then there will be 4 lists in the nested list.'''

        list_of_lists = [[] for _ in range(len(rows[0]))]

        for row in rows:
            for i, item in enumerate(row):
                list_of_lists[i].append(item)
        return list_of_lists
    
    @staticmethod
    def from_tuples(index : Sequence[BasicTuple], names = None, cache : bool = True, memory_efficient : bool = False) -> MultiIndex:
        '''This method allows you to create a MultiIndex from tuples.
        Each tuple MUST signify one MultiIndex point.
        Each and every tuple must be of equal length.'''
        
        MultiIndex._verify_tuples(index)
        list_of_lists = MultiIndex.rows_to_long_columns(index)
        return MultiIndex(list_of_lists, names = names, cache = cache, memory_efficient = memory_efficient)
    
    @staticmethod
    def from_lists(index : Sequence[BasicSequenceNotStr], names = None, cache : bool = True, memory_efficient : bool = False) -> MultiIndex:
        '''This method allows you to create a MultiIndex from lists.
        Each list inside the nested list must signify one column of the MultiIndex.
        Each and every list must be of equal length.'''
        
        MultiIndex._verify_sequences(index)
        return MultiIndex(index, names = names, cache = cache, memory_efficient = memory_efficient)
    
    @staticmethod
    def from_product(index : Sequence[BasicSequenceNotStr], names = None, cache : bool = True, memory_efficient : bool = False) -> MultiIndex:
        '''This method will take two or more Sequences that are not strings and will form a MultiIndex
        from their cartesian products.'''
        
        # Ideas for future: Design an algorithem that takes the lists and just converts them directly to list of lists.
        # Since the final number of lists inside the nested list == number of levels == number of inputted lists in .from_product
        # It should be possible. Though this isn't half bad either, that would probably be much more faster.
        # Just something to consider for next time.
        # Right now, I just want this to work and design the other features as well to get this into working shape first.
        
        if not len(index) > 1:
            raise IndexError("There needs to be 2 or more sequences to form a MultiIndex from products.")
        MultiIndex._verify_sequences(index, check_len=False)
        
        products = list(product(*index))
        
        list_of_lists = MultiIndex.rows_to_long_columns(products)
        return MultiIndex(list_of_lists, names = names, cache=cache, memory_efficient = memory_efficient)
    
    def verify_integrity(self, full : bool = True) -> str:
        '''This method verifies the integrity of the data as well as the mappings.
        It checks whether all the keys needed for data to be returned back to normal are present inside of the mapping or not.
        It also checks whether or not both the mapping and reverse mapping are mutually correct or not.
        You can also set the full argument to false to allow for a shallow but quicker scan. Not recommended.'''
        
        internal_multiindex_state = 1
        mapping_integrity = 1
        reverse_mapping_integrity = 1

        mapping_keys = set(self._mapping.keys())
        reverse_mapping_keys = set(self._reverse_mapping.keys())
        reverse_mapping_values = set(self._reverse_mapping.values())
        
        lengths = {len(column) for column in self._multiindex}
        if len(lengths) != 1:
            internal_multiindex_state = 0
        all_mapping_keys = set()
        for column in self._multiindex:
            all_mapping_keys.update(column)

        for key in all_mapping_keys:
            if not key in mapping_keys or key not in reverse_mapping_values:
                mapping_integrity = 0
                break
        
        for mapping_key in mapping_keys:
            mapped_value = self._mapping[mapping_key]
            if not mapped_value in reverse_mapping_keys:
                reverse_mapping_integrity = 0
                break
            reverse_mapped_key = self._reverse_mapping[mapped_value]
            if not reverse_mapped_key == mapping_key:
                reverse_mapping_integrity = 0
        
        if len(self._mapping.values()) != len(set(self._mapping.values())):
            mapping_integrity = 0
        
        if full:
            for reverse_mapping_key in reverse_mapping_keys:
                reverse_mapped_value = self._reverse_mapping[reverse_mapping_key]
                if not reverse_mapped_value in mapping_keys:
                    reverse_mapping_integrity = 0
                    break
                mapped_key = self._mapping[reverse_mapped_value]
                if not mapped_key == reverse_mapping_key:
                    reverse_mapping_integrity = 0

        integrity_checkers_int = (internal_multiindex_state, mapping_integrity, reverse_mapping_integrity)
        integrity_checkers_dict = {0 : "internal_multiindex_state", 1 : "mapping_integrity", 2 : "reverse_mapping_integrity"}
        integrity_checkers = {}
        
        for i, integrity_checker in enumerate(integrity_checkers_int):
            if integrity_checker == 0:
                integrity_checkers[integrity_checkers_dict[i]] = "Compromised"
            else:
                integrity_checkers[integrity_checkers_dict[i]] = "Ok"
        
        integrity_checks = (
            f"Internal MultiIndex State: {integrity_checkers['internal_multiindex_state']}\n"
            f"Mapping Integrity: {integrity_checkers['mapping_integrity']}\n"
            f"Reverse Mapping Integrity : {integrity_checkers['reverse_mapping_integrity']}"
            )
        
        if not full:
            integrity_checks = integrity_checks + "\nFor full integrity check, pass argument (full = True) to method \"verify_integrity\"."
        
        return integrity_checks
    
    def get_loc(self, tup : tuple, get_all = True, give_error = True) -> int | list[int] | None:
        '''This method is used to get the integer referring to the row index where the MultiIndex "tup" is found.
        This method has a few optional arguments, namely:
        "get_all" - which is by default true and returns every integer index location of where the provided MultiIndex is found,
        It can be set to false, in which case only the index of the first appearance of the provided MultiIndex will be returned.
        "give_error" - which is by default true will raise an error if the provided MultiIndex is not found anywhere in the MultiIndex.
        It can be set to false to not give an error and instead return None if the provided index is not found anywhere in the MultiIndex.'''
        
        self._verify_tuple(tup)
        if len(tup) != self._levels:
            raise IndexError("Length of the MultiIndex you want to find needs to match the number of levels.")
        internal_form = []
        for level, item in enumerate(tup):
            if item not in self._reverse_mapping:
                if give_error:
                    raise KeyError(f"Value not found in entered index for search at level : \"{level}\". There is no such value as \"{item}\" in any level.")
                else:
                    return None
            internal_form.append(self._reverse_mapping[item])

        internal_form = tuple(internal_form)
        
        all_instances = []
        
        if not self._cache:
            for row_index in range(len(self)):
                for level, value_to_match in enumerate(internal_form):
                    if value_to_match != self._multiindex[level][row_index]:
                        break
                else:
                    if not get_all:
                        return row_index
                    all_instances.append(row_index)
                        
        else:
            if not get_all:
                try:
                        return self._cache[internal_form][0]
                except:
                    pass
            else:
                return self._cache[internal_form]

        if give_error:
            raise ValueError(f"MultiIndex : \"{tup}\" not found.")
        else:
            return None
    
    def show_cache(self) -> dict:
        '''This method returns a shallow copy of the cache to allow for easy debugging.'''
        
        if self._cache:
            return dict(self._cache)
        else:
            return None
    
    def get_raw_internal_multiindex(self) -> list[list]:
        '''This method returns a shallow copy of the raw internal state of the MultiIndex to allow for easy debugging.'''
        
        return list(self._multiindex)
    
    def to_tuples(self) -> list[tuple]:
        '''The method returns a list of tuples as the rows of the MultiIndex consisting of their original values.'''
        
        rows = []
        for row_index in range(len(self)):
            row = []
            for level in range(self._levels):
                row.append(self._mapping[self._multiindex[level][row_index]])
            rows.append(tuple(row))
        return rows
    
    def is_unique(self) -> bool:
        '''This method returns True if all the row indexes present inside of the MultiIndex are unique.
        Else, it returns false.'''
        
        if self._cache:
            is_unique = len(self) == len(self._cache)
        else:
            is_unique = len(self) == len(set(self.to_tuples()))
        return is_unique
    
    def get_row_by_int_index(self, index : int) -> list:
        '''This method returns a single MultiIndex row at the provided numerical index, returned back to its original form.'''
        
        if isinstance(index, int):
            if index < 0:
                index = len(self) + index
            if index >= len(self):
                raise IndexError("Index out of bounds.")
            row = []
            for level in range(self._levels):
                row.append(self._mapping[self._multiindex[level][index]])
            return tuple(row)
        else:
            raise TypeError(f"\"{type(index)}\" is not a valid type. Only int type is accepted in get_row_by_int_index method.")
    
    def get_rows_by_int_index(self, index : list[int]) -> list[list]:
        '''This method returns a list of MultiIndex rows present at the numerical indexes provided in the list,
        returned back to their original form.'''
        
        if not isinstance(index, TypeSequence):
            raise TypeError("get_rows_by_int_index method only allows sequences containing integers.")
        elif isinstance(index, (str, bytes)):
            raise TypeError("get_rows_by_int_index_method does not allow string or bytes as the sequence supposed to contain integers.")
        
        rows = []
        for index in index:
            row = self.get_row_by_int_index(index)
            rows.append(row)
        return rows
    
    def _get_correct_slice(self, index : slice) -> slice:
        '''This is another major method of the MultiIndex. This method corrects the slice provided in such a way that:
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
            
            #lets say I have this : [1:4:-1]
            if start != None and stop != None:
                if start < stop:
                    start, stop = stop, start
                    #[4:1:-1]
                if stop == 0:
                    stop = None
                else:
                    stop -= 1
                    #[4:0:-1] Perfect.
            #now lets say I have this: [None:4:-1]
            elif start == None and stop != None:
                start, stop = stop, start
                # [4:None:-1] Perfect.
                if start == len(self) -1:
                    start = None
                    
        return slice(start, stop, step)
    
    def get_rows_by_slice(self, index : slice) -> list[tuple]:
        '''This method returns all the rows selected by the slice.
        Internally it calls the internal _get_correct_slice method to correct the slice based on the custom semantics.
        It then applies the corrected slice on each and every column,
        Finally, it converts the selected MultiIndex to its original form (maps keys to original data) and then returns it in the form of rows.'''
        
        corrected_slice = self._get_correct_slice(index)
        
        columns = []
        
        for level in range(self._levels):
            column = self._multiindex[level][corrected_slice]
            columns.append(column)
        
        rows = []
        for row_index in range(len(columns[0])):
            row = []
            for level in range(self._levels):
                row.append(self._mapping[columns[level][row_index]])
            rows.append(tuple(row))
        return rows
    
    def _get_row_indexes_from_mask(self, index : list[bool]) -> list[int]:
        '''This method returns the indexes of the rows where the mask is True.'''
        
        if len(index) != len(self):
            raise IndexError("The mask needs to be the same length as the number of rows.")
        
        indexes = []
        
        for i, Bool in enumerate(index):
            if not isinstance(Bool, bool):
                raise TypeError("Each and every entry inside of a mask needs to be a bool.")
            elif Bool:
                indexes.append(i)

        return indexes
        
    def get_rows_from_mask(self, index : list[bool]) -> list[list[tuple]]:
        '''This method returns all the rows where the bool in the mask is True.'''
        
        indexes = self._get_row_indexes_from_mask(index)
        
        return self.get_rows_by_int_index(indexes)
            
    def __len__(self) -> int:
        '''This method returns the length of the first column of the MultiIndex.
        Since all the columns of the MultiIndex are the same length, its the correct length of the MultiIndex.'''
        
        return len(self._multiindex[0])
    
    def __getitem__(self, index : int | slice) -> tuple | list[tuple]:
        '''This method allows getting a single row from an int index, Multiple rows from a list of int indexes,
        Multiple rows from a bool mask as well as rows selected by the slice according to the custom slicing semantics.'''
        
        if isinstance(index, int):
            return self.get_row_by_int_index(index)
        
        elif isinstance(index, list):
            if isinstance(index[0], bool):
                return self.get_rows_from_mask(index)
            elif isinstance(index[0], int):
                return self.get_rows_by_int_index(index)
            else:
                raise TypeError(f"\"{type(index[0])}\" is not a supported lookup type.")
        
        elif isinstance(index, slice):
            return self.get_rows_by_slice(index)
        
        else:
            raise TypeError(f"\"{type(index)}\" is not a valid type. Only int, list of ints or a slice are acceptable types for __getitem__.")
    
    def _update_mappings_with_single_item(self, new_mapping : Basic) -> None:
        '''This method updates both the mappings (self._mapping and self._reverse_mapping) with the new mapping value.'''
        
        if new_mapping not in self._reverse_mapping:
            length = len(self._mapping)
            self._mapping[length] = new_mapping
            self._reverse_mapping[new_mapping] = length

    def update_mappings_with(self, new_mappings : list[Basic] | Basic) -> None:
        '''This method updates both the mappings (self._mapping and self._reverse_mapping) with the new mapping value(s).
        This is different than self._update_mappings_with_single_items as this method can take multiple values to update at a single time.'''
        
        if isinstance(new_mappings, list):
            
            new_mappings = list(set(new_mappings))
            self._verify_sequence(new_mappings)
            
            for new_mapping in new_mappings:
                self._update_mappings_with_single_item(new_mapping)
        else:
            self._verify_item(new_mappings)
            self._update_mappings_with_single_item(new_mappings)
        
    def _verify_new_row(self, new_row : list[Basic]) -> None:
        '''This method verifies whether all the values inside of a soon to be added (usually) row are correct or not.'''
        
        if not len(new_row) == self._levels:
            raise IndexError("number of levels of the new MultiIndex entry and the existing MultiIndex must match.")
        for item in new_row:
            self._verify_item(item)
    
    def _get_internal_form_by_int_index(self, index : int) -> tuple[int, ...]:
        '''This method returns the internal form of the row of the MultiIndex by its numerical index.'''
        
        if not isinstance(index, int):
            raise TypeError("Only int indexes are accepted in _get_internal_form_by_int_index method.")
        elif index >= len(self):
            raise IndexError("Index out of bounds.")
        
        internal_form = []
        for level in range(self._levels):
            internal_form.append(self._multiindex[level][index])

        return tuple(internal_form)
    
    def _update_cache(self, operation : Literal["add", "remove"], operation_args : dict[tuple, list[int]], by_internal_form : bool = True) -> None:
        '''This function can be used to either add or remove a numerical index reference of a row to/from the cache.'''
        
        if self._cache is None:
            return
        
        #This was an absolute pain to build. Wow.
        if not isinstance(operation, str):
            raise TypeError("Only strings are allowed as operation specifiers. eg: add or replace.")
        
        operation = operation.lower().strip()
        
        if not operation in ["add", "remove"]:
            raise ValueError("\"add\" or \"remove\" are the only valid operation specifiers.")
        
        if not by_internal_form:
        
            internal_forms = []
            for single_index in operation_args.keys():
                internal_form = []
                for item in single_index:
                    if item not in self._reverse_mapping:
                        raise KeyError(f"Mapping not found for \"{item}\" in \"{single_index}\". Verify whether it is really inside the MultiIndex.\n If it is, verify mapping, reverse mapping integrities.")
                    internal_form.append(self._reverse_mapping[item])
                internal_forms.append(tuple(internal_form))
        else:
            
            internal_forms = list(operation_args.keys())
        
        for i, tup in enumerate(operation_args.keys()):
            for row in operation_args[tup]:
                if row >= len(self):
                    raise IndexError(f"Index \"{row}\" out of bounds.")
                
                if operation == "add":
                    if internal_forms[i] in self._cache:
                        self._cache[internal_forms[i]].append(row)
                    else:
                        self._cache[internal_forms[i]] = [row]
                else:
                    if row not in self._cache[internal_forms[i]]:
                        raise ValueError(f"\"{row}\" not found in cache for the specified MultiIndex. The MultiIndex at {row} is {self[row]}")
                    self._cache[internal_forms[i]].remove(row)
            self._cache[internal_forms[i]].sort()
        
    def _set_int_index(self, index : int, new_data : list[Basic], verify_data : bool = True, update_mappings : bool = True, update_cache : bool = True) -> None:
        '''This method is an internal helper method of __setitem__.
        It is used to replace an existing MultiIndex at the specified numerical index by another MultiIndex.'''
        
        new_data = list(new_data)
        
        if not isinstance(index, int):
            raise TypeError("_set_int_index method only takes an int as the index to be set.")

        if verify_data:
            self._verify_new_row(new_data)

        if update_mappings:
            self.update_mappings_with(new_data)
        
        if update_cache:
            self._update_cache("remove", {self[index] : [index]}, by_internal_form = False)
            self._update_cache("add", {tuple(new_data) : [index]}, by_internal_form = False)

        for level, item in enumerate(new_data):
            item_mapping = self._reverse_mapping[item]
            self._multiindex[level][index] = item_mapping

        
    def _set_multiple_int_indexes(self, index : Sequence[int], new_data : list[Basic]) -> None:
        '''This method is an internal helper method of __setitem__.
        It is used to replace multiple existing MultiIndexes at the specified numerical indexes by another MultiIndex.'''
        
        new_data = list(new_data)
        
        if isinstance(index, TypeSequence):
            if isinstance(index, (str, bytes)):
                raise TypeError("strings or bytes are not a valid sequence type for _set_multiple_int_indexes")
            else:
                self._verify_new_row(new_data)
                self.update_mappings_with(new_data)
                for row_index in index:
                    self._set_int_index(row_index, new_data, verify_data = False, update_mappings = False)
    
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
    
    def _set_rows_by_slice(self, index : slice, new_data : list[Basic], update_cache : bool = True) -> None:
        '''This method is an internal helper method of __setitem__.
        It is used to replace existing MultiIndexes at the given slice by another.'''
        
        new_data = list(new_data)
        
        corrected_slice = self._get_correct_slice(index)

        self._verify_new_row(new_data)
        self.update_mappings_with(new_data)

        if update_cache:
            int_indexes = self._get_int_indexes_from_slice(corrected_slice)
            new_data_internal_form = tuple([self._reverse_mapping[item] for item in new_data])
        
            for row_index in int_indexes:
                row_internal_form = self._get_internal_form_by_int_index(row_index)
                self._update_cache("remove", {row_internal_form : [row_index]})
                self._update_cache("add", {new_data_internal_form : [row_index]})
        
        for level, item in enumerate(new_data):
            item_mapping = self._reverse_mapping[item]
            self._multiindex[level][corrected_slice] = [item_mapping] * len(self._multiindex[0][corrected_slice])
    
    def _compare_names(self, second : MultiIndex) -> bool:
        '''This method compares the names of the current MultiIndex to another. Returns True if they match, else False.'''
        
        if not self.names or not second.names or (self._levels != second._levels):
            return False
        
        for name in self.names:
            if name not in second.names:
                return False
        
        return True
    
    @staticmethod
    def _add_multiindexes(first : MultiIndex, second : MultiIndex, inplace : bool = False) -> MultiIndex | None:
        '''This method adds two MultiIndexes together. You can choose to either return a new MultiIndex using inplace = False (default)
        or you can extend the first MultiIndex with the second MultiIndex using inplace = True.'''
        
        if not isinstance(first, MultiIndex) or not isinstance(second, MultiIndex):
            raise TypeError("Only two MultiIndexes can be concatenated together.")
        if not first._levels == second._levels:
            raise IndexError("Number of levels of the first MultiIndex must be the same as the number of levels of the second MultiIndex for them to be concatenated.")
        
        if not inplace:
            first = MultiIndex.from_tuples(first.to_tuples())

        first.update_mappings_with(list(second._reverse_mapping.keys()))
        
        names_match = first._compare_names(second)
        
        for level in range(first._levels):
            level_to_extend = []
            seconds_level = second._multiindex[level]
            for mapping in seconds_level:
                actual_value = second._mapping[mapping]
                level_to_extend.append(first._reverse_mapping[actual_value])
            
            if names_match:
                level = first.names.index(second.names[level])
            
            first._multiindex[level].extend(level_to_extend)
        
        if first._cache:
            range_start_of_rows_to_update = len(first) - len(second)
            range_stop_of_rows_to_update = len(first)

            for row_index in range(range_start_of_rows_to_update, range_stop_of_rows_to_update):
                first._update_cache("add", {first._get_internal_form_by_int_index(row_index) : [row_index]})
            
        if not inplace:
            return first
        
    def extend(self, second : MultiIndex) -> None:
        '''This method extends the current MultiIndex with the second MultiIndex.'''
        
        self._add_multiindexes(self, second, inplace = True)
            
    def __setitem__(self, index : int | list[int] | list[bool] | slice, new_data : list[Basic]) -> None:
        '''This method allows you to set new MultiIndexes to the index you provided.
        I will be extremely disappointed if you don't use this atleast once because it was an absolute pain to make.
        This method can take one numerical index, a list of numerical indexes, a boolean mask or even a slice.'''
        
        if isinstance(index, int):
            self._set_int_index(index, new_data)

        elif isinstance(index, list):
            if isinstance(index[0], bool):
                index = self._get_row_indexes_from_mask(index)
            
            elif not isinstance(index[0], int):
                raise TypeError(f"\"{type(index[0])}\" is not a supported lookup type.")
            
            self._set_multiple_int_indexes(index, new_data)
            
        elif isinstance(index, slice):
            self._set_rows_by_slice(index, new_data)
    
    def __add__(self, second):
        '''This method returns a new MultiIndex consisting of both itself and the second MultiIndexes added together.'''
        
        return self._add_multiindexes(self, second)
    
    def __iter__(self) -> Generator:
        '''returns an iterator providing tuples of rows of the MultiIndexes returned to their original values.'''
        
        return iter(self.to_tuples())
    
    def __contains__(self, item : BasicTuple) -> bool:
        '''This method returns True if the provided item is present inside the MultiIndex, otherwise it returns False.'''
        
        if not isinstance(item, tuple) or (self._levels != len(item)):
            return False
        
        if self._cache:
            try:
                internal_form = tuple([self._reverse_mapping[i] for i in item])
                return internal_form in self._cache
            except:
                return False
        
        try:
            self.get_loc(item, get_all = False)
            return True
        except:
            return False
        
    def __str__(self) -> str:
        '''This method returns a pretty view of the first 50 rows (by default) of the MultiIndex.'''
        
        string_of_rows = f"names : {self.names}\n"
        for row in self._pretty_row_view():
            string_of_rows = string_of_rows + str(row) + "\n"
        
        return string_of_rows
    
    def __repr__(self) -> str:
        '''This method returns a comprehensive view of all the internal states,
        mappings as well as data integrity of the MultiIndex.'''
        
        return ("MultiIndex internal view:\n"
    f"{str(self._multiindex).replace("],", "]\n")}\n\n"
    f"Mapping :\n{str(self._mapping)}\n\n"
    f"Reverse mapping :\n{str(self._reverse_mapping)}\n\n"
    f"number of levels : {str(self._levels)}\n\n"
    f"Integrity checks:\n{str(self.verify_integrity())}")