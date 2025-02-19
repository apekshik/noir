from noir_lexer import lex
from noir_parser import Parser
from ast_printer import print_ast

# Your source code here
source_code = """
x: Int = 42
y: Float = 3.14
y = 3.51

for i in 0 to 10:
    if i % 2 == 0:
        print(i, "is even")
    :: else:
        print(i, "is odd")
    ::
::

i: Int = 0
while i < 10:
    print(i)
    i = i + 1
::
"""

source_code2 = """
func fibonacci(n: Int) -> [Int]:
    if n <= 0:
        return [0]
    ::
    else if n == 1:
        return [0, 1]
    ::

    fibSeq: [Int] = [0, 1]

    for i in 2 to n:
        fibSeq.append(fibSeq[i - 1] + fibSeq[i - 2])
    ::

    return fibSeq
::

fibonacciNumbers: [Int] = fibonacci(10)
print(fibonacciNumbers)
"""
tokens = lex(source_code2)
# print("Tokens:", [f"{t.type}({t.value})" for t in tokens])  # Debug tokens
parser = Parser(tokens)
ast = parser.parse()
# print("Number of AST nodes:", len(ast))  # Debug AST length
print("AST output:")
print(print_ast(ast))