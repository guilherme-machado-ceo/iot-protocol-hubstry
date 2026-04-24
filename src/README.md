# Harmonic Protocol - C++ Implementation

This directory contains the C++ proof-of-concept implementation of the Harmonic IoT Protocol.

## Building the Project

### Option 1: Using CMake (Recommended)
```bash
mkdir build
cd build
cmake ..
cmake --build .
```

### Option 2: Direct Compilation
```bash
# Using GCC/Clang
g++ -std=c++17 -Wall -Wextra -o harmonic_protocol main.cpp

# Using MSVC
cl /EHsc /std:c++17 main.cpp /Fe:harmonic_protocol.exe
```

## Running the Demo

```bash
./harmonic_protocol        # Linux/macOS
harmonic_protocol.exe      # Windows
```

## Code Structure

- **`main.cpp`**: Complete implementation with namespace organization
- **`CMakeLists.txt`**: Cross-platform build configuration

## Features Demonstrated

- **Harmonic Channel Assignment**: Different device types use specific harmonic frequencies
- **Encoding/Decoding**: Messages are encoded using harmonic frequency offsets
- **Multi-Channel Testing**: Demonstrates sensor, actuator, and security channels
- **Frequency Calculation**: Shows actual frequencies for each harmonic

## Sample Output

The demo shows encoding and decoding across different harmonic channels:
- **H8 (8 kHz)**: Data stream channel
- **H3 (3 kHz)**: Temperature sensor channel  
- **H5 (5 kHz)**: LED actuator channel
- **H7 (7 kHz)**: Security channel

Each test case displays the harmonic analysis with actual frequencies and validates the encoding/decoding process.

## Next Steps

This proof-of-concept demonstrates the core mathematical principles. A production implementation would include:

- Real frequency modulation/demodulation
- FFT-based signal processing
- Network synchronization protocols
- Error correction and detection
- Multi-device coordination
- Hardware abstraction layers
