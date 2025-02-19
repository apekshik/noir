from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, List
import re

class TokenType(Enum):
    # Keywords
    IF = auto()
    ELSE = auto()
    TRUE = auto()
    FALSE = auto()
    FOR = auto()
    WHILE = auto()
    RETURN = auto()
    AS = auto()
    IN = auto()
    TO = auto()
    THRU = auto()
    BY = auto()
    EMPTY = auto()
    AND = auto()
    OR = auto()
    FUNC = auto()
    
    # Types
    INT = auto()
    FLOAT = auto()
    DOUBLE = auto()
    STRING = auto()
    CHAR = auto()
    BOOL = auto()
    SET = auto()
    OSET = auto()
    
    # Literals
    INTEGER_LIT = auto()
    FLOAT_LIT = auto()
    DOUBLE_LIT = auto()
    STRING_LIT = auto()
    CHAR_LIT = auto()
    BOOL_LIT = auto()
    
    # Identifiers
    IDENTIFIER = auto()
    
    # Operators
    PLUS = auto()          # +
    MINUS = auto()         # -
    MULTIPLY = auto()      # *
    DIVIDE = auto()        # /
    MODULO = auto()        # %
    ASSIGN = auto()        # =
    EQUALS = auto()        # ==
    NOT_EQUALS = auto()    # !=
    LESS_THAN = auto()     # <
    GREATER_THAN = auto()  # >
    LESS_EQUAL = auto()    # <=
    GREATER_EQUAL = auto() # >=
    
    # Delimiters
    LPAREN = auto()        # (
    RPAREN = auto()        # )
    LBRACKET = auto()      # [
    RBRACKET = auto()      # ]
    LANGLE = auto()        # <
    RANGLE = auto()        # >
    COLON = auto()         # :
    DOUBLE_COLON = auto()  # ::
    COMMA = auto()         # ,
    DOT = auto()           # .
    ARROW = auto()         # ->
    
    # Special
    COMMENT = auto()
    WHITESPACE = auto()
    NEWLINE = auto()
    EOF = auto()
    
    # New token type
    BANG = auto()        # For the '!' operator

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int
    
class LexerError(Exception):
    pass

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        
        # Keywords mapping
        self.keywords = {
            'if': TokenType.IF,
            'else': TokenType.ELSE,
            'true': TokenType.TRUE,
            'false': TokenType.FALSE,
            'for': TokenType.FOR,
            'while': TokenType.WHILE,
            'return': TokenType.RETURN,
            'as': TokenType.AS,
            'in': TokenType.IN,
            'to': TokenType.TO,
            'thru': TokenType.THRU,
            'by': TokenType.BY,
            'empty': TokenType.EMPTY,
            'Int': TokenType.INT,
            'Float': TokenType.FLOAT,
            'Double': TokenType.DOUBLE,
            'String': TokenType.STRING,
            'Char': TokenType.CHAR,
            'Bool': TokenType.BOOL,
            'Set': TokenType.SET,
            'OSet': TokenType.OSET,
            'and': TokenType.AND,
            'or': TokenType.OR,
            'func': TokenType.FUNC
        }
        
    def peek(self, ahead: int = 0) -> str:
        """Look ahead in the source without consuming."""
        if self.pos + ahead >= len(self.source):
            return ''
        return self.source[self.pos + ahead]
    
    def advance(self) -> str:
        """Consume and return the next character."""
        if self.pos >= len(self.source):
            return ''
        
        char = self.source[self.pos]
        self.pos += 1
        
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
            
        return char
    
    def add_token(self, type: TokenType, value: str):
        """Add a token to the token list."""
        self.tokens.append(Token(type, value, self.line, self.column - len(value)))
    
    def is_whitespace(self, char: str) -> bool:
        """Check if character is whitespace."""
        return char in ' \t\r'
    
    def is_digit(self, char: str) -> bool:
        """Check if character is a digit."""
        return char.isdigit()
    
    def is_alpha(self, char: str) -> bool:
        """Check if character is alphabetic."""
        return char.isalpha() or char == '_'
    
    def scan_number(self) -> None:
        """Scan a number literal."""
        num = ''
        has_dot = False
        is_double = False
        
        while self.peek() and (self.is_digit(self.peek()) or self.peek() == '.'):
            if self.peek() == '.':
                if has_dot:
                    raise LexerError(f"Invalid number format at line {self.line}, column {self.column}")
                has_dot = True
                
            # Check for double precision
            if has_dot and len(num.split('.')[-1]) > 7:
                is_double = True
                
            num += self.advance()
        
        if has_dot:
            self.add_token(TokenType.DOUBLE_LIT if is_double else TokenType.FLOAT_LIT, num)
        else:
            self.add_token(TokenType.INTEGER_LIT, num)
    
    def scan_string(self) -> None:
        """Scan a string literal."""
        string = ''
        self.advance()  # Consume opening quote
        
        while self.peek() and self.peek() != '"':
            if self.peek() == '\\':
                self.advance()
                # Handle escape sequences
                escaped = self.advance()
                if escaped == 'n': string += '\n'
                elif escaped == 't': string += '\t'
                elif escaped == 'r': string += '\r'
                elif escaped == '"': string += '"'
                elif escaped == '\\': string += '\\'
                else:
                    raise LexerError(f"Invalid escape sequence '\\{escaped}' at line {self.line}, column {self.column}")
            else:
                string += self.advance()
                
        if not self.peek():
            raise LexerError(f"Unterminated string at line {self.line}, column {self.column}")
            
        self.advance()  # Consume closing quote
        self.add_token(TokenType.STRING_LIT, string)
    
    def scan_char(self) -> None:
        """Scan a character literal."""
        self.advance()  # Consume opening quote
        
        if not self.peek():
            raise LexerError(f"Unterminated character literal at line {self.line}, column {self.column}")
            
        char = self.advance()
        
        if self.peek() != "'":
            raise LexerError(f"Invalid character literal at line {self.line}, column {self.column}")
            
        self.advance()  # Consume closing quote
        self.add_token(TokenType.CHAR_LIT, char)
    
    def scan_identifier(self) -> None:
        """Scan an identifier or keyword."""
        identifier = ''
        
        while self.peek() and (self.is_alpha(self.peek()) or self.is_digit(self.peek())):
            identifier += self.advance()
            
        # Check if it's a keyword
        token_type = self.keywords.get(identifier, TokenType.IDENTIFIER)
        self.add_token(token_type, identifier)
    
    def scan_comment(self) -> None:
        """Scan a comment."""
        comment = '//'
        self.advance()  # Consume second '/'
        
        while self.peek() and self.peek() != '\n':
            comment += self.advance()
            
        self.add_token(TokenType.COMMENT, comment)
    
    def tokenize(self) -> List[Token]:
        """Convert source code into a list of tokens."""
        while self.pos < len(self.source):
            char = self.peek()
            
            # Handle whitespace
            if self.is_whitespace(char):
                self.advance()
                continue
                
            # Handle newlines
            if char == '\n':
                self.add_token(TokenType.NEWLINE, '\n')
                self.advance()
                continue
                
            # Handle numbers
            if self.is_digit(char):
                self.scan_number()
                continue
                
            # Handle identifiers and keywords
            if self.is_alpha(char):
                self.scan_identifier()
                continue
                
            # Handle string literals
            if char == '"':
                self.scan_string()
                continue
                
            # Handle character literals
            if char == "'":
                self.scan_char()
                continue
                
            # Handle operators and delimiters
            if char == '/':
                if self.peek(1) == '/':
                    self.scan_comment()
                else:
                    self.add_token(TokenType.DIVIDE, self.advance())
                continue
                
            # Handle two-character tokens
            if char == ':' and self.peek(1) == ':':
                self.advance()  # Consume first ':'
                self.advance()  # Consume second ':'
                self.add_token(TokenType.DOUBLE_COLON, '::')
                continue
                
            if char == '-' and self.peek(1) == '>':
                self.advance()  # Consume '-'
                self.advance()  # Consume '>'
                self.add_token(TokenType.ARROW, '->')
                continue
                
            if char == '=' and self.peek(1) == '=':
                self.advance()  # Consume first '='
                self.advance()  # Consume second '='
                self.add_token(TokenType.EQUALS, '==')
                continue
                
            if char == '!' and self.peek(1) == '=':
                self.advance()  # Consume '!'
                self.advance()  # Consume '='
                self.add_token(TokenType.NOT_EQUALS, '!=')
                continue
                
            if char == '<' and self.peek(1) == '=':
                self.advance()  # Consume '<'
                self.advance()  # Consume '='
                self.add_token(TokenType.LESS_EQUAL, '<=')
                continue
                
            if char == '>' and self.peek(1) == '=':
                self.advance()  # Consume '>'
                self.advance()  # Consume '='
                self.add_token(TokenType.GREATER_EQUAL, '>=')
                continue
            
            # Handle single-character tokens
            token_map = {
                '+': TokenType.PLUS,
                '-': TokenType.MINUS,
                '*': TokenType.MULTIPLY,
                '%': TokenType.MODULO,
                '=': TokenType.ASSIGN,
                '<': TokenType.LESS_THAN,
                '>': TokenType.GREATER_THAN,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET,
                ':': TokenType.COLON,
                ',': TokenType.COMMA,
                '.': TokenType.DOT
            }
            
            if char in token_map:
                self.add_token(token_map[char], self.advance())
                continue
                
            # If we get here, we encountered an invalid character
            raise LexerError(f"Invalid character '{char}' at line {self.line}, column {self.column}")
            
        # Add EOF token
        self.add_token(TokenType.EOF, '')
        return self.tokens

def lex(source: str) -> List[Token]:
    """Convenience function to create a lexer and tokenize source code."""
    lexer = Lexer(source)
    return lexer.tokenize()

# Example usage
if __name__ == "__main__":
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

for i in 1 to nums.count by 1:
    for j in range i:
        if nums[i] > nums[j]:
            dp[i] = max(dp[i], dp[j] + 1) 
        :: 
::  :: 
    """
    
    try:
        tokens = lex(source_code)
        for token in tokens:
            print(f"{token.type}: '{token.value}' at line {token.line}, column {token.column}")
    except LexerError as e:
        print(f"Error: {e}")