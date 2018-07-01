from collections.abc import MutableSequence
from collections import namedtuple, defaultdict
from bs4 import BeautifulSoup

Cell = namedtuple('Cell', ['ri', 'ci', 'rs', 'cs', 'text'])

class Table(MutableSequence):
    def __init__(self, html):
        self.html = html
        self._soup = BeautifulSoup(html, 'html.parser')
        self._rows = self._make_rows()

    def _make_rows(self):
        _dict = self._table_to_dict()
        rows = [
            [col for _,col in sorted(row.items())]
            for _,row in sorted(_dict.items())
        ]
        return rows

    def _cells(self):
        cells = [
            Cell(
                ri=ri,
                ci=ci,
                rs=int(td.get('rowspan', 1)),
                cs=int(td.get('colspan', 1)),
                text=td.text.strip()
            )
            for ri, tr in enumerate(self._soup.find_all('tr'))
            for ci, td in enumerate(tr.find_all(['th', 'td']))
        ]
        return cells

    def _table_to_dict(self):
        _dict = defaultdict(dict)
        for cell in self._cells():
            insertion_indices = Table._find_insertion_indices(cell, _dict)
            for ri, ci in insertion_indices: 
                _dict[ri][ci] = cell.text
        return dict(_dict)

    @staticmethod
    def _find_insertion_indices(cell, _dict):
        row = _dict[cell.ri]
        ci = cell.ci
        while row.get(ci):
            ci += 1
        row_range = range(cell.ri, cell.ri+cell.rs)
        col_range = range(ci, ci+cell.cs)
        for ri in row_range:
            for ci in col_range:
                yield ri, ci

    def __getitem__(self, index):
        return self._rows[index]

    def __iter__(self):
        return iter(self._rows)
        
    def __setitem__(self, index, value):
        pass

    def __delitem__(self, index):
        pass

    def __len__(self):
        return len(self._rows)

    def insert(self, index, value):
        pass

class StructuredTable:
    def __init__(self, html):
        self.table = Table(html)
        self._struct = {
            'sr': 0,
            'sc': 0,
            'hr': 1,
            'hc': 1,
            'hrj': ' ',
            'hcj': ' '
        }
        self._slices = self._make_slices()

    def _make_slices(self):
        struct = self._struct
        slices = {
           'head': slice(struct['sr'], struct['sr']+struct['hr']),
           'colhead': slice(struct['sc'], struct['sc']+struct['hc']),
           'startleft': slice(struct['sc']+struct['hc'],None),
           'starttop': slice(struct['sr']+struct['hr'],None)
        }
        return slices
    @property
    def struct(self):
        return self._struct

    @struct.setter
    def struct(self, value):
        self._struct.update(value)

    @property
    def head(self):
        rows = self.table[self._slices['head']]
        joiner = self._struct['hrj']
        processed = [joiner.join(items) for items in zip(*rows)]
        return processed[self._slices['startleft']]
        
    def __iter__(self):
        return iter(self.table)
