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
import zuspec.dm as dm
import zuspec.dataclasses as zdc
from typing import Any, Optional
from .context import Context

@dc.dataclass
class TypeFactory(object):
    ctxt : Context = dc.field()

    def build(self, t : Any, a : Optional[Any] = None) -> dm.DataType:
        rt : dm.DataType = None
        if issubclass(t, zdc.Bit):
            width = t.W
            rt = self.ctxt().findDataTypeBit(width)

        return rt


