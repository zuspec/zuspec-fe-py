#****************************************************************************
# Copyright 2019-2025 Matthew Ballance and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#****************************************************************************
import dataclasses as dc
import ast
import zuspec.dm as dm
from typing import Any, Dict, Type

@dc.dataclass
class ExprFactory(object):
    ctxt : dm.Context = dc.field()

    def build(self, e : ast.expr) -> dm.TypeExpr:
        if isinstance(e, ast.BinOp):
            return self._buildBinExpr(e)
        elif isinstance(e, ast.UnaryOp):
            pass
        elif isinstance(e, ast.Name):
            return self._buildNameRef(e)
        else:
            raise NotImplementedError("Expression type %s (%s)" % (
                type(e), str(e)
            ))
        pass

    def _buildBinExpr(self, e : ast.BinOp) -> dm.TypeExprBin:
        op_map : Dict[Any, dm.BinOp] = {
            ast.Add: dm.BinOp.Add,
            ast.Sub: dm.BinOp.Sub,
            ast.Mult: dm.BinOp.Mul,
            ast.Div: dm.BinOp.Div,
            ast.Mod: dm.BinOp.Mod,
            ast.BitAnd: dm.BinOp.BitAnd,
            ast.BitOr: dm.BinOp.BitOr,
            ast.BitXor: dm.BinOp.BitXor,
            ast.LShift: dm.BinOp.Sll,
            ast.RShift: dm.BinOp.Srl,
            ast.Eq: dm.BinOp.Eq,
            ast.NotEq: dm.BinOp.Ne,
            ast.Lt: dm.BinOp.Lt,
            ast.LtE: dm.BinOp.Le,
            ast.Gt: dm.BinOp.Gt,
            ast.GtE: dm.BinOp.Ge,
            ast.And: dm.BinOp.LogAnd,
            ast.Or: dm.BinOp.LogOr
        }
        if e.op not in op_map.keys():
            raise NotImplementedError(f"Unsupported BinOp: {type(e.op)}")

        lhs = ExprFactory(self.ctxt).build(e.left)
        rhs = ExprFactory(self.ctxt).build(e.right)

        loc = dm.Loc(line=e.lineno, pos=e.col_offset)

        return self.ctxt.mkTypeExprBin(
            lhs, 
            op_map[e.op], 
            rhs,
            loc)
    
    def _buildNameRef(self, e : ast.Name) -> dm.TypeExpr:
        pass

    pass