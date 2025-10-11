from __future__ import annotations
import dataclasses as dc
import zuspec.dm as dm
from typing import Optional, cast
from .context import Context

@dc.dataclass
class StaticPathMock(object):
    """Path-building mock object"""
    ctxt : Context = dc.field()
    typ : type = dc.field()
    expr : Optional[dm.TypeExpr] = dc.field(default=None)

    def __getattribute__(self, name):
        if name in ("ctxt", "typ", "expr", "__class__"):
            return object.__getattribute__(self, name)
        # Validate field exists

        fields = {f.name for f in dc.fields(self.typ)}

        if name not in fields:
            raise AttributeError(f"Invalid field '{name}' in path")
        
        root = self.expr if self.expr is not None else self.ctxt().mkTypeExprRefSelf()

        # Find the field offset and type
        idx, field_type = next((i,f) for i,f in enumerate(dc.fields(self.typ)) if f.name == name)

        expr = self.ctxt().mkTypeExprRefField(root, idx)

        # Return new mock for nested access
        return StaticPathMock(
            self.ctxt,
            cast(type, field_type.type), 
            expr
        )

    def __call__(self):
        # For supporting callables if needed
        raise Exception("Method calls cannot be a static path element")
        return self

    def __repr__(self):
        return f"_BindPathMock({self.typ})"
