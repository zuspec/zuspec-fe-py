import dataclasses as dc
import zuspec.dataclasses as zdc
from zsp_arl_dm.core import DataTypeComponent, Context
from zuspec.dataclasses.api.visitor import Visitor
from zuspec.dataclasses.ports import Input, Output
import vsc_dm.core as vsc_dm

@dc.dataclass
class TransformToArlDm(object):
    ctxt : Context

    class _Visitor(Visitor):
        def __init__(self, ctxt):
            super().__init__()
            self.ctxt = ctxt
            self.comp = None

        def visitComponentType(self, t):
            # Create ARL-DM component type using the class name
            name = t.__name__
            self.comp = self.ctxt.mkDataTypeComponent(name)
            self.ctxt.addDataTypeStruct(self.comp)

            # Traverse fields and methods as per base Visitor
            self.visitStructType(t)

        def visitField(self, f):
            # Detect port fields (Input/Output)
            if hasattr(f, "default_factory"):
                if f.default_factory is Input:
                    # Input port
                    arl_type = None
                    # Only handle zdc.Bit for now
                    if f.type is zdc.Bit:
                        arl_type = self.ctxt.findDataTypeInt(False, 1)
                    else:
                        raise NotImplementedError(f"Port type {f.type} not supported")
                    port_field = self.ctxt.mkTypeFieldInOut(f.name, arl_type, True)
                    self.comp.addField(port_field)
                    return
                elif f.default_factory is Output:
                    # Output port
                    arl_type = None
                    if f.type is zdc.Bit:
                        arl_type = self.ctxt.findDataTypeInt(False, 1)
                    else:
                        raise NotImplementedError(f"Port type {f.type} not supported")
                    port_field = self.ctxt.mkTypeFieldInOut(f.name, arl_type, False)
                    self.comp.addField(port_field)
                    return
            # Fallback for non-port fields (future logic)
            pass

    def transform(self, t : zdc.Component) -> DataTypeComponent:
        visitor = self._Visitor(self.ctxt)
        visitor.visit(type(t))
        return visitor.comp
