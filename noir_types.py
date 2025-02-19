from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Any
from enum import Enum, auto

class TypeKind(Enum):
    """Kinds of types in the type system."""
    PRIMITIVE = auto()  # Int, Float, String, etc.
    GENERIC = auto()    # Set<T>, Array<T>, etc.
    PARAMETER = auto()  # T in Set<T>
    INSTANTIATED = auto()  # Set<Int>, Array<String>, etc.

@dataclass
class TypeConstraint:
    """Represents constraints on type parameters."""
    kind: str  # 'subtype', 'supertype', 'equals'
    type_name: str

@dataclass
class TypeParameter:
    """Represents a type parameter in a generic type."""
    name: str
    constraints: List[TypeConstraint] = None
    
    def __init__(self, name: str, constraints: List[TypeConstraint] = None):
        self.name = name
        self.constraints = constraints or []

    def is_satisfied_by(self, type_annotation: 'TypeAnnotation', type_checker: Any) -> bool:
        """Check if a type satisfies this parameter's constraints."""
        for constraint in self.constraints:
            if constraint.kind == 'subtype':
                if not type_checker.is_subtype(type_annotation.name, constraint.type_name):
                    return False
            elif constraint.kind == 'supertype':
                if not type_checker.is_subtype(constraint.type_name, type_annotation.name):
                    return False
            elif constraint.kind == 'equals':
                if type_annotation.name != constraint.type_name:
                    return False
        return True

@dataclass
class TypeAnnotation:
    """Represents a type in the type system."""
    name: str
    parameters: Optional[List[Union['TypeAnnotation', TypeParameter]]] = None
    kind: TypeKind = TypeKind.PRIMITIVE
    
    def __post_init__(self):
        # Determine the kind of type if not explicitly set
        if self.parameters:
            if any(isinstance(p, TypeParameter) for p in self.parameters):
                self.kind = TypeKind.GENERIC
            else:
                self.kind = TypeKind.INSTANTIATED
        elif self.name.isupper() and len(self.name) == 1:  # e.g., 'T', 'U'
            self.kind = TypeKind.PARAMETER

    def is_generic(self) -> bool:
        """Check if this is a generic type."""
        return self.kind == TypeKind.GENERIC

    def is_instantiated(self) -> bool:
        """Check if this is an instantiated generic type."""
        return self.kind == TypeKind.INSTANTIATED

    def is_primitive(self) -> bool:
        """Check if this is a primitive type."""
        return self.kind == TypeKind.PRIMITIVE

    def instantiate(self, type_args: List['TypeAnnotation']) -> 'TypeAnnotation':
        """Create an instantiated version of this generic type."""
        if not self.is_generic():
            raise TypeError(f"Cannot instantiate non-generic type {self.name}")
        if len(type_args) != len(self.parameters):
            raise TypeError(f"Wrong number of type arguments for {self.name}")
        
        return TypeAnnotation(
            name=self.name,
            parameters=type_args,
            kind=TypeKind.INSTANTIATED
        )

    def substitute(self, type_params: Dict[str, 'TypeAnnotation']) -> 'TypeAnnotation':
        """Substitute type parameters with concrete types."""
        if self.kind == TypeKind.PARAMETER:
            return type_params.get(self.name, self)
        elif self.parameters:
            new_params = [
                param.substitute(type_params) if isinstance(param, TypeAnnotation)
                else param for param in self.parameters
            ]
            return TypeAnnotation(self.name, new_params, self.kind)
        return self

# Example generic type definitions
LIST_TYPE = TypeAnnotation(
    name="List",
    parameters=[TypeParameter("T")],
    kind=TypeKind.GENERIC
)

SET_TYPE = TypeAnnotation(
    name="Set",
    parameters=[TypeParameter("T")],
    kind=TypeKind.GENERIC
)

ORDERED_SET_TYPE = TypeAnnotation(
    name="OSet",
    parameters=[TypeParameter("T")],
    kind=TypeKind.GENERIC
)

DICTIONARY_TYPE = TypeAnnotation(
    name="Dict",
    parameters=[
        TypeParameter("K"),
        TypeParameter("V")
    ],
    kind=TypeKind.GENERIC
) 