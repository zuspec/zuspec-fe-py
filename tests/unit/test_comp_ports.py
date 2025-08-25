import zuspec.dataclasses as zdc
from zuspec.py.transform_to_arl_dm import TransformToArlDm

def test_smoke():

    @zdc.dataclass
    class MyC(zdc.Component):
        pass

    # Create a dummy ARL-DM context
    from zsp_arl_dm.core import Factory, Context
    ctxt = Factory.inst().mkContext()
    # Apply the transform
    t = MyC()
    arl_comp = TransformToArlDm(ctxt).transform(t)
    # Register the component with the context before accessing properties
#    ctxt.addDataTypeStruct(arl_comp)
    # Check that the ARL-DM component type was created and has the correct name
    assert arl_comp is not None
    assert arl_comp.name() == "MyC"


def test_ports():

    @zdc.dataclass
    class MyC(zdc.Component):
        clock : zdc.Bit = zdc.input()
        reset : zdc.Bit = zdc.input()
        pass

    # Create a dummy ARL-DM context
    from zsp_arl_dm.core import Factory, Context
    ctxt = Factory.inst().mkContext()
    # Apply the transform
    t = MyC()
    arl_comp = TransformToArlDm(ctxt).transform(t)
    # Register the component with the context before accessing properties
#    ctxt.addDataTypeStruct(arl_comp)
    # Check that the ARL-DM component type was created and has the correct name
    assert arl_comp is not None
    assert arl_comp.name() == "MyC"
    # Check for correct number of fields and presence of 'clock' and 'reset'
    fields = list(arl_comp.getFields())
    assert len(fields) == 2
    field_names = [f.name() for f in fields]
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
