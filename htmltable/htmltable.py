from collections.abc import MutableSequence
from collections import namedtuple, defaultdict
from bs4 import BeautifulSoup

Cell = namedtuple('Cell', ['ri', 'ci', 'rs', 'cs', 'text'])

class Table(MutableSequence):
    def __init__(self, html):
        self.html = html
        self._soup = BeautifulSoup(html, 'html.parser')

    @property
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

    @property
    def _dict(self):
        _dict = defaultdict(dict)
        for cell in self._cells:
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
        row_dict = self._dict[index]
        row = [v for _,v in sorted(row_dict.items())]
        return row

    def __setitem__(self, index, value):
        pass

    def __delitem__(self, index):
        pass

    def __len__(self):
        return len(self._dict)

    def insert(self, index, value):
        pass
