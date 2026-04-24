[![Language: PT](https://img.shields.io/badge/lang-PT-green.svg)](../pt/Tests.md) | **EN**

# Harmonic IoT Protocol - Test Cases

This document outlines the test cases for the Harmonic IoT Protocol based on the approved Product Requirements Document (PRD).

## 1. Functional Test Cases

| Test Case ID | Requirement ID | Test Scenario | Test Steps | Expected Result |
| :--- | :--- | :--- | :--- | :--- |
| TC-FR-001 | FR1 | Verify Fundamental Frequency (f₀) Synchronization | 1. Designate one node as the Master. <br> 2. Configure the Master to broadcast f₀ = 1 kHz. <br> 3. Power on three Slave nodes. <br> 4. Query the synchronized frequency of each Slave node. | All three Slave nodes report a synchronized frequency of 1 kHz within a +/- 0.1% tolerance. |
| TC-FR-002 | FR2 | Verify Harmonic Channel to Function Mapping | 1. Configure the network with f₀ = 1kHz. <br> 2. Map H2 (2kHz) to "read_temperature" on Device A. <br> 3. Map H3 (3kHz) to "toggle_led" on Device B. <br> 4. Send a generic "read" command on H3. <br> 5. Send a "toggle" command on H2. | Device B (LED) does not respond. Device A (temp) does not respond. The system correctly isolates functions to their mapped harmonics. |
| TC-FR-003 | FR3 & FR4 | Test End-to-End Harmonic Encoding and Decoding | 1. Configure network with f₀ = 1kHz. <br> 2. Assign Device A to H4 (4kHz). <br> 3. Instruct Device A to transmit the value "123". <br> 4. A Gateway node listens for all harmonic traffic. | The Gateway correctly isolates the signal on H4 and decodes the payload as "123". No data is detected on other harmonics from Device A. |
| TC-FR-004 | FR5 | Verify Omnichannel Routing | 1. A LoRa sensor (Device L) is on H5. A Wi-Fi actuator (Device W) is on H10. <br> 2. Device L transmits sensor data on H5. <br> 3. Configure the Gateway to route any data from H5 to H10. | The Gateway receives the LoRa transmission on H5, decodes it, re-encodes it, and transmits it to Device W over Wi-Fi on H10. |
| TC-FR-005 | FR6 | Test Harmonic Signature Authentication | 1. Define Device A's signature as a simultaneous transmission on H2 and H7. <br> 2. Device A transmits a valid payload on H2 and H7. <br> 3. A rogue Device B attempts to transmit on H2 only. | The Gateway accepts the transmission from Device A. The Gateway rejects or flags the transmission from Device B as "unauthenticated". |
| TC-FR-006 | FR7 | Test Spectral Intrusion Detection | 1. Establish a valid network using H2, H3, and H4. <br> 2. Introduce a rogue transmitter broadcasting a strong signal on H5 (an unassigned channel). | The Gateway's monitoring system immediately flags an "Unauthorized Spectral Event" on frequency 5 * f₀. |

## 2. Non-Functional Test Cases

| Test Case ID | Requirement ID | Test Scenario | Test Steps | Expected Result |
| :--- | :--- | :--- | :--- | :--- |
| TC-NFR-001 | NFR1 | Test Robustness Against Interference | 1. Set up a communication link on H3 (3kHz). <br> 2. Introduce a known interfering RF signal at 3.1 kHz. <br> 3. Transmit 10,000 packets. | The Bit Error Rate (BER) remains below the specified acceptable threshold (e.g., < 10^-5), demonstrating the protocol's ability to reject adjacent-frequency noise. |
| TC-NFR-002 | NFR2 | Test Scalability of Harmonic Channels | 1. Configure a network and simulate the addition of devices on 1,000 different harmonic channels. <br> 2. Command a transmission from a device on H999. | The system successfully processes the transmission on H999 without significant increase in latency or processing load on the gateway. |
| TC-NFR-003 | NFR3 | Measure Real-Time Latency | 1. Trigger a sensor event on Device A. <br> 2. Measure the time from the trigger to the successful reception and decoding of the data at the Gateway. | The total end-to-end latency is less than 50ms. |

## 3. Implementation Test Cases

| Test Case ID | Requirement ID | Test Scenario | Test Steps | Expected Result |
| :--- | :--- | :--- | :--- | :--- |
| TC-IMP-001 | DS1 | Verify C++ Prototype Compilation | 1. Navigate to the `src/` directory. <br> 2. Run the build command (e.g., `make` or `g++`). | The C++ prototype code compiles successfully without errors or warnings. |