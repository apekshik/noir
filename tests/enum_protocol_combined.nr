// Combined Enum and Protocol Test

// Define a simple Error protocol
protocol Error:
    // Required method
    getMessage() -> String
::

// Define an enum that conforms to the Error protocol
enum NetworkError <- Error:
    ConnectionTimeout
    InvalidResponse
    ServerUnavailable
::

// Define another enum that conforms to the Error protocol
enum ValidationError <- Error:
    InvalidInput
    MissingField
    TooLong
::

// Print success message
print("Combined enum and protocol test complete!") 