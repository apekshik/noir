from typing import Any, List
from noir_parser import (
    Node, Expression, Statement, Literal, Identifier, TypeAnnotation,
    BinaryOp, UnaryOp, VariableDecl, Assignment, Block, IfStatement,
    ForLoop, WhileLoop, FunctionParam, FunctionDecl, FunctionCall,
    ReturnStatement, ExpressionStmt, TypeCast, ArrayLiteral, MethodCall,
    ArrayAccess
)

class ASTPrinter:
    def __init__(self):
        self.indent_level = 0
        self.indent_size = 2

    def indent(self) -> str:
        """Return the current indentation string."""
        return " " * (self.indent_level * self.indent_size)

    def print_ast(self, node: Node) -> str:
        """Print an AST node and its children."""
        if node is None:
            return f"{self.indent()}<invalid statement: parsing error>"
        method_name = f"print_{type(node).__name__.lower()}"
        printer = getattr(self, method_name, self.print_unknown)
        return printer(node)

    def print_unknown(self, node: Node) -> str:
        """Handle unknown node types."""
        return f"{self.indent()}<unknown node type: {type(node).__name__}>"

    def print_block(self, node: Block) -> str:
        """Print a block of statements."""
        self.indent_level += 1
        statements = "\n".join(self.print_ast(stmt) for stmt in node.statements)
        self.indent_level -= 1
        return statements

    def print_literal(self, node: Literal) -> str:
        """Print a literal value."""
        return f"{self.indent()}{node.type.name}({repr(node.value)})"

    def print_identifier(self, node: Identifier) -> str:
        """Print an identifier."""
        return f"{self.indent()}IDENTIFIER({node.name})"

    def print_typeannotation(self, node: TypeAnnotation) -> str:
        """Print a type annotation."""
        if node.parameters:
            params = ", ".join(self.print_ast(param) for param in node.parameters)
            return f"{self.indent()}TYPE({node.name}<{params}>)"
        return f"{self.indent()}TYPE({node.name})"

    def print_binaryop(self, node: BinaryOp) -> str:
        """Print a binary operation."""
        return (
            f"{self.indent()}BINARY_OP({node.operator.type.name})\n"
            f"{self.print_ast(node.left)}\n"
            f"{self.print_ast(node.right)}"
        )

    def print_unaryop(self, node: UnaryOp) -> str:
        """Print a unary operation."""
        return (
            f"{self.indent()}UNARY_OP({node.operator.type.name})\n"
            f"{self.print_ast(node.operand)}"
        )

    def print_variabledecl(self, node: VariableDecl) -> str:
        """Print a variable declaration."""
        result = [
            f"{self.indent()}VARIABLE_DECLARATION",
            self.print_ast(node.name),
            self.print_ast(node.type_annotation)
        ]
        if node.initializer:
            result.append(self.print_ast(node.initializer))
        return "\n".join(result)

    def print_assignment(self, node: Assignment) -> str:
        """Print an assignment."""
        return (
            f"{self.indent()}ASSIGNMENT\n"
            f"{self.print_ast(node.target)}\n"
            f"{self.print_ast(node.value)}"
        )

    def print_ifstatement(self, node: IfStatement) -> str:
        """Print an if statement."""
        result = [
            f"{self.indent()}IF_STATEMENT",
            f"{self.indent()}CONDITION:",
            self.print_ast(node.condition),
            f"{self.indent()}THEN:",
            self.print_ast(node.then_branch)
        ]
        
        for condition, block in node.elif_branches:
            result.extend([
                f"{self.indent()}ELIF_CONDITION:",
                self.print_ast(condition),
                f"{self.indent()}ELIF_BODY:",
                self.print_ast(block)
            ])
            
        if node.else_branch:
            result.extend([
                f"{self.indent()}ELSE:",
                self.print_ast(node.else_branch)
            ])
        return "\n".join(result)

    def print_forloop(self, node: ForLoop) -> str:
        """Print a for loop."""
        return (
            f"{self.indent()}FOR_LOOP\n"
            f"{self.print_ast(node.iterator)}\n"
            f"{self.indent()}FROM:\n"
            f"{self.print_ast(node.start)}\n"
            f"{self.indent()}{'THROUGH' if node.is_inclusive else 'TO'}:\n"
            f"{self.print_ast(node.end)}\n"
            f"{self.indent()}STEP:\n"
            f"{self.print_ast(node.step) if node.step else self.indent() + 'DEFAULT'}\n"
            f"{self.indent()}BODY:\n"
            f"{self.print_ast(node.body)}"
        )

    def print_whileloop(self, node: WhileLoop) -> str:
        """Print a while loop."""
        return (
            f"{self.indent()}WHILE_LOOP\n"
            f"{self.indent()}CONDITION:\n"
            f"{self.print_ast(node.condition)}\n"
            f"{self.indent()}BODY:\n"
            f"{self.print_ast(node.body)}"
        )

    def print_functionparam(self, node: FunctionParam) -> str:
        """Print a function parameter."""
        return (
            f"{self.indent()}PARAMETER\n"
            f"{self.print_ast(node.name)}\n"
            f"{self.print_ast(node.type_annotation)}"
        )

    def print_functiondecl(self, node: FunctionDecl) -> str:
        """Print a function declaration."""
        result = [
            f"{self.indent()}FUNCTION_DECLARATION",
            self.print_ast(node.name),
            f"{self.indent()}PARAMETERS:"
        ]
        
        for param in node.params:
            result.append(self.print_ast(param))
            
        if node.return_type:
            result.extend([
                f"{self.indent()}RETURN_TYPE:",
                self.print_ast(node.return_type)
            ])
            
        result.extend([
            f"{self.indent()}BODY:",
            self.print_ast(node.body)
        ])
        return "\n".join(result)

    def print_functioncall(self, node: FunctionCall) -> str:
        """Print a function call."""
        result = [
            f"{self.indent()}FUNCTION_CALL",
            self.print_ast(node.callee),
            f"{self.indent()}ARGUMENTS:"
        ]
        
        for arg in node.arguments:
            result.append(self.print_ast(arg))
        return "\n".join(result)

    def print_returnstatement(self, node: ReturnStatement) -> str:
        """Print a return statement."""
        result = [f"{self.indent()}RETURN"]
        if node.value:
            result.append(self.print_ast(node.value))
        return "\n".join(result)

    def print_expressionstmt(self, node: ExpressionStmt) -> str:
        """Print an expression statement."""
        return (
            f"{self.indent()}EXPRESSION_STATEMENT\n"
            f"{self.print_ast(node.expression)}"
        )

    def print_typecast(self, node: TypeCast) -> str:
        """Print a type cast."""
        return (
            f"{self.indent()}TYPE_CAST\n"
            f"{self.print_ast(node.expression)}\n"
            f"{self.indent()}TO:\n"
            f"{self.print_ast(node.target_type)}"
        )

    def print_arrayliteral(self, node: ArrayLiteral) -> str:
        """Print an array literal."""
        result = [f"{self.indent()}ARRAY_LITERAL"]
        self.indent_level += 1
        for element in node.elements:
            result.append(self.print_ast(element))
        self.indent_level -= 1
        return "\n".join(result)

    def print_methodcall(self, node: MethodCall) -> str:
        """Print a method call."""
        result = [
            f"{self.indent()}METHOD_CALL",
            f"{self.indent()}OBJECT:",
            self.print_ast(node.object),
            f"{self.indent()}METHOD:",
            self.print_ast(node.method),
            f"{self.indent()}ARGUMENTS:"
        ]
        self.indent_level += 1
        for arg in node.arguments:
            result.append(self.print_ast(arg))
        self.indent_level -= 1
        return "\n".join(result)

    def print_arrayaccess(self, node: ArrayAccess) -> str:
        """Print an array access."""
        return (
            f"{self.indent()}ARRAY_ACCESS\n"
            f"{self.indent()}ARRAY:\n"
            f"{self.print_ast(node.array)}\n"
            f"{self.indent()}INDEX:\n"
            f"{self.print_ast(node.index)}"
        )

def print_ast(ast: List[Statement]) -> str:
    """Convenience function to print an entire AST."""
    printer = ASTPrinter()
    return "\n".join(printer.print_ast(node) for node in ast)

# Example usage
if __name__ == "__main__":
    from noir_lexer import lex
    from noir_parser import Parser
    
    source_code = """
    x: Int = 42
    if x > 0:
        print("Positive")
    :: else:
        print("Non-positive")
    ::
    
    for i in 0 to 10:
        if i % 2 == 0:
            print(i, "is even")
        :: else:
            print(i, "is odd")
        ::
    ::
    """
    
    try:
        tokens = lex(source_code)
        parser = Parser(tokens)
        ast = parser.parse()
        print(print_ast(ast))
    except Exception as e:
        print(f"Error: {e}")