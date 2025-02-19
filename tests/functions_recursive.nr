// Recursive function to calculate factorial
func factorial(n: Int) -> Int:
    if n <= 1:
        return 1
    :: 
    return n * factorial(n - 1)
:: 

print(factorial(5))