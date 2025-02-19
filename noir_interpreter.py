from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from noir_parser import (
    Node, Expression, Statement, Literal, Identifier, BinaryOp,
    UnaryOp, VariableDecl, Assignment, Block, IfStatement,
    WhileLoop, ForLoop, FunctionDecl, FunctionCall, ReturnStatement,
    ExpressionStmt, TypeCast, ArrayLiteral, MethodCall, ArrayAccess
)
from noir_lexer import TokenType
from noir_type_checker import TypeChecker, TypeError
from noir_types import TypeKind, TypeAnnotation

class InterpreterError(Exception):
    """Base class for interpreter errors."""
    pass

class RuntimeError(InterpreterError):
    """Error that occurs during program execution."""
    pass

@dataclass
class Environment:
    """Represents a scope for variable bindings."""
    values: Dict[str, Any]
    types: Dict[str, str]  # Store variable types
    parent: Optional['Environment'] = None

    def __init__(self, values: Dict[str, Any] = None, types: Dict[str, str] = None, parent: Optional['Environment'] = None):
        self.values = values if values is not None else {}
        self.types = types if types is not None else {}
        self.parent = parent

    def define(self, name: str, value: Any, type_name: str) -> None:
        """Define a new variable in the current scope."""
        self.values[name] = value
        self.types[name] = type_name

    def assign(self, name: str, value: Any) -> None:
        """Assign a value to an existing variable."""
        env = self.resolve(name)
        if env:
            # Type check the assignment
            value_type = TypeChecker.get_type_name(value)
            target_type = TypeAnnotation(env.types[name], kind=TypeKind.PRIMITIVE)
            value_type_annotation = TypeAnnotation(value_type, kind=TypeKind.PRIMITIVE)
            type_checker = TypeChecker()
            try:
                converted_value = type_checker.validate_assignment(target_type, value, value_type_annotation)
                env.values[name] = converted_value
            except TypeError as e:
                raise RuntimeError(str(e))
        else:
            raise RuntimeError(f"Undefined variable '{name}'")

    def get(self, name: str) -> Any:
        """Get the value of a variable."""
        env = self.resolve(name)
        if env:
            return env.values[name]
        raise RuntimeError(f"Undefined variable '{name}'")

    def get_type(self, name: str) -> str:
        """Get the type of a variable."""
        env = self.resolve(name)
        if env:
            return env.types[name]
        raise RuntimeError(f"Undefined variable '{name}'")

    def resolve(self, name: str) -> Optional['Environment']:
        """Find the environment where a variable is defined."""
        if name in self.values:
            return self
        if self.parent:
            return self.parent.resolve(name)
        return None

class Interpreter:
    def __init__(self):
        self.environment = Environment()
        # Built-in functions
        self.environment.define("print", print, "Function")

    def interpret(self, statements: List[Statement]) -> None:
        """Interpret a list of statements."""
        try:
            for statement in statements:
                self.execute(statement)
        except InterpreterError as e:
            print(f"Runtime Error: {e}")

    def execute(self, statement: Statement) -> None:
        """Execute a statement."""
        method = f"execute_{type(statement).__name__.lower()}"
        if hasattr(self, method):
            return getattr(self, method)(statement)
        raise RuntimeError(f"Unknown statement type: {type(statement).__name__}")

    def evaluate(self, expression: Expression) -> Any:
        """Evaluate an expression."""
        method = f"evaluate_{type(expression).__name__.lower()}"
        if hasattr(self, method):
            return getattr(self, method)(expression)
        raise RuntimeError(f"Unknown expression type: {type(expression).__name__}")

    def execute_block(self, statement: Block) -> None:
        """Execute a block of statements in a new scope."""
        # Execute statements in the current environment
        # This allows proper access to variables in the enclosing scope
        for stmt in statement.statements:
            self.execute(stmt)

    def execute_variabledecl(self, statement: VariableDecl) -> None:
        """Execute a variable declaration."""
        value = None
        if statement.initializer:
            value = self.evaluate(statement.initializer)
            if isinstance(statement.initializer, TypeCast):
                # For type casts, we've already validated the conversion in evaluate_typecast
                pass
            else:
                value_type = TypeChecker.get_type_name(value)
                value_type_annotation = TypeAnnotation(value_type, kind=TypeKind.PRIMITIVE)
                type_checker = TypeChecker()
                try:
                    value = type_checker.validate_assignment(statement.type_annotation, value, value_type_annotation)
                except TypeError as e:
                    raise RuntimeError(str(e))
        
        name = statement.name.name
        if name == ':':  # Skip the colon token that was incorrectly parsed as the name
            return
        self.environment.define(name, value, statement.type_annotation.name)

    def execute_assignment(self, statement: Assignment) -> None:
        """Execute an assignment statement."""
        value = self.evaluate(statement.value)
        self.environment.assign(statement.target.name, value)

    def execute_ifstatement(self, statement: IfStatement) -> None:
        """Execute an if statement."""
        condition_value = self.evaluate(statement.condition)
        
        # Execute the appropriate branch in the current environment
        if condition_value:
            self.execute(statement.then_branch)
        else:
            # Handle elif branches
            for condition, branch in statement.elif_branches:
                if self.evaluate(condition):
                    self.execute(branch)
                    return
            # Handle else branch
            if statement.else_branch:
                self.execute(statement.else_branch)

    def execute_whileloop(self, statement: WhileLoop) -> None:
        """Execute a while loop."""
        while self.evaluate(statement.condition):
            self.execute(statement.body)

    def execute_forloop(self, statement: ForLoop) -> None:
        """Execute a for loop."""
        start = self.evaluate(statement.start)
        end = self.evaluate(statement.end)
        step = 1 if statement.step is None else self.evaluate(statement.step)
        
        # Handle inclusive/exclusive range
        if not statement.is_inclusive:
            end = end - 1 if step > 0 else end + 1

        iterator_name = statement.iterator.name
        previous = self.environment
        try:
            self.environment = Environment(parent=previous)
            self.environment.define(iterator_name, start, "Int")  # Iterator is always Int type
            i = start
            while (i <= end if step > 0 else i >= end):
                self.environment.assign(iterator_name, i)
                self.execute(statement.body)
                i += step
        finally:
            self.environment = previous

    def execute_expressionstmt(self, statement: ExpressionStmt) -> None:
        """Execute an expression statement."""
        self.evaluate(statement.expression)

    def evaluate_literal(self, expression: Literal) -> Any:
        """Evaluate a literal value."""
        if expression.type == TokenType.INTEGER_LIT:
            return int(expression.value)
        elif expression.type == TokenType.FLOAT_LIT:
            return float(expression.value)
        elif expression.type == TokenType.DOUBLE_LIT:
            return float(expression.value)
        elif expression.type == TokenType.STRING_LIT:
            return str(expression.value)
        elif expression.type == TokenType.CHAR_LIT:
            return str(expression.value)
        elif expression.type == TokenType.BOOL_LIT:
            return bool(expression.value)
        elif expression.type == TokenType.EMPTY:
            return []  # Empty collections are represented as empty lists
        return expression.value

    def evaluate_identifier(self, expression: Identifier) -> Any:
        """Evaluate an identifier."""
        name = expression.name
        env = self.environment
        
        while env is not None:
            if name in env.values:
                return env.values[name]
            env = env.parent
            
        raise RuntimeError(f"Undefined variable '{name}'")

    def evaluate_binaryop(self, expression: BinaryOp) -> Any:
        """Evaluate a binary operation."""
        left = self.evaluate(expression.left)
        right = self.evaluate(expression.right)

        op_type = expression.operator.type
        if op_type == TokenType.PLUS:
            return left + right
        elif op_type == TokenType.MINUS:
            return left - right
        elif op_type == TokenType.MULTIPLY:
            return left * right
        elif op_type == TokenType.DIVIDE:
            if right == 0:
                raise RuntimeError("Division by zero")
            return left / right
        elif op_type == TokenType.MODULO:
            return left % right
        elif op_type == TokenType.EQUALS:
            return left == right
        elif op_type == TokenType.NOT_EQUALS:
            return left != right
        elif op_type == TokenType.LESS_THAN:
            return left < right
        elif op_type == TokenType.LESS_EQUAL:
            return left <= right
        elif op_type == TokenType.GREATER_THAN:
            return left > right
        elif op_type == TokenType.GREATER_EQUAL:
            return left >= right
        
        raise RuntimeError(f"Unknown binary operator: {op_type}")

    def evaluate_unaryop(self, expression: UnaryOp) -> Any:
        """Evaluate a unary operation."""
        operand = self.evaluate(expression.operand)
        
        op_type = expression.operator.type
        if op_type == TokenType.MINUS:
            return -operand
        elif op_type == TokenType.BANG:
            return not operand
            
        raise RuntimeError(f"Unknown unary operator: {op_type}")

    def evaluate_arrayliteral(self, expression: ArrayLiteral) -> Any:
        """Evaluate an array literal."""
        return [self.evaluate(element) for element in expression.elements]

    def execute_functiondecl(self, statement: FunctionDecl) -> None:
        """Execute a function declaration."""
        def function(*args):
            if len(args) != len(statement.params):
                raise RuntimeError(f"Expected {len(statement.params)} arguments but got {len(args)}")
                
            # Create new environment with the current environment as parent
            function_env = Environment(parent=self.environment)
            
            # Bind parameters to arguments first
            type_checker = TypeChecker()
            for param, arg in zip(statement.params, args):
                param_type = TypeAnnotation(param.type_annotation.name, kind=TypeKind.PRIMITIVE)
                arg_type = TypeAnnotation(TypeChecker.get_type_name(arg), kind=TypeKind.PRIMITIVE)
                try:
                    converted_arg = type_checker.validate_assignment(param_type, arg, arg_type)
                    function_env.define(param.name.name, converted_arg, param_type.name)
                except TypeError as e:
                    raise RuntimeError(f"Type error in function argument: {str(e)}")
            
            # Save and switch environment
            previous = self.environment
            self.environment = function_env
            
            try:
                # Execute the function body
                result = None
                try:
                    self.execute(statement.body)
                except ReturnValue as return_value:
                    result = return_value.value
                
                if statement.return_type:
                    if result is None:
                        raise RuntimeError("Function did not return a value")
                    return_type = TypeAnnotation(statement.return_type.name, kind=TypeKind.PRIMITIVE)
                    value_type = TypeAnnotation(TypeChecker.get_type_name(result), kind=TypeKind.PRIMITIVE)
                    try:
                        return type_checker.validate_assignment(return_type, result, value_type)
                    except TypeError as e:
                        raise RuntimeError(f"Type error in return value: {str(e)}")
                return result
            finally:
                self.environment = previous
            
        # Store the function in the current environment
        self.environment.define(statement.name.name, function, "Function")

    def evaluate_functioncall(self, expression: FunctionCall) -> Any:
        """Evaluate a function call."""
        # Look up the function in the current environment chain
        if isinstance(expression.callee, Identifier):
            callee = self.environment.get(expression.callee.name)
        else:
            callee = self.evaluate(expression.callee)
        
        # Evaluate arguments in the current environment
        arguments = [self.evaluate(arg) for arg in expression.arguments]
        
        if callable(callee):
            return callee(*arguments)
        raise RuntimeError(f"Can only call functions and classes")
        
    def execute_returnstatement(self, statement: ReturnStatement) -> None:
        """Execute a return statement."""
        value = None
        if statement.value:
            value = self.evaluate(statement.value)
        raise ReturnValue(value)

    def evaluate_assignment(self, expression: Assignment) -> Any:
        """Evaluate an assignment expression."""
        value = self.evaluate(expression.value)
        self.environment.assign(expression.target.name, value)
        return value

    def evaluate_typecast(self, expression: TypeCast) -> Any:
        """Evaluate a type cast expression."""
        value = self.evaluate(expression.expression)
        from_type = TypeChecker.get_type_name(value)
        to_type = expression.target_type.name
        
        try:
            type_checker = TypeChecker()
            return type_checker.validate_type_cast(value, from_type, to_type)
        except TypeError as e:
            raise RuntimeError(str(e))

class ReturnValue(Exception):
    """Used to handle return statements in functions."""
    def __init__(self, value):
        self.value = value

if __name__ == "__main__":
    from noir_lexer import lex
    from noir_parser import Parser
    
    source = """
    func factorial(n: Int) -> Int:
        if n <= 1:
            return 1
        ::
        return n * factorial(n - 1)
    ::

    func calculate_series(start: Int, end: Int) -> Int:
        func sum_range(a: Int, b: Int) -> Int:
            total: Int = 0
            for i in a to b:
                total = total + i
            ::
            return total
        ::

        result: Int = sum_range(start, end)
        return result
    ::

    print("Factorial of 5:", factorial(5))
    print("Sum of numbers from 1 to 5:", calculate_series(1, 6))
    """
    
    try:
        tokens = lex(source)
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        interpreter.interpret(ast)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()