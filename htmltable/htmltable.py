from collections.abc import Sequence
from collections import namedtuple, defaultdict
from bs4 import BeautifulSoup
from functools import partial

Cell = namedtuple('Cell', ['ri', 'ci', 'rs', 'cs', 'text'])

class Table(Sequence):
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
        
    def __len__(self):
        return len(self._rows)

class StructuredTable(Table):
    def __init__(self, html):
        super(StructuredTable, self).__init__(html)
        self._struct = {
            'sr': 0,
            'sc': 0,
            'hr': 1,
            'hc': 1,
            'hrj': ' ',
            'hcj': ' '
        }

    def _slices(self):
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

    def _head(self, head_slice):
        rows = self[head_slice]
        joiner = self._struct['hrj']
        processed = [joiner.join(items) for items in zip(*rows)]
        return processed

    def simplify(self):
        slices = self._slices()
        fixed_params = {
            'colhead_slice': slices['colhead'],
            'joiner': self._struct['hcj'],
            'startleft_slice': slices['startleft']
        }
        simple_row = partial(_simple_row, **fixed_params)
        simple_heading = simple_row(self._head(slices['head']))
        simple_table = [simple_heading]
        simple_table.extend(simple_row(row) for row in self[slices['starttop']])
        return simple_table

    def to_dict(self, row_outer_key=False):
        rows = self.simplify()
        if row_outer_key:
            rows = list(zip(*rows))
        header = rows[0][1:]
        _dict = {
            row[0]: dict(zip(header, row[1:]))
            for row in rows[1:]
        }
        return _dict
            
def _simple_row(row, joiner, colhead_slice, startleft_slice):
    colhead = joiner.join(row[colhead_slice])
    simple = [colhead]
    simple.extend(row[startleft_slice])
    return simple
