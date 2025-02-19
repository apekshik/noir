// Require explicit conversions when going from Float or Double to Int, or between Float and Double.
a: Float = 3.14
b: Int = a as Int // Explicit conversion from Float to Int

c: Double = 3.141592653589793
d: Float = c as Float // Explicit conversion from Double to Float

e: Float = 2.71828
f: Double = e as Double // Explicit conversion from Float to Double