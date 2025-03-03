from typing import Dict, List, Optional, Union, Any
from noir_lexer import Token, TokenType, LexerError
from noir_ast import (
    Node, Expression, Statement, Literal, Identifier, BinaryOp, UnaryOp,
    TypeKind, TypeConstraint, TypeParameter, TypeAnnotation,
    VariableDecl, Assignment, Block, IfStatement, ForLoop, WhileLoop,
    FunctionParam, FunctionDecl, FunctionCall, ReturnStatement,
    ExpressionStmt, TypeCast, ArrayLiteral, MethodCall, ArrayAccess,
    LIST_TYPE, SET_TYPE, ORDERED_SET_TYPE, DICTIONARY_TYPE,
    EnumDeclaration, EnumVariant, ProtocolDeclaration, ProtocolProperty, ProtocolMethod
)

class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        self.message = message
        self.token = token
        super().__init__(f"Parse error at line {token.line}, column {token.column}: {message}")

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        self.block_stack = []  # Stack to track blocks that need :: terminators

    def begin_block(self, block_type: str, line: int, column: int) -> None:
        """Track the start of a new block that requires a :: terminator."""
        self.block_stack.append((block_type, line, column))

    def end_block(self) -> None:
        """End the most recent block, ensuring it has a :: terminator."""
        if not self.block_stack:
            raise ParseError("Unexpected '::' terminator with no matching block.", self.peek())
        self.block_stack.pop()

    def check_unclosed_blocks(self) -> None:
        """Check for any blocks that weren't properly terminated with ::"""
        if self.block_stack:
            block_type, line, column = self.block_stack[-1]
            raise ParseError(
                f"Missing '::' terminator for {block_type} block starting at line {line}, column {column}",
                self.peek()
            )

    def peek(self) -> Token:
        """Look at the current token without consuming it."""
        if self.current >= len(self.tokens):
            return Token(TokenType.EOF, "", 0, 0)
        return self.tokens[self.current]

    def previous(self) -> Token:
        """Get the previously consumed token."""
        return self.tokens[self.current - 1]

    def advance(self) -> Token:
        """Consume and return the current token."""
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        """Check if we've reached the end of the token stream."""
        return self.peek().type == TokenType.EOF

    def match(self, *types: TokenType) -> bool:
        """Check if the current token matches any of the given types."""
        for type in types:
            if self.check(type):
                self.advance()
                return True
        return False

    def check(self, type: TokenType) -> bool:
        """Check if the current token is of the given type without consuming it."""
        if self.is_at_end():
            return False
        return self.peek().type == type

    def consume(self, type: TokenType, message: str) -> Token:
        """Consume the current token if it matches the expected type."""
        if self.check(type):
            return self.advance()
        raise ParseError(message, self.peek())

    def parse(self) -> List[Statement]:
        """Parse the entire program."""
        statements = []
        while not self.is_at_end():
            try:
                # Skip any leading newlines between statements
                while self.match(TokenType.NEWLINE):
                    pass
                    
                # If we've reached EOF after skipping newlines, break
                if self.is_at_end():
                    break
                    
                # Skip comments
                if self.match(TokenType.COMMENT):
                    continue
                    
                stmt = self.declaration()
                if stmt is not None:  # Only add non-None statements
                    statements.append(stmt)
            except ParseError as e:
                # Keep error logging
                print(f"Parse error: {e}")
                self.synchronize()

        # Check for any unclosed blocks at the end of parsing
        self.check_unclosed_blocks()
        return statements

    def declaration(self) -> Statement:
        """Parse a declaration (variables, functions, etc.)"""
        if self.match(TokenType.IDENTIFIER):
            # Check for variable declarations with type annotations
            if self.check(TokenType.COLON):
                return self.finish_variable_declaration(self.previous())
                
            # Otherwise, this might be an assignment
            self.current -= 1  # Rewind to re-read the identifier
            
        if self.match(TokenType.FUNC):
            # Function declaration, consume the function name
            if self.match(TokenType.IDENTIFIER):
                return self.finish_function_declaration(self.previous())
            else:
                raise ParseError("Expected function name after 'func' keyword", self.peek())
                
        # Check for enum declaration
        if self.match(TokenType.ENUM):
            return self.enum_declaration()
            
        # Check for protocol declaration
        if self.match(TokenType.PROTOCOL):
            return self.protocol_declaration()
            
        # No declaration keyword found, try parsing a statement
        return self.statement()
        
    def enum_declaration(self) -> EnumDeclaration:
        """Parse an enum declaration"""
        # Parse the enum name
        name_token = self.consume(TokenType.IDENTIFIER, "Expected enum name")
        name = Identifier(name_token.value)
        
        # Check if this enum conforms to a protocol
        protocol_conformance = None
        if self.match(TokenType.CONFORMANCE) or self.match(TokenType.CONFORMS):
            protocol_name = self.consume(TokenType.IDENTIFIER, "Expected protocol name after conformance operator")
            protocol_conformance = Identifier(protocol_name.value)
        
        # Expect a colon after the enum name (and optional protocol conformance)
        self.consume(TokenType.COLON, "Expected ':' after enum name")
        
        # Begin tracking this block for :: termination
        self.begin_block("enum", name_token.line, name_token.column)
        
        # Parse the enum variants
        variants = []
        
        # Skip any newlines and comments after the colon
        while self.match(TokenType.NEWLINE, TokenType.COMMENT):
            pass
            
        # Parse variants until we reach the :: terminator
        while not self.check(TokenType.DOUBLE_COLON) and not self.is_at_end():
            # Skip newlines and comments between variants
            while self.match(TokenType.NEWLINE, TokenType.COMMENT):
                pass
                
            # Parse a variant
            if self.match(TokenType.IDENTIFIER):
                variant_name = Identifier(self.previous().value)
                variants.append(EnumVariant(variant_name))
                
                # Skip newlines and comments after a variant
                while self.match(TokenType.NEWLINE, TokenType.COMMENT):
                    pass
            else:
                # If we don't find an identifier, break out of the loop
                # This allows for trailing newlines before the :: terminator
                break
        
        # Consume the :: terminator
        self.consume(TokenType.DOUBLE_COLON, "Expected '::' to terminate enum declaration")
        
        # End this block
        self.end_block()
        
        return EnumDeclaration(name, variants, protocol_conformance)
        
    def protocol_declaration(self) -> ProtocolDeclaration:
        """Parse a protocol declaration"""
        # Parse the protocol name
        name_token = self.consume(TokenType.IDENTIFIER, "Expected protocol name")
        name = Identifier(name_token.value)
        
        # Expect a colon after the protocol name
        self.consume(TokenType.COLON, "Expected ':' after protocol name")
        
        # Begin tracking this block for :: termination
        self.begin_block("protocol", name_token.line, name_token.column)
        
        # Parse protocol members (properties and methods)
        properties = []
        methods = []
        
        # Skip any newlines and comments after the colon
        while self.match(TokenType.NEWLINE, TokenType.COMMENT):
            pass
            
        # Parse members until we reach the :: terminator
        while not self.check(TokenType.DOUBLE_COLON) and not self.is_at_end():
            # Skip newlines and comments between members
            while self.match(TokenType.NEWLINE, TokenType.COMMENT):
                pass
                
            # Check for empty keyword for empty protocol
            if self.match(TokenType.EMPTY):
                # Skip newlines and comments after empty
                while self.match(TokenType.NEWLINE, TokenType.COMMENT):
                    pass
                break
                
            # Parse a member (property or method)
            if self.match(TokenType.IDENTIFIER):
                member_name = Identifier(self.previous().value)
                
                # If followed by a colon, it's a property
                if self.match(TokenType.COLON):
                    type_annotation = self.parse_type_annotation()
                    properties.append(ProtocolProperty(member_name, type_annotation))
                # If followed by parentheses, it's a method
                elif self.match(TokenType.LPAREN):
                    # Parse parameters
                    params = []
                    if not self.check(TokenType.RPAREN):
                        # Parse first parameter
                        param_name = self.consume(TokenType.IDENTIFIER, "Expected parameter name")
                        self.consume(TokenType.COLON, "Expected ':' after parameter name")
                        param_type = self.parse_type_annotation()
                        params.append(FunctionParam(Identifier(param_name.value), param_type))
                        
                        # Parse additional parameters
                        while self.match(TokenType.COMMA):
                            param_name = self.consume(TokenType.IDENTIFIER, "Expected parameter name")
                            self.consume(TokenType.COLON, "Expected ':' after parameter name")
                            param_type = self.parse_type_annotation()
                            params.append(FunctionParam(Identifier(param_name.value), param_type))
                    
                    # Consume closing parenthesis
                    self.consume(TokenType.RPAREN, "Expected ')' after parameters")
                    
                    # Parse return type if any
                    return_type = None
                    if self.match(TokenType.ARROW):
                        return_type = self.parse_type_annotation()
                        
                    methods.append(ProtocolMethod(member_name, params, return_type))
                else:
                    raise ParseError("Expected ':' or '(' after member name", self.peek())
                    
                # Skip newlines and comments after a member
                while self.match(TokenType.NEWLINE, TokenType.COMMENT):
                    pass
            else:
                # If we don't find an identifier, break out of the loop
                # This allows for trailing newlines before the :: terminator
                break
        
        # Consume the :: terminator
        self.consume(TokenType.DOUBLE_COLON, "Expected '::' to terminate protocol declaration")
        
        # End this block
        self.end_block()
        
        return ProtocolDeclaration(name, properties, methods)

    def finish_variable_declaration(self, identifier_token: Token) -> VariableDecl:
        """Parse the rest of a variable declaration after seeing the identifier and colon."""
        type_annotation = self.parse_type_annotation()
        
        # Require initialization
        if not self.match(TokenType.ASSIGN):
            raise ParseError("Variables must be initialized at declaration.", self.peek())
        
        initializer = self.expression()
        
        return VariableDecl(
            Identifier(identifier_token.value),
            type_annotation,
            initializer
        )

    def parse_type_annotation(self) -> TypeAnnotation:
        """Parse a type annotation, including generic types."""
        # Handle array types using bracket notation [Type]
        if self.match(TokenType.LBRACKET):
            # For dictionary types with key-value notation [K: V]
            element_type = self.parse_type_annotation()
            if self.match(TokenType.COLON):
                value_type = self.parse_type_annotation()
                self.consume(TokenType.RBRACKET, "Expected ']' after dictionary type.")
                return TypeAnnotation(
                    "Dict",
                    [element_type, value_type],
                    kind=TypeKind.INSTANTIATED
                )
            
            self.consume(TokenType.RBRACKET, "Expected ']' after array element type.")
            return TypeAnnotation(
                "Array",
                [element_type],
                kind=TypeKind.INSTANTIATED
            )

        # Handle type parameters (single uppercase letters)
        if self.match(TokenType.IDENTIFIER):
            type_name = self.previous().value
            if len(type_name) == 1 and type_name.isupper():
                return TypeAnnotation(
                    type_name,
                    kind=TypeKind.PARAMETER
                )
            
            # Handle generic types with parameters
            if self.match(TokenType.LESS_THAN):
                parameters = []
                
                if not self.check(TokenType.GREATER_THAN):
                    while True:
                        # Parse type parameter or concrete type
                        param = self.parse_type_annotation()
                        parameters.append(param)
                        
                        if not self.match(TokenType.COMMA):
                            break
                            
                self.consume(TokenType.GREATER_THAN, "Expected '>' after type parameters.")
                
                # Determine if this is a generic type or an instantiated type
                is_generic = any(
                    isinstance(p, TypeAnnotation) and p.kind == TypeKind.PARAMETER
                    for p in parameters
                )
                
                return TypeAnnotation(
                    type_name,
                    parameters,
                    kind=TypeKind.GENERIC if is_generic else TypeKind.INSTANTIATED
                )
                
            # Regular type identifier without parameters
            return TypeAnnotation(type_name, kind=TypeKind.PRIMITIVE)
        
        # Handle built-in types
        if self.match(TokenType.INT, TokenType.FLOAT, TokenType.DOUBLE,
                    TokenType.STRING, TokenType.CHAR, TokenType.BOOL):
            return TypeAnnotation(self.previous().value, kind=TypeKind.PRIMITIVE)
            
        # Handle Set and OSet types
        if self.match(TokenType.SET, TokenType.OSET):
            base_type = self.previous().value
            
            # Generic set types must have a type parameter
            if self.match(TokenType.LESS_THAN):
                element_type = self.parse_type_annotation()
                self.consume(TokenType.GREATER_THAN, "Expected '>' after set type parameter.")
                return TypeAnnotation(
                    base_type,
                    [element_type],
                    kind=TypeKind.INSTANTIATED if element_type.kind != TypeKind.PARAMETER else TypeKind.GENERIC
                )
            
            # Set without type parameter is invalid
            raise ParseError("Set types must specify their element type", self.peek())
        
        raise ParseError("Expected type name", self.peek())

    def finish_function_declaration(self, identifier_token: Token) -> FunctionDecl:
        """Parse a function declaration after seeing the identifier."""
        # Begin a new block for the function
        self.begin_block("function", identifier_token.line, identifier_token.column)
        
        # Consume the opening parenthesis
        self.consume(TokenType.LPAREN, "Expected '(' after function name.")
        
        params = []
        # Parse parameters
        if not self.check(TokenType.RPAREN):
            while True:
                param_name = self.consume(TokenType.IDENTIFIER, "Expected parameter name.")
                self.consume(TokenType.COLON, "Expected ':' after parameter name.")
                param_type = self.parse_type_annotation()
                params.append(FunctionParam(Identifier(param_name.value), param_type))
                
                if not self.match(TokenType.COMMA):
                    break
                    
        self.consume(TokenType.RPAREN, "Expected ')' after parameters.")
        
        # Parse return type if present
        return_type = None
        if self.match(TokenType.ARROW):
            return_type = self.parse_type_annotation()
            
        self.consume(TokenType.COLON, "Expected ':' before function body.")
        body = self.block()
        self.consume(TokenType.DOUBLE_COLON, "Expected '::' after function body.")
        
        # End the function block
        self.end_block()
        
        return FunctionDecl(
            Identifier(identifier_token.value),
            params,
            return_type,
            body
        )

    def statement(self) -> Statement:
        """Parse a statement."""
        try:
            if self.previous().type == TokenType.IF:
                return self.if_statement()
            if self.previous().type == TokenType.FOR:
                return self.for_statement()
            if self.previous().type == TokenType.WHILE:
                return self.while_statement()
            if self.previous().type == TokenType.RETURN:
                return self.return_statement()
            
            return self.expression_statement()
        except ParseError as error:
            self.synchronize()
            return None

    def expression_statement(self) -> Statement:
        """Parse an expression statement."""
        # Skip any leading newlines
        while self.match(TokenType.NEWLINE):
            pass
        
        expr = self.expression()
        
        # Skip any trailing newlines
        while self.match(TokenType.NEWLINE):
            pass
        
        return ExpressionStmt(expr)

    def if_statement(self) -> IfStatement:
        """Parse an if statement."""
        # Track the start of the if block
        self.begin_block("if", self.previous().line, self.previous().column)
        
        condition = self.expression()
        self.consume(TokenType.COLON, "Expected ':' after if condition.")
        
        # Skip any newlines after the colon
        while self.match(TokenType.NEWLINE):
            pass
        
        then_branch = self.block()
        elif_branches = []
        else_branch = None
        
        # Handle else and else if branches
        if self.match(TokenType.DOUBLE_COLON):
            self.end_block()  # End the if block
            
            # Skip any newlines after the double colon
            while self.match(TokenType.NEWLINE):
                pass
                
            if self.match(TokenType.ELSE):
                if self.match(TokenType.IF):
                    # This is an else if branch
                    self.begin_block("else if", self.previous().line, self.previous().column)
                    elif_condition = self.expression()
                    self.consume(TokenType.COLON, "Expected ':' after else if condition.")
                    # Skip any newlines after the colon
                    while self.match(TokenType.NEWLINE):
                        pass
                    elif_body = self.block()
                    elif_branches.append((elif_condition, elif_body))
                else:
                    # This is the else branch
                    self.begin_block("else", self.previous().line, self.previous().column)
                    self.consume(TokenType.COLON, "Expected ':' after else.")
                    # Skip any newlines after the colon
                    while self.match(TokenType.NEWLINE):
                        pass
                    else_branch = self.block()
                    self.consume(TokenType.DOUBLE_COLON, "Expected '::' after else block.")
                    self.end_block()  # End the else block
        else:
            raise ParseError(
                f"Missing '::' terminator for if block starting at line {self.previous().line}",
                self.peek()
            )
        
        return IfStatement(condition, then_branch, elif_branches, else_branch)

    def for_statement(self) -> ForLoop:
        """Parse a for loop."""
        # Track the start of the for block
        self.begin_block("for", self.previous().line, self.previous().column)
        
        iterator = Identifier(self.consume(TokenType.IDENTIFIER, "Expected iterator variable name.").value)
        self.consume(TokenType.IN, "Expected 'in' after for loop variable.")
        
        start = self.expression()
        is_inclusive = False
        
        if self.match(TokenType.TO):
            is_inclusive = False
        elif self.match(TokenType.THRU):
            is_inclusive = True
        else:
            raise ParseError("Expected 'to' or 'thru' in for loop range.", self.peek())
            
        end = self.expression()
        step = None
        
        if self.match(TokenType.BY):
            step = self.expression()
            
        self.consume(TokenType.COLON, "Expected ':' after for loop range.")
        body = self.block()
        
        if self.match(TokenType.DOUBLE_COLON):
            self.end_block()  # End the for block
        else:
            raise ParseError(
                f"Missing '::' terminator for for block starting at line {self.previous().line}",
                self.peek()
            )
        
        return ForLoop(iterator, start, end, step, body, is_inclusive)

    def while_statement(self) -> WhileLoop:
        """Parse a while loop."""
        # Track the start of the while block
        self.begin_block("while", self.previous().line, self.previous().column)
        
        condition = self.expression()
        self.consume(TokenType.COLON, "Expected ':' after while condition.")
        body = self.block()
        
        if self.match(TokenType.DOUBLE_COLON):
            self.end_block()  # End the while block
        else:
            raise ParseError(
                f"Missing '::' terminator for while block starting at line {self.previous().line}",
                self.peek()
            )
        
        return WhileLoop(condition, body)

    def return_statement(self) -> ReturnStatement:
        """Parse a return statement."""
        value = None
        if not self.check(TokenType.DOUBLE_COLON):
            value = self.expression()
        return ReturnStatement(value)

    def block(self) -> Block:
        """Parse a block of statements."""
        statements = []
        
        # Skip any initial newlines
        while self.match(TokenType.NEWLINE):
            pass
        
        while not self.check(TokenType.DOUBLE_COLON) and not self.is_at_end():
            # Skip comments
            if self.match(TokenType.COMMENT):
                continue
                
            stmt = self.declaration()
            if stmt is not None:
                statements.append(stmt)
            # Skip any newlines between statements
            while self.match(TokenType.NEWLINE):
                pass
            
        return Block(statements)

    def expression(self) -> Expression:
        """Parse an expression."""
        return self.assignment()

    def assignment(self) -> Expression:
        """Parse an assignment expression."""
        expr = self.logical_or()
        
        if self.match(TokenType.ASSIGN):
            equals = self.previous()
            value = self.assignment()
            
            if isinstance(expr, Identifier):
                return Assignment(expr, value)
                
            raise ParseError("Invalid assignment target.", equals)
            
        return expr

    def logical_or(self) -> Expression:
        """Parse logical OR expression."""
        expr = self.logical_and()
        
        while self.match(TokenType.OR):
            operator = self.previous()
            right = self.logical_and()
            expr = BinaryOp(expr, operator, right)
            
        return expr

    def logical_and(self) -> Expression:
        """Parse logical AND expression."""
        expr = self.equality()
        
        while self.match(TokenType.AND):
            operator = self.previous()
            right = self.equality()
            expr = BinaryOp(expr, operator, right)
            
        return expr

    def equality(self) -> Expression:
        """Parse equality comparison."""
        expr = self.comparison()
        
        while self.match(TokenType.EQUALS, TokenType.NOT_EQUALS):
            operator = self.previous()
            right = self.comparison()
            expr = BinaryOp(expr, operator, right)
            
        return expr

    def comparison(self) -> Expression:
        """Parse comparison expression."""
        expr = self.term()
        
        while self.match(TokenType.LESS_THAN, TokenType.GREATER_THAN,
                        TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL):
            operator = self.previous()
            right = self.term()
            expr = BinaryOp(expr, operator, right)
            
        return expr

    def term(self) -> Expression:
        """Parse addition and subtraction."""
        expr = self.factor()
        
        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous()
            right = self.factor()
            expr = BinaryOp(expr, operator, right)
            
        return expr

    def factor(self) -> Expression:
        """Parse multiplication and division."""
        expr = self.unary()
        
        while self.match(TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO):
            operator = self.previous()
            right = self.unary()
            expr = BinaryOp(expr, operator, right)
            
        return expr

    def unary(self) -> Expression:
        """Parse unary expressions."""
        if self.match(TokenType.MINUS, TokenType.BANG):
            operator = self.previous()
            right = self.unary()
            return UnaryOp(operator, right)
            
        return self.type_cast()

    def type_cast(self) -> Expression:
        """Parse type cast expressions."""
        expr = self.primary()
        
        if self.match(TokenType.AS):
            target_type = self.parse_type_annotation()
            return TypeCast(expr, target_type)
            
        return expr

    def primary(self) -> Expression:
        """Parse primary expressions."""
        if self.match(TokenType.FALSE):
            return Literal(False, TokenType.BOOL_LIT)
        if self.match(TokenType.TRUE):
            return Literal(True, TokenType.BOOL_LIT)
            
        if self.match(TokenType.INTEGER_LIT, TokenType.FLOAT_LIT,
                     TokenType.DOUBLE_LIT, TokenType.STRING_LIT,
                     TokenType.CHAR_LIT):
            return Literal(self.previous().value, self.previous().type)
            
        if self.match(TokenType.LBRACKET):
            # Parse array literal
            elements = []
            if not self.check(TokenType.RBRACKET):
                while True:
                    elements.append(self.expression())
                    if not self.match(TokenType.COMMA):
                        break
            self.consume(TokenType.RBRACKET, "Expected ']' after array elements.")
            return ArrayLiteral(elements)
            
        if self.match(TokenType.IDENTIFIER):
            identifier = Identifier(self.previous().value)
            
            # Check for method call
            if self.match(TokenType.DOT):
                method = self.consume(TokenType.IDENTIFIER, "Expected method name after '.'")
                self.consume(TokenType.LPAREN, "Expected '(' after method name")
                arguments = []
                if not self.check(TokenType.RPAREN):
                    while True:
                        arguments.append(self.expression())
                        if not self.match(TokenType.COMMA):
                            break
                self.consume(TokenType.RPAREN, "Expected ')' after arguments")
                return MethodCall(identifier, method.value, arguments)
                
            # Check for array access
            if self.match(TokenType.LBRACKET):
                index = self.expression()
                self.consume(TokenType.RBRACKET, "Expected ']' after array index")
                return ArrayAccess(identifier, index)
                
            # Check for function call
            if self.match(TokenType.LPAREN):
                arguments = []
                if not self.check(TokenType.RPAREN):
                    while True:
                        arguments.append(self.expression())
                        if not self.match(TokenType.COMMA):
                            break
                self.consume(TokenType.RPAREN, "Expected ')' after arguments")
                return FunctionCall(identifier, arguments)
                
            return identifier
            
        if self.match(TokenType.LPAREN):
            expr = self.expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression.")
            return expr
            
        raise ParseError("Expected expression.", self.peek())

    def synchronize(self):
        """Recover from a parse error by synchronizing to the next statement."""
        self.advance()
        
        while not self.is_at_end():
            # If we see a double colon, we're at the end of a block
            if self.previous().type == TokenType.DOUBLE_COLON:
                # Skip any newlines after the double colon
                while self.match(TokenType.NEWLINE):
                    pass
                return
            
            # If we see any of these tokens, we're at the start of a new statement
            if self.peek().type in {
                TokenType.IF,
                TokenType.FOR,
                TokenType.WHILE,
                TokenType.RETURN,
                TokenType.IDENTIFIER
            }:
                return
            
            self.advance()


if __name__ == "__main__":
    from noir_lexer import lex
    source_code = """
x: Int = 42
y: Float = 3.14
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
    except ParseError as e:
        print(f"Error: {e}")