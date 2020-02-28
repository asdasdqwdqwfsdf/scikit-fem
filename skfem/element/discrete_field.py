from typing import NamedTuple, Optional

import numpy as np
from numpy import ndarray


class DiscreteField(NamedTuple):
    """A function defined at the global quadrature points."""

    value: Optional[ndarray] = None
    grad: Optional[ndarray] = None
    div: Optional[ndarray] = None
    curl: Optional[ndarray] = None
    ggrad: Optional[ndarray] = None

    @property
    def f(self):
        return self.value

    @property
    def df(self):
        if self.grad is not None:
            return self.grad
        elif self.div is not None:
            return self.div
        elif self.curl is not None:
            return self.curl
        return None

    @property
    def ddf(self):
        return self.ggrad

    def __array__(self):
        return self.f

    def __mul__(self, other):
        if isinstance(other, DiscreteField):
            return self.f * other.f
        return self.f * other

    def _split(self):
        """Split all components based on their first dimension."""
        return [DiscreteField(*[f[i] for f in self if f is not None])
                for i in range(self.f.shape[0])]

    def zeros_like(self):
        def zero_or_none(x):
            if x is None:
                return None
            return np.zeros_like(x)
        return DiscreteField(*[zero_or_none(field)
                               for field in self])

    __rmul__ = __mul__
