
import pytest
import zuspec.dataclasses as zdc
import zuspec.dm as dm
from zuspec.fe.py import Context, TransformToDm

def test_smoke():

    @zdc.dataclass
    class MyC(zdc.Component):
        clock : zdc.Bit = zdc.input()
        reset : zdc.Bit = zdc.input()
        count : zdc.Bit[32] = zdc.output()

        @zdc.sync(clock=lambda s:s.clock, reset=lambda s:s.reset)
        def abc(self):
            if self.reset:
                self.count = 0
            else:
                self.count += 1

    dm_ctxt = dm.impl.Context()
    ctxt = Context(ctxt=dm_ctxt)

    # Apply the transform
    comp_dm = TransformToDm(ctxt=ctxt).transform(MyC)

    assert comp_dm is not None
    assert comp_dm.name == MyC.__qualname__
    assert comp_dm.numExecs == 1
    exec = comp_dm.getExec(0)
    assert hasattr(exec, "clock")
    assert hasattr(exec, "reset")
    assert exec.clock is not None
    assert exec.reset is not None
#    exec = execs[0]
#    body = exec.getBody()
#    assert len(body.getStatements()) == 1

def test_visit_type_exec_proc():
    from zsp_arl_dm.core import VisitorBase, Factory, ExecKindT
    from zuspec.fe.py.transform_to_arl_dm import TransformToArlDm

    @zdc.dataclass
    class MyC(zdc.Component):
        clock : zdc.Bit = zdc.input()
        reset : zdc.Bit = zdc.input()
        @zdc.sync(clock=lambda s: s.clock, reset=lambda s:s.reset)
        def abc(self):
            if self.reset:
                pass
            else:
                pass

    ctxt = Factory.inst().mkContext()
    arl_comp = TransformToArlDm(ctxt).transform(MyC)
    execs = arl_comp.getExecs(ExecKindT.Body)
    assert execs, "No execs found"
    exec_proc = execs[0]

    called = {}
    class MyVisitor(VisitorBase):
        def visitTypeExecProc(self, t):
            called["hit"] = True
            super().visitTypeExecProc(t)

    visitor = MyVisitor()
    exec_proc.accept(visitor)
    assert called.get("hit"), "visitTypeExecProc was not called"

def test_visitor_ast_statement_dispatch():
    import zuspec.dataclasses.api.visitor as visitor_mod
    import ast

    visited = []

    class TestVisitor(visitor_mod.Visitor):
        def visit_If(self, stmt: ast.If):
            visited.append("If")
            return super().visit_If(stmt)
        def visit_Expr(self, stmt: ast.Expr):
            visited.append("Expr")
            return super().visit_Expr(stmt)
        def visit_Assign(self, stmt: ast.Assign):
            visited.append("Assign")
            return super().visit_Assign(stmt)

    @zdc.dataclass
    class MyC(zdc.Component):
        clock : zdc.Bit = zdc.input()
        reset : zdc.Bit = zdc.input()
        @zdc.sync(clock=lambda s: s.clock, reset=lambda s:s.reset)
        def abc(self):
            if self.reset:
                x = 1
            else:
                y = 2

    v = TestVisitor()
    v.visitStructType(MyC)
    assert "If" in visited
    assert "Assign" in visited

def test_expr_binop():
    import zuspec.dataclasses as zdc
    from zuspec.fe.py.transform_to_arl_dm import TransformToArlDm
    from zsp_arl_dm.core import Factory, ExecKindT

    @zdc.dataclass
    class MyC(zdc.Component):
        a : zdc.Bit = zdc.input()
        b : zdc.Bit = zdc.input()
        x : zdc.Bit = zdc.output()

        @zdc.sync(clock=lambda s: s.a, reset=lambda s: s.b)
        def abc(self):
            if self.b:
                self.x = self.a + self.b
            else:
                self.x = self.a - self.b

    ctxt = Factory.inst().mkContext()
    arl_comp = TransformToArlDm(ctxt).transform(MyC)
    execs = arl_comp.getExecs(ExecKindT.Body)
    assert execs, "No execs found"
    exec_proc = execs[0]
    body = exec_proc.getBody()
    stmts = body.getStatements()
    assert len(stmts) == 1

def test_expr_unaryop():
    import zuspec.dataclasses as zdc
    from zuspec.fe.py.transform_to_arl_dm import TransformToArlDm
    from zsp_arl_dm.core import Factory, ExecKindT

    @zdc.dataclass
    class MyC(zdc.Component):
        a : zdc.Bit = zdc.input()
        x : zdc.Bit = zdc.output()

        @zdc.sync(clock=lambda s: s.a, reset=lambda s: s.a)
        def abc(self):
            if not self.a:
                self.x = 1
            else:
                self.x = 0

    ctxt = Factory.inst().mkContext()
    arl_comp = TransformToArlDm(ctxt).transform(MyC)
    execs = arl_comp.getExecs(ExecKindT.Body)
    assert execs, "No execs found"
    exec_proc = execs[0]
    body = exec_proc.getBody()
    stmts = body.getStatements()
    assert len(stmts) == 1

def test_expr_constant():
    import zuspec.dataclasses as zdc
    from zuspec.fe.py.transform_to_arl_dm import TransformToArlDm
    from zsp_arl_dm.core import Factory, ExecKindT

    @zdc.dataclass
    class MyC(zdc.Component):
        x : zdc.Bit = zdc.output()

        @zdc.sync(clock=lambda s: s.x, reset=lambda s: s.x)
        def abc(self):
            if 1:
                self.x = 42
            else:
                self.x = 0

    ctxt = Factory.inst().mkContext()
    arl_comp = TransformToArlDm(ctxt).transform(MyC)
    execs = arl_comp.getExecs(ExecKindT.Body)
    assert execs, "No execs found"
    exec_proc = execs[0]
    body = exec_proc.getBody()
    stmts = body.getStatements()
    assert len(stmts) == 1
