import zuspec.dataclasses as zdc
from zuspec.fe.py.transform_to_dm import TransformToDm, Context
from zuspec.dm import TypeFieldInOut

def test_smoke():

    @zdc.dataclass
    class MyC(zdc.Component):
        pass

    import zuspec.dm.impl as dm_impl
    ctxt = Context(dm_impl.Context())

    # Apply the transform
    comp_dm = TransformToDm(ctxt=ctxt).transform(MyC)

    assert comp_dm is not None
    assert comp_dm.name == MyC.__qualname__
    assert ctxt.findDataTypeStruct(MyC.__qualname__) is comp_dm

#    assert arl_comp is not None
#    assert arl_comp.name() == "MyC"


def test_ports():

    @zdc.dataclass
    class MyC(zdc.Component):
        clock : zdc.Bit = zdc.input()
        reset : zdc.Bit = zdc.input()
        pass

    import zuspec.dm.impl as dm_impl
    ctxt = Context(ctxt=dm_impl.Context())

    # Apply the transform
    dm_comp = TransformToDm(ctxt=ctxt).transform(MyC)

    assert dm_comp is not None
    assert dm_comp.name == MyC.__qualname__

    assert dm_comp.numFields() == 2

    # Check for correct number of fields and presence of 'clock' and 'reset'
    fields = list(dm_comp.fields)
    for f in dm_comp.fields:
        assert isinstance(f, TypeFieldInOut)
        assert not f.isOutput

    assert len(fields) == 2
    field_names = [f.name for f in fields]
    assert "clock" in field_names
    assert "reset" in field_names

def test_inout_ports():

    @zdc.dataclass
    class MyC(zdc.Component):
        a : zdc.Bit = zdc.input()
        b : zdc.Bit = zdc.output()

    from zsp_arl_dm.core import Factory, Context, TypeFieldInOut
    ctxt = Factory.inst().mkContext()
    t = MyC()
    arl_comp = TransformToArlDm(ctxt).transform(t)
    assert arl_comp is not None
    fields = list(arl_comp.getFields())
    assert len(fields) == 2
    names = [f.name() for f in fields]
    assert "a" in names
    assert "b" in names
    for f in fields:
        if f.name() == "a":
            assert isinstance(f, TypeFieldInOut)
            assert f.isInput() is True
        elif f.name() == "b":
            assert isinstance(f, TypeFieldInOut)
            assert f.isInput() is False

def test_ports_visitor():
    """
    Variant of test_ports that uses a Visitor subclass to collect and verify
    the component's ports. The base Visitor does not currently traverse struct/
    component fields (visitDataTypeStruct is pass). Additionally, the duplicate
    visitTypeField definition in visitor.py would cause recursion if we tried
    per-field accept traversal. We therefore collect fields directly in the
    overridden visitDataTypeComponent.
    """
    @zdc.dataclass
    class MyC(zdc.Component):
        clock: zdc.Bit = zdc.input()
        reset: zdc.Bit = zdc.input()
        pass

    import zuspec.dm.impl as dm_impl
    from zuspec.dm.visitor import Visitor
    ctxt = Context(ctxt=dm_impl.Context())
    dm_comp = TransformToDm(ctxt=ctxt).transform(MyC)

    class CollectPortsVisitor(Visitor):
        def __init__(self):
            self.fields = []
        def visitDataTypeComponent(self, obj):
            # Directly collect fields; no recursive field.accept calls
            for f in obj.fields:
                self.fields.append(f)

    v = CollectPortsVisitor()
    dm_comp.accept(v)

    assert len(v.fields) == 2
    names = {f.name for f in v.fields}
    assert names == {"clock", "reset"}
    for f in v.fields:
        assert isinstance(f, TypeFieldInOut)
        assert not f.isOutput
