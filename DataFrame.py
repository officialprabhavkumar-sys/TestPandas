from __future__ import annotations
from typing import Sequence, Union, TypeAlias, Any, Generator, Literal, TYPE_CHECKING
from collections.abc import Sequence as TypeSequence
from Index import Index
from MultiIndex import MultiIndex
from Series import Series

BasicTuple : TypeAlias = tuple[Union[str, int, float], ...]
Basic : TypeAlias = Union[int, str, float, BasicTuple]
SequenceNotStr : TypeAlias = Union[list[Any], tuple[Any, ...]]
BasicSequenceNotStr : TypeAlias = Union[list[Basic], tuple[Basic, ...]]

class DataFrame(object):
    def __init__(self, data : list[list] | list[dict[Basic, list[Any]]] | dict[Basic, list[Any]], index : list | Index | MultiIndex = None, columns : list | Index | MultiIndex = None):
        self._initialize_data(data)

        if index is not None:
            self.index = index
        if columns is not None:
            self.columns = columns
        
    @property
    def columns(self):
        return self._columns
    
    @columns.setter
    def columns(self, index):
        if isinstance(index, (list, Index, MultiIndex)):
            if not len(self._data) == len(index):
                raise TypeError("length of the index for columns and the number of columns needs to be the same.")
            if isinstance(index, list):
                columns = Index(index)
            self._columns = columns
    
    @property
    def index(self):
        return self._index
    
    @index.setter
    def index(self, index):
        if isinstance(index, (list, Index, MultiIndex)):
            if not len(self) == len(index):
                raise TypeError("length of the index for rows and the number of rows needs to be the same.")
            if isinstance(index, list):
                index = Index(index)
            self._index = index

    def _initialize_data(self, data : list[list] | list[dict[Basic, list[Any]]] | dict[Basic, list[Any]]) -> None:
        if not data:
            return
        
        if isinstance(data, dict):
            if isinstance(data[list(data.keys())[0]], list):
                new_data = list(data.values())
                max_length = max([len(column) for column in new_data])
                new_data = [column.extend([None for _ in max_length - len(column)]) for column in data.values()]
                
                self._data = new_data
                
                self.columns = list(data.keys())
                self.index = [i for i in range(max_length)]
                
            elif isinstance(data[list(data.keys())[0]], dict):
                rows = list(data.keys())
                
                all_columns = []
                for column_keys in data.values().keys():
                    for column_key in column_keys:
                        if column_key not in all_columns:
                            all_columns.append(column_key)

                new_data = [[] for _ in range(len(all_columns))]
                
                for row_key in rows:
                    row = data[row_key]
                    for i, column in enumerate(all_columns):
                        if column in data[row]:
                            new_data[i].append(data[row[column]])
                        else:
                            new_data[i].append(None)
                
                self._data = new_data
                
                self.columns = all_columns
                self.index = rows
                
        elif isinstance(data, list):
            if isinstance(data[0], dict):
                new_data = {i : data[i] for i in range(len(data))}
                self._initialize_data(new_data)
                
            elif isinstance(data[0], list):
                max_length = max([len(row) for row in data])
                
                new_data = [[] for _ in range(max_length)]
                
                for row in data:
                    row.extend([None for _ in range(max_length - len(row))])
                    for i, item in enumerate(row):
                        new_data[i].append(item)
                
                self._data = new_data
                
                self.columns = [i for i in range(max_length)]
                self.index = [i for i in range(len(data))]
        
            elif isinstance(data[0], Series):
                self._initialize_data([series.to_dict() for series in data])
            
            else:
                raise TypeError(f"\"{type(data[0])}\" is not a valid type for creating a DataFrame.")
        
        else:
            raise TypeError(f"{type(data)} is not a valid type for creating a DataFrame.")
        
    def to_list(self) -> list[list[Any]]:
        return self._data
    
    def to_list_of_rows(self) -> list[list[Any]]:
        rows = [[] for _ in range(len(self))]
        for column_index in range(len(self._data)):
            for row_index in range(len(rows)):
                data = self._data[column_index][row_index]
                if data is not None:
                    rows[row_index].append(data)
        return rows
        
    def __len__(self):
        return len(self._data[0])

    def __str__(self):
        pretty_print = f"columns: {str(self.columns.to_list())}\n".replace("[", "").replace("]", "")
        list_of_rows = self.to_list_of_rows()
        for i in range(len(list_of_rows)):
            pretty_print += f"{self.index[i]} : {list_of_rows[i]}\n"
        return pretty_print

if __name__ == "__main__":
    dataframe = DataFrame([[1,2], [2,3]])
    print(dataframe)