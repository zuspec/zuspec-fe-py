
# Running Tests

The unit tests use the pytest library. You must explicitly add the src directory to PYTHONPATH:

% PYTHONPATH=$(pwd)/src ./packages/python/bin/pytest -s tests/unit

# Document learnings
As you add new features, always document new learnings here.

# Learnings about the Transformation Process

- The project transforms Python dataclasses (using `zuspec.dataclasses`) into ARL-DM data model types using `zsp_arl_dm.core`.
- The transformation is performed by a class `TransformToArlDm`, which uses a Visitor pattern (`zuspec.dataclasses.api.Visitor`) to traverse user dataclasses.
- The Visitor subclass identifies key features (e.g., components, fields) and creates corresponding ARL-DM types via the Context API (`mkDataTypeComponent`, etc.).
- The process is validated by unit tests that define user dataclasses (e.g., `MyC`) and expect ARL-DM component types to be created.
- Implementation requires mapping Python dataclass structure to ARL-DM constructs, with extensibility for fields, ports, and other features.

