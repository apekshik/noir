// Complex Protocol Test
protocol HttpResponse:
    // Required property
    statusCode: Int
    
    // Required method
    getMessage() -> String
::

// Print success message
print("Complex protocol test complete!") 