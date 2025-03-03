# The Noir Programming Language

Noir is a modern programming language designed with clarity and safety in mind. It combines static typing with clean, expressive syntax to create a language that's powerful yet intuitive and approachable.

## Language Philosophy

Noir emphasizes:
- Clear, readable syntax that minimizes boilerplate
- Strong static typing with safe type conversions
- Explicit over implicit
- Block structure using the `::` terminator
- Safe concurrency patterns built into the language
- Predictable behavior through controlled type conversions

## Key Features

### Type System

Noir features a strong, static type system with clear conversion rules:

```noir
// Basic types
x: Int = 42
text: String = "Hello"
pi: Float = 3.14
precise: Double = 3.141592653589793
ch: Char = 'a'
flag: Bool = true

// Collections
numbers: [Int] = [1, 2, 3]
pairs: [String: Int] = ["one": 1, "two": 2]
uniqueItems: Set<String> = ("apple", "banana")
orderedItems: OSet<Int> = (1, 2, 3)
```

### Type Conversions

Noir manages type conversions explicitly:

```noir
// Implicit conversions (safe)
x: Int = 42
y: Float = x  // Int to Float is safe

// Explicit conversions (potentially unsafe)
f: Float = 3.14
i: Int = f as Int  // Requires explicit cast
```

### Control Flow

Clean, block-based control flow using `::` as terminators:

```noir
if condition:
    // True branch
:: else if another:
    // Else-if branch
:: else:
    // Else branch
::

for i in 0 to 10:
    // Loop body
::

while condition:
    // While loop body
::
```

### Functions

Functions with clear parameter and return type annotations:

```noir
func calculate(x: Int, y: Float) -> Float:
    result: Float = (x as Float) + y
    return result
::
```

### Range Operations

Flexible range operations with inclusive and exclusive bounds:

```noir
// Exclusive range
for i in 0 to 10:  // 0 to 9
    print(i)
::

// Inclusive range
for i in 0 thru 10:  // 0 to 10
    print(i)
::

// Custom step
for i in 0 to 10 by 2:  // 0, 2, 4, 6, 8
    print(i)
::
```

### Error Handling

TODO: Error handling details to be determined.


# Concurrency in Noir: Shared Data and Locks

Noir provides a simple yet powerful concurrency model centered around shared data access. Instead of manually managing locks, Noir uses a declarative approach where shared resources are marked with the `shared` keyword, and access patterns are explicitly defined using intuitive syntax.

## Declaring Shared Data

Use the `shared` keyword to declare variables that will be accessed by multiple async tasks:

```noir
shared counter: Int = 0
shared taskQueue: [String] = []
```

## Accessing Shared Data

Noir uses a `grab` syntax to define critical sections where shared data is accessed:

```noir
// Write access (can both read and modify)
grab counter:
    counter = counter + 1
::

// Read-only access
grab counter to read:
    print(counter)
::

// Explicit write access (same as grab counter:)
grab counter to write:
    counter = counter + 1
::
```

## Multiple Resource Access

Multiple shared resources can be accessed in a single grab statement:

```noir
grab inventory, orderCount:
    // Access both resources
::

grab inventory to read, orderCount to write:
    // Read from inventory, modify orderCount
::
```

## Lock Transitions

When you need to switch from read to write access, release the read lock and acquire a write lock explicitly:

```noir
grab cache to read:
    if cache.needsUpdate():
        grab cache to write:
            cache.update()
        ::
    ::
::
```

## Asynchronous Waiting

Use `await` within a grab block to wait for conditions on shared data:

```noir
grab messageQueue:
    await messageQueue.length < maxSize:
        messageQueue.push(message)
    ::
::
```

## Key Features

- No explicit lock/unlock calls required
- Clear visual indication of critical sections using `grab` and `::`
- Distinction between read and write access
- Automatic lock release at the end of blocks
- Support for conditional waiting with `await`
- Prevention of common concurrency bugs through compile-time checks# noir

## Enums and Protocols

Noir now supports enums and protocols, inspired by Swift's protocol system which promotes composition over inheritance.

### Enums

Enums allow you to define a type that can have one of several variants:

```noir
enum Status:
    Ok
    NotFound
    ServerError
::
```

### Protocols

Protocols define a set of requirements that conforming types must implement:

```noir
protocol Error:
    getMessage() -> String
::
```

An empty protocol can be defined using the `empty` keyword:

```noir
protocol Equatable:
    empty
::
```

### Protocol Conformance

Enums can conform to protocols using the `<-` operator or the `conforms` keyword:

```noir
enum NetworkError <- Error:
    ConnectionTimeout
    InvalidResponse
    ServerUnavailable
::

// Equivalent using 'conforms'
enum ValidationError conforms Error:
    InvalidInput
    MissingField
    TooLong
::
```

### Future Enhancements

In the future, we plan to implement:

1. Protocol implementation for enums with methods and properties
2. Pattern matching with `match` statements
3. Protocol composition
4. Default implementations for protocol methods
