// Noir is a statically typed language with type inference. It doesn't really care about whitespace, but it's recommended to use it for readability.

// Basic data types in Noir
x: Int = 4
x = 4 
content: String = "This is some text that stores content"
z: Float = 3.432
d: Double = 3.1415926573203
c: Char = 'a'
booleanValue: Bool = false

// Allow implicit conversions from Int to Float and Double since this does not risk data loss.
x: Int = 42
y: Float = x // Implicit conversion from Int to Float
z: Double = x // Implicit conversion from Int to Double

// Require explicit conversions when going from Float or Double to Int, or between Float and Double.
a: Float = 3.14
b: Int = a as Int // Explicit conversion from Float to Int

c: Double = 3.141592653589793
d: Float = c as Float // Explicit conversion from Double to Float

e: Float = 2.71828
f: Double = e as Double // Explicit conversion from Float to Double

// I wanted to use 'as' instead of Int(a) or similar because I want to separate type conversion from function calling because
// they're fundamentally different programming concepts happening although under the hood they're about the same thing. The focus is on readability.

// Data collection types in Noir
arr: [Float] = [3.2, 4.3, 23.232]
emptyArray: [Int] = empty // equivalent to emptyArray: [Int] = [] 

dict: [Int: String] = [34: "France", 42, "Paris"]
emptyDict: [Char: Double] = empty // equivalent to emptyDict: [Char: Doule] = []

set: Set<String> = ("Bruh", "What", "Hell na")
orderedSet: OSet<Int> = ("Bruh", "What", "Hell na")
emptySet: Set<Int> = empty // equivalent to emtpySet: Set<Int> = ()

// if-else branching looks like this. I really like how the '::' demarkator is a natural structural indicator. 
if condition:
    // Code block for true condition
:: else if another_condition:
    // Code block for another condition
:: else:
    // Code block for false condition
::

// Another way to style this is like so
if condition_met: 
    one line of code :: 
else if: 
    one line of code :: 
else: 
    final one line of code :: 


// For Loops will be internally handled like this
for i in stride(from: 0, to: 10, by: 1): 
    // Loop body
::

// But for the ease of the programmer, they can be written simply like this: 
for i in 0 to 10: 
    // Loop Body
::

for i in 0 to 10 by 2: 
    // Loop Body
:: 

// Including the upper bound
for i in stride(from: 0, through: 10, by: 1): 
    // Loop body
::

for i in 0 thru 10: 
    // Loop body
    print(i)
:: 

// Combined For Loop and If-Else Example in Rizz
for i in 0 to 10:
    if i % 2 == 0:
        print(i, "is even")
    :: else:
        print(i, "is odd")
    ::
::


// While Loops will be handled like this 
while condition: 
    // Loop Body 
:: 

// Printing 
print(content)

// Iterative Fibonacci function in Rizz
iterativeFibonacci(n: Int) -> [Int]:
    if n <= 0:
        return [0] 
    :: else if n == 1:
        return [0, 1] 
    ::
    
    fibSeq: [Int] = [0, 1]

    for i in 2 to n:
        fibSeq.append(fibSeq[i - 1] + fibSeq[i - 2]) 
    :: 

    return fibSeq
::

fibonacciNumbers: [Int] = iterativeFibonacci(10)
print(fibonacciNumbers)

// More complex function example: 

lengthOfLIS(nums: [Int]):
    if not nums:
        return 0
    
    // Initialize the dp array with 1, since each element is an increasing subsequence of length 1 by itself
    dp: [Int] = [Int](repeat: 1, count: nums.count)
    
    // Fill the dp array
    for i in 1 to nums.count by 1:
        for j in range i:
            if nums[i] > nums[j]:
                dp[i] = max(dp[i], dp[j] + 1) 
            :: 
    ::  :: // Notice how the number of :: operators tells how deep the nested loop is. 
    
    # The length of the longest increasing subsequence
    return max(dp) 
:: 

// Example usage
nums: [Int] = [10, 9, 2, 5, 3, 7, 101, 18]
lis_length: Int = lengthOfLIS(nums)
print("Length of Longest Increasing Subsequence:", lis_length)