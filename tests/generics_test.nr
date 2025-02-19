// Simple types
x: Int = 0
y: String = ""

// Generic collections
numbers: [Int] = []                    // Array of integers
pairs: [String: Int] = []             // Dictionary
uniqueItems: Set<String> = empty      // Set of strings
orderedNums: OSet<Int> = empty       // Ordered set of integers

// Generic type parameters
data: Collection<T> = empty              // Generic collection
pairs: KeyValue<K, V> = empty           // Generic key-value pairs
nested: Tree<Node<T>> = empty           // Nested generic type