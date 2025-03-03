from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Any
from enum import Enum, auto
from noir_lexer import Token, TokenType
from noir_types import TypeAnnotation, TypeParameter, TypeKind, TypeConstraint

# AST Node definitions
@dataclass
class Node:
    pass

@dataclass
class Expression(Node):
    pass

@dataclass
class Statement(Node):
    pass

@dataclass
class Literal(Expression):
    value: Any
    type: TokenType

@dataclass
class Identifier(Expression):
    name: str

@dataclass
class BinaryOp(Expression):
    left: Expression
    operator: Token
    right: Expression

@dataclass
class UnaryOp(Expression):
    operator: Token
    operand: Expression
    
@dataclass
class VariableDecl(Statement):
    name: Identifier
    type_annotation: TypeAnnotation
    initializer: Optional[Expression]

@dataclass
class Assignment(Statement):
    target: Identifier
    value: Expression

@dataclass
class Block(Statement):
    statements: List[Statement]

@dataclass
class IfStatement(Statement):
    condition: Expression
    then_branch: Block
    elif_branches: List[tuple[Expression, Block]]
    else_branch: Optional[Block]

@dataclass
class ForLoop(Statement):
    iterator: Identifier
    start: Expression
    end: Expression
    step: Optional[Expression]
    body: Block
    is_inclusive: bool  # True for 'thru', False for 'to'

@dataclass
class WhileLoop(Statement):
    condition: Expression
    body: Block

@dataclass
class FunctionParam(Node):
    name: Identifier
    type_annotation: TypeAnnotation

@dataclass
class FunctionDecl(Statement):
    name: Identifier
    params: List[FunctionParam]
    return_type: Optional[TypeAnnotation]
    body: Block

@dataclass
class FunctionCall(Expression):
    callee: Identifier
    arguments: List[Expression]

@dataclass
class ReturnStatement(Statement):
    value: Optional[Expression]

@dataclass
class ExpressionStmt(Statement):
    expression: Expression

@dataclass
class TypeCast(Expression):
    expression: Expression
    target_type: TypeAnnotation

@dataclass
class ArrayLiteral(Expression):
    elements: List[Expression]

@dataclass
class MethodCall(Expression):
    object: Identifier
    method: Identifier
    arguments: List[Expression]

@dataclass
class ArrayAccess(Expression):
    array: Expression
    index: Expression

# New Enum support
@dataclass
class EnumVariant(Node):
    name: Identifier
    
@dataclass
class EnumDeclaration(Statement):
    name: Identifier
    variants: List[EnumVariant]
    protocol_conformance: Optional[Identifier] = None  # For protocol conformance with <- or 'conforms'

# New Protocol support
@dataclass
class ProtocolProperty(Node):
    name: Identifier
    type_annotation: TypeAnnotation

@dataclass
class ProtocolMethod(Node):
    name: Identifier
    params: List[FunctionParam]
    return_type: Optional[TypeAnnotation]

@dataclass
class ProtocolDeclaration(Statement):
    name: Identifier
    properties: List[ProtocolProperty]
    methods: List[ProtocolMethod]

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