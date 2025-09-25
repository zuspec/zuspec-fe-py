import dataclasses as dc
import zuspec.dataclasses as zdc
from zuspec.dataclasses.api.visitor import Visitor
from zuspec.dataclasses.ports import Input, Output
from zuspec.dm import (
    Context, DataTypeComponent
)

@dc.dataclass
class TransformToDm(object):
    ctxt : Context

    class _Visitor(Visitor):
        def __init__(self, ctxt):
            super().__init__()
            self.ctxt = ctxt
            self.comp = None

        def visitComponentType(self, t):
            # Always work with the class, not the instance
            t_cls = t if isinstance(t, type) else type(t)
            name = t_cls.__qualname__
            self.comp = self.ctxt.mkDataTypeComponent(name)
            self.ctxt.addDataTypeStruct(self.comp)

            # Call base Visitor logic to ensure visitExec is called
            super().visitComponentType(t)

            # Explicitly call visitExec for @sync methods
            from zuspec.dataclasses.annotation import AnnotationSync
            for attr_name in dir(t_cls):
                attr = getattr(t_cls, attr_name)
                if hasattr(attr, "__zsp_annotation__") and isinstance(getattr(attr, "__zsp_annotation__"), AnnotationSync):
                    self.visitExec(attr)

        def visitExec(self, m):
            # Called for methods decorated with @zdc.sync
            import inspect
            import ast
            from zsp_arl_dm.core import ExecKindT

            import textwrap
            src = inspect.getsource(m)
            src = textwrap.dedent(src)
            tree = ast.parse(src)

            body = self.ctxt.mkTypeProcStmtScope()

            def _proc_expr(expr):
                # Recursively convert Python AST expressions to vsc_dm.core expressions
                if isinstance(expr, ast.BinOp):
                    op_map = {
                        ast.Add: vsc_dm.BinOp.Add,
                        ast.Sub: vsc_dm.BinOp.Sub,
                        ast.Mult: vsc_dm.BinOp.Mul,
                        ast.Div: vsc_dm.BinOp.Div,
                        ast.Mod: vsc_dm.BinOp.Mod,
                        ast.BitAnd: vsc_dm.BinOp.BinAnd,
                        ast.BitOr: vsc_dm.BinOp.BinOr,
                        ast.BitXor: vsc_dm.BinOp.BinXor,
                        ast.LShift: vsc_dm.BinOp.Sll,
                        ast.RShift: vsc_dm.BinOp.Srl,
                        ast.Eq: vsc_dm.BinOp.Eq,
                        ast.NotEq: vsc_dm.BinOp.Ne,
                        ast.Lt: vsc_dm.BinOp.Lt,
                        ast.LtE: vsc_dm.BinOp.Le,
                        ast.Gt: vsc_dm.BinOp.Gt,
                        ast.GtE: vsc_dm.BinOp.Ge,
                        ast.And: vsc_dm.BinOp.LogAnd,
                        ast.Or: vsc_dm.BinOp.LogOr,
                    }
                    lhs = _proc_expr(expr.left)
                    rhs = _proc_expr(expr.right)
                    op = op_map.get(type(expr.op))
                    if op is None:
                        raise NotImplementedError(f"Unsupported BinOp: {type(expr.op)}")
                    return self.ctxt.mkModelExprBin(lhs, op, rhs)
                elif isinstance(expr, ast.UnaryOp):
                    op_map = {
                        ast.Not: vsc_dm.UnaryOp.Not,
                        # Add more as needed
                    }
                    operand = _proc_expr(expr.operand)
                    op = op_map.get(type(expr.op))
                    if op is None:
                        raise NotImplementedError(f"Unsupported UnaryOp: {type(expr.op)}")
                    return self.ctxt.mkModelExprUnary(op, operand, False)
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
                    return self.ctxt.mkModelExprFieldRef(model_field)
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
                        return self.ctxt.mkModelExprFieldRef(model_field)
                    raise NotImplementedError("Only 'self.<field>' attribute access is supported")
                elif isinstance(expr, ast.Constant):
                    # Only handle integer constants for now
                    if isinstance(expr.value, int):
                        return self.ctxt.mkModelExprVal(self.ctxt.mkValRefInt(expr.value, True, 32))
                    else:
                        raise NotImplementedError(f"Unsupported constant type: {type(expr.value)}")
                else:
                    raise NotImplementedError(f"Unsupported AST expr: {type(expr)}")

            def _proc_stmt(node):
                stmts = []
                if isinstance(node, ast.If):
                    cond_expr = _proc_expr(node.test)
                    body_scope = self.ctxt.mkTypeProcStmtScope()
                    for stmt in node.body:
                        for s in _proc_stmt(stmt):
                            body_scope.addStatement(s)
                    if_clauses = [self.ctxt.mkTypeProcStmtIfClause(cond_expr, body_scope)]
                    else_scope = self.ctxt.mkTypeProcStmtScope()
                    for stmt in node.orelse:
                        for s in _proc_stmt(stmt):
                            else_scope.addStatement(s)
                    if_stmt = self.ctxt.mkTypeProcStmtIfElse(if_clauses, else_scope)
                    stmts.append(if_stmt)
                # TODO: handle other statement types (assign, expr, etc.)
                return stmts

            # Traverse AST and add statements to body
            for stmt in tree.body[0].body:
                for s in _proc_stmt(stmt):
                    body.addStatement(s)

            exec_proc = self.ctxt.mkTypeExecProc(ExecKindT.Body, body)
            self.comp.addExec(exec_proc)

        def visitField(self, f):
            # Detect port fields (Input/Output)
            if hasattr(f, "default_factory"):
                if f.default_factory is Input:
                    # Input port
                    arl_type = None
                    # Only handle zdc.Bit for now
                    if f.type is zdc.Bit:
                        arl_type = self.ctxt.findDataTypeBit(1)
                    else:
                        raise NotImplementedError(f"Port type {f.type} not supported")
                    port_field = self.ctxt.mkTypeFieldInOut(f.name, arl_type, False)
                    self.comp.addField(port_field)
                    return
                elif f.default_factory is Output:
                    # Output port
                    arl_type = None
                    if f.type is zdc.Bit:
                        arl_type = self.ctxt.findDataTypeBit(False, 1)
                    else:
                        raise NotImplementedError(f"Port type {f.type} not supported")
                    port_field = self.ctxt.mkTypeFieldInOut(f.name, arl_type, True)
                    self.comp.addField(port_field)
                    return
            else:
                # Fallback for non-port fields (future logic)
                raise Exception("Unsupported field %s" % f.name)

    def transform(self, t : zdc.Component) -> DataTypeComponent:
        visitor = self._Visitor(self.ctxt)
        visitor.visit(t)
        return visitor.comp
