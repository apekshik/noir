x: Int = 22 

func add(a: Int, b: Int) -> Float:
    return a + b
:: 

print(add(x, 2))

// Testing proper type conversion
y: Float = 3.14
x2: Int = y as Int  // Proper way to convert Float to Int using explicit cast
print("Test -1:", x2)

// This should pass
str: String = "123"
num: Int = str as Int  // This should pass since the string is a valid integer
print("Test 0:", num)

// Test 1: Valid implicit conversion (Int to Float)
x: Int = 22
y: Float = x  // This should work
print("Test 1:", y)

// Test 2: Float to Int requires explicit cast
z: Float = 3.14
w: Int = z as Int  // Using explicit cast
print("Test 2:", w)

// Test 1: Valid explicit conversion (Float to Int)
a: Float = 3.14
b: Int = a as Int  // This should work
print("Test 1 (Float to Int):", b)

// Test 2: Valid explicit conversion (String to Int)
str1: String = "123"
num1: Int = str1 as Int  // This should work
print("Test 2 (String to Int):", num1)

// Test 4: Valid explicit conversion (String to Float)
str3: String = "3.14"
num3: Float = str3 as Float  // This should work
print("Test 4 (String to Float):", num3)

// Test 3: Invalid explicit conversion (String to Int)
str2: String = "abc"
num2: Int = str2 as Int  // This should fail
print("Test 3 (Invalid String to Int):", num2)




