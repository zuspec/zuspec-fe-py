import pytest
import zsp_arl_dm.core as arl
import vsc_dm.core as vsc

def test_mkTypeProcStmtAssign():
    ctxt = arl.Factory.inst().mkContext()
    lhs = vsc.TypeExpr.mkVarRef("lhs")
    rhs = vsc.TypeExpr.mkVarRef("rhs")
    stmt = ctxt.mkTypeProcStmtAssign(lhs, 0, rhs)
    assert stmt is not None
    assert stmt.getLhs().name() == "lhs"
    assert stmt.getRhs().name() == "rhs"

def test_mkTypeProcStmtBreak():
    ctxt = arl.Factory.inst().mkContext()
    stmt = ctxt.mkTypeProcStmtBreak()
    assert stmt is not None

def test_mkTypeProcStmtContinue():
    ctxt = arl.Factory.inst().mkContext()
    stmt = ctxt.mkTypeProcStmtContinue()
    assert stmt is not None

def test_mkTypeProcStmtExpr():
    ctxt = arl.Factory.inst().mkContext()
    expr = vsc.TypeExpr.mkVarRef("e")
    stmt = ctxt.mkTypeProcStmtExpr(expr)
    assert stmt is not None
    assert stmt.getExpr().name() == "e"

def test_mkTypeProcStmtYield():
    ctxt = arl.Factory.inst().mkContext()
    stmt = ctxt.mkTypeProcStmtYield()
    assert stmt is not None
