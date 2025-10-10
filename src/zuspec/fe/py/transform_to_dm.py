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
import inspect
import logging
import zuspec.dataclasses as zdc
from typing import ClassVar, List, Optional, cast
from zuspec.dataclasses import Input, Output
import zuspec.dm as dm
from zuspec.dm import (DataTypeComponent, Loc)
from .context import Context, StructScope
from .stmt_factory import StmtFactory
from .type_factory import TypeFactory
from .visitor import Visitor

@dc.dataclass
class TransformToDm(Visitor):
    ctxt : Optional[Context] = dc.field(default=None)
    _log : ClassVar = logging.getLogger("zuspec.be.py.TransformToDm")

    def __post_init__(self):
        super().__post_init__()
        assert self.ctxt is not None

    def visitComponentType(self, t):
        # Always work with the class, not the instance
        t_cls = t if isinstance(t, type) else type(t)
        name = t_cls.__qualname__
        comp_t = self.ctxt().mkDataTypeComponent(name)
        self.ctxt().addDataTypeStruct(comp_t)

        self.ctxt.push_scope(StructScope(scope=t, type=comp_t))

        # Call base Visitor logic to ensure visitExec is called
        self.visitStructType(cast(zdc.Struct, t))

        # Explicitly call visitExec for @sync methods
        from zuspec.dataclasses.annotation import AnnotationSync
        for attr_name in dir(t_cls):
            attr = getattr(t_cls, attr_name)
            if hasattr(attr, "__zsp_annotation__") and isinstance(getattr(attr, "__zsp_annotation__"), AnnotationSync):
                self.visitExec(attr)
        
        self.ctxt.pop_scope()
        self.ctxt.setResult(comp_t)

    def visitStructType(self, t : zdc.Struct):
        self._visitFields(t)
        self._visitExecs(t)
        
        for f in dir(t):
            o = getattr(t, f)
