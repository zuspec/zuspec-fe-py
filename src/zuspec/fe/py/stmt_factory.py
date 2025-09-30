
import ast
import dataclasses as dc
import logging
import zuspec.dm as dm
from typing import cast, ClassVar, List
from .context import Context
from .expr_factory import ExprFactory

@dc.dataclass
class StmtFactory(object):
    ctxt : Context = dc.field()
    _log : ClassVar = logging.getLogger("StmtFactory")

    def build(self, s):
        stmt : dm.ExecStmt = None

        if isinstance(s, ast.If):
            stmt = self._buildStmtIf(s)
        elif isinstance(s, ast.AugAssign):
            stmt = self._buildStmtAugAssign(s)
        elif isinstance(s, ast.Assign):
            stmt = self._buildStmtAssign(s)
        return stmt
    
    def _processOrElse(self, if_clauses : List[dm.ExecStmtIf], orelse):
        self._log.debug("--> _processOrElse")
        else_scope = None
        if isinstance(orelse[0], ast.If):
            # elif
            if_s = cast(ast.If, orelse[0])
            cond = ExprFactory(self.ctxt).build(if_s.test)
            # Append to if_clauses
            if_clauses.append(self.ctxt().mkExecStmtIf(
                cond,
                self.build(if_s.body)
            ))

            if if_s.orelse is not None:
                else_scope = self._processOrElse(if_clauses, if_s.orelse)
        else:
            # else
            self._log.debug(" else")
            else_scope = self.ctxt().mkExecStmtScope()
            for s in orelse:
                else_scope.addStmt(self.build(s))
            if else_scope.numStmts == 1:
                else_scope = else_scope.getStmt(0)

        self._log.debug("<-- _processOrElse")
        return else_scope
    
    def _buildStmtIf(self, s) -> dm.ExecStmt:
        self._log.debug("--> _buildStmtIf")
        stmt : dm.ExecStmt = None
        cond = ExprFactory(self.ctxt).build(s.test)

        stmt = self.ctxt().mkExecStmtIf(
            cond,
            self.build(s.body))

        if s.orelse is not None:
            # It's nested
            if_clauses = [stmt]
            else_scope = self._processOrElse(if_clauses, s.orelse)
            stmt = self.ctxt().mkExecStmtIfElse(
                if_clauses,
                else_scope)

        self._log.debug("<-- _buildStmtIf")
        return stmt

    def _buildStmtAssign(self, s : ast.Assign):
        pass

    def _buildStmtAugAssign(self, s : ast.AugAssign):
        pass
