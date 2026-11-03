"""Public diff-engine result types shared with consumers.

These types form the stable contract between the diff engine (producer) and
the code that consumes its results (e.g. ``src/diff.py``). They deliberately
do not expose ``SequenceMatcher`` opcodes: the engine interprets opcodes
internally and returns these higher-level objects instead.
"""

from dataclasses import dataclass


# Row-level change status. A row in a diffed table is either kept (present in
# both inputs), inserted (present only in the right input) or removed (present
# only in the left input).
ROW_STATUS_KEEP = 'keep'
ROW_STATUS_INSERT = 'insert'
ROW_STATUS_REMOVE = 'remove'


@dataclass(frozen=True)
class RowDiff:
    """One row in the combined (left/right merged) row sequence.

    ``name``   - the row's name.
    ``status`` - one of ROW_STATUS_KEEP / ROW_STATUS_INSERT / ROW_STATUS_REMOVE.
    """
    name: str
    status: str