#             if callable(o) and hasattr(o, Annotation.NAME):
#                 # Extract source code of the method
#                 try:
#                     src = inspect.getsource(o)
#                     src = textwrap.dedent(src)
#                     tree = ast.parse(src)
#                     for stmt in tree.body[0].body:  # tree.body[0] is the FunctionDef
#                         self.visit_statement(stmt)
#                 except Exception as e:
#                     print(f"Could not process method {f}: {e}")
# #                self.visitExec(f, o)
# #                print("Found")

    def visitExec(self, m):
        # Called for methods decorated with @zdc.sync
        import inspect
        import ast
        from zsp_arl_dm.core import ExecKindT

        import textwrap
        src = inspect.getsource(m)
        src = textwrap.dedent(src)
        tree = ast.parse(src)

        body = self.ctxt().mkTypeProcStmtScope()

        def _proc_expr(expr):
            # Recursively convert Python AST expressions to vsc_dm.core expressions
            if isinstance(expr, ast.BinOp):
                pass
            elif isinstance(expr, ast.UnaryOp):
                op_map = {
                    ast.Not: vsc_dm.UnaryOp.Not,
                    # Add more as needed
                }
                operand = _proc_expr(expr.operand)
                op = op_map.get(type(expr.op))
                if op is None:
                    raise NotImplementedError(f"Unsupported UnaryOp: {type(expr.op)}")
                return self.ctxt().mkModelExprUnary(op, operand, False)
            elif isinstance(expr, ast.Name):
                # Look up the field in the current component by name
                field = None
                for f in self.comp.getFields():
                    if f.name() == expr.id:
                        field = f
                        break
                if field is None:
                    raise RuntimeError(f"Field '{expr.id}' not found in component")
                model_field = self.ctxt.buildModelField(field)
                return self.ctxt().mkModelExprFieldRef(model_field)
            elif isinstance(expr, ast.Attribute):
                # Handle attribute access (e.g., self.x)
                if isinstance(expr.value, ast.Name) and expr.value.id == "self":
                    field = None
                    for f in self.comp.getFields():
                        if f.name() == expr.attr:
                            field = f
                            break
                    if field is None:
                        raise RuntimeError(f"Field '{expr.attr}' not found in component")
                    model_field = self.ctxt.buildModelField(field)
                    return self.ctxt().mkModelExprFieldRef(model_field)
                raise NotImplementedError("Only 'self.<field>' attribute access is supported")
            elif isinstance(expr, ast.Constant):
                # Only handle integer constants for now
                if isinstance(expr.value, int):
                    return self.ctxt().mkModelExprVal(self.ctxt().mkValRefInt(expr.value, True, 32))
                else:
                    raise NotImplementedError(f"Unsupported constant type: {type(expr.value)}")
            else:
                raise NotImplementedError(f"Unsupported AST expr: {type(expr)}")

        def _proc_stmt(node):
            stmts = []
            if isinstance(node, ast.If):
                cond_expr = _proc_expr(node.test)
                body_scope = self.ctxt().mkTypeProcStmtScope()
                for stmt in node.body:
                    for s in _proc_stmt(stmt):
                        body_scope.addStatement(s)
                if_clauses = [self.ctxt().mkTypeProcStmtIfClause(cond_expr, body_scope)]
                else_scope = self.ctxt().mkTypeProcStmtScope()
                for stmt in node.orelse:
                    for s in _proc_stmt(stmt):
                        else_scope.addStatement(s)
                if_stmt = self.ctxt().mkTypeProcStmtIfElse(if_clauses, else_scope)
                stmts.append(if_stmt)
            # TODO: handle other statement types (assign, expr, etc.)
            return stmts

        # Traverse AST and add statements to body
        for stmt in tree.body[0].body:
            for s in _proc_stmt(stmt):
                body.addStatement(s)

        exec_proc = self.ctxt().mkTypeExecProc(ExecKindT.Body, body)
        self.comp.addExec(exec_proc)

    def visitExecSync(self, e : zdc.ExecSync):
        import inspect
        import ast
        from .static_path_mock import StaticPathMock
        from zsp_arl_dm.core import ExecKindT

        import textwrap
        src = inspect.getsource(e.method)
        src = textwrap.dedent(src)
        tree = ast.parse(src)

        scope : StructScope = cast(StructScope, self.ctxt.scope)

        clock_r = e.clock(StaticPathMock(self.ctxt, scope.scope))
        reset_r = e.clock(StaticPathMock(self.ctxt, scope.scope))

        if not isinstance(clock_r, StaticPathMock) or clock_r.expr is None:
            raise Exception("Clock is not a static ref (%s)" % str(clock_r))

        if not isinstance(reset_r, StaticPathMock) or reset_r.expr is None:
            raise Exception("Reset is not a static ref (%s)" % str(reset_r))

        # TODO: Convert lambda expressions to ref expressions

        clock = clock_r.expr
        reset = reset_r.expr

        file = e.method.__code__.co_filename
        line = e.method.__code__.co_firstlineno
        pos = -1
        exec = self.ctxt().mkExecSync(
            clock,
            reset,
            loc=Loc(file=file, line=line, ref=e.method)
        )

        # Process the body 
        for s_ast in tree.body[0].body:
            stmt = StmtFactory(self.ctxt).build(s_ast)
            print("Stmt: %s" % stmt)

        scope.type.addExec(exec)

    def visitField(self, f):
        self._log.debug("--> visitField: %s" % f.name)
        scope : StructScope = cast(StructScope, self.ctxt.scope)

        # TODO: gather binds from fields

        data_t = TypeFactory(self.ctxt).build(f.type)

        if data_t is None:
            raise NotImplementedError(f"Unsupported type for field {f.name}")

        field : dm.TypeField = None
        if hasattr(f, "default_factory"):
            kind_m = [
                (Input, self._mkFieldInOut),
                (Output, self._mkFieldInOut),
            ]

            for kind_t, kind_f in kind_m:
                if issubclass(f.default_factory, kind_t):
                    field = kind_f(f, data_t)
                    break
        else:
            field = self.ctxt().mkTypeField(f.name, data_t)

        if field is None:
            raise NotImplementedError(f"Port {f.name} (type {f.type}) not supported")
        
        scope.type.addField(field)
        self._log.debug("<-- visitField: %s" % f.name)
        
    def _mkFieldInOut(self, f, data_t : dm.DataType) -> dm.TypeFieldInOut:
        field = self.ctxt().mkTypeFieldInOut(
            f.name,
            data_t,
            issubclass(f.default_factory, Output))
        return field
    
    def _visitExecs(self, t):
        exec_t = (
            (zdc.ExecSync, self.visitExecSync),
            (zdc.Exec, self.visitExec)
        )
        for n in dir(t):
            o = getattr(t, n)
            for et, em in exec_t:
                if isinstance(o, et):
                    em(o)
                    break

    def _visitDataType(self, t):

        if t == int:
            self.visitDataTypeInt()
        elif type(t) is type:
            zsp_base_t = (
                (zdc.Component, self.visitDataTypeComponent),
            )

            v = None
            for tt,vv in zsp_base_t:
                print("t: %s tt: %s vv: %s" % (t, tt, vv))
                if issubclass(t, tt):
                    v = vv
                    break
            
            v(t)
        else:
            raise Exception("Unknown type %s" % str(t))
        pass

    def transform(self, t : zdc.Component) -> DataTypeComponent:
        self._log.debug("--> transform: %s" % str(t))
        if self.ctxt is None:
            raise Exception()

        self.visit(t)
        result = self.ctxt.result
        self._log.debug("<-- transform: %s" % str(t))
        return cast(DataTypeComponent, result)


