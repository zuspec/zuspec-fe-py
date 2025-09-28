
import dataclasses as dc
import zuspec.dm as dm
from typing import Any, List

@dc.dataclass
class Scope(object):
    scope : object = dc.field()

@dc.dataclass
class StructScope(Scope):
    type : dm.DataTypeStruct = dc.field()

@dc.dataclass
class Context(object):
    ctxt : dm.Context = dc.field()
    scope_s : List[Scope] = dc.field(default_factory=list)
    _result : Any = dc.field(default=None)

    def push_scope(self, s : Scope):
        self.scope_s.append(s)

    @property
    def scope(self) -> Scope:
        return self.scope_s[-1]
    
    def pop_scope(self) -> None:
        self.scope_s.pop()

    @property
    def result(self) -> Any:
        return self._result
    
    def setResult(self, r : Any) -> None:
        self._result = r

    def __call__(self):
        return self.ctxt

    pass