"""
Example Usage of RV-2AJ Serial Communication with Response Parser

This file demonstrates various ways to use the rv2aj_serial library
with the integrated response parser for the RV-2AJ robot controller.
"""

from rv2aj_serial import RV2AJSerial, RV2AJSerialException
from rv2aj_response_parser import RV2AJResponseParser


def example_basic_commands():
    """Example: Basic commands with automatic response parsing."""
    print("=" * 70)
    print("Example 1: Basic Commands with Automatic Parsing")
    print("=" * 70)
    
    try:
        # Create robot interface with parser enabled (default)
        robot = RV2AJSerial()
        robot.connect()
        
        # Send commands and get parsed responses
        print("\n1. Resetting alarm...")
        response = robot.reset_alarm()
        if response.is_success:
            print("   ✓ Alarm reset successful")
        elif response.is_error:
            print(f"   ✗ Error {response.error_code}: {response.error_message}")
        
        print("\n2. Turning on controller...")
        response = robot.control_on()
        if response.is_success:
            print("   ✓ Controller enabled")
        
        print("\n3. Turning on servos...")
        response = robot.servo_on()
        if response.is_success:
            print("   ✓ Servos enabled")
        
        print("\n4. Getting current position...")
        response = robot.get_position()
        if response.is_success:
            positions = robot.parser.parse_position(response.raw)
            if positions:
                print("   Joint Positions:")
                for joint, angle in sorted(positions.items()):
                    print(f"     {joint}: {angle:>8.2f}°")
        
        print("\n5. Turning off servos...")
        response = robot.servo_off()
        if response.is_success:
            print("   ✓ Servos disabled")
        
        robot.disconnect()
        print("\n✓ Example completed successfully\n")
        
    except RV2AJSerialException as e:
        print(f"   ✗ Error: {e}\n")


def example_error_handling():
    """Example: Comprehensive error handling."""
    print("=" * 70)
    print("Example 2: Error Handling")
    print("=" * 70)
    
    try:
        robot = RV2AJSerial()
        robot.connect()
        
        # Check for existing errors
        print("\n1. Checking for errors...")
        response = robot.get_error()
        
        if response.is_error:
            print(f"   ✗ Controller Error Detected!")
            print(f"     Code: {response.error_code}")
            print(f"     Level: {response.error_level} ", end="")
            
            if response.error_level == 'H':
                print("(High - Servo OFF)")
            elif response.error_level == 'L':
                print("(Low - Operation stopped)")
            elif response.error_level == 'C':
                print("(Warning - Operation continues)")
            
            if response.error_info:
                print(f"     Message: {response.error_info.message}")
                if response.error_info.cause:
                    print(f"     Cause: {response.error_info.cause}")
                if response.error_info.measures:
                    print(f"     Measures: {response.error_info.measures}")
                if response.error_info.power_cycle_reset:
                    print(f"     ⚠ Requires power cycle to reset")
        else:
            print("   ✓ No errors detected")
        
        robot.disconnect()
        print("\n✓ Example completed successfully\n")
        
    except RV2AJSerialException as e:
        print(f"   ✗ Error: {e}\n")


def example_position_monitoring():
    """Example: Monitor robot position."""
    print("=" * 70)
    print("Example 3: Position Monitoring")
    print("=" * 70)
    
    try:
        robot = RV2AJSerial()
        robot.connect()
        
        # Initialize robot
        print("\nInitializing robot...")
        robot.initialize_robot()
        
        # Monitor position
        print("\nReading current position (JPOSF):")
        response = robot.get_position()
        
        if response.is_success:
            print(f"  Raw response: {response.raw}")
            print(f"  Data dictionary: {response.data}")
            
            positions = robot.parser.parse_position(response.raw)
            if positions:
                print("\n  Parsed Joint Angles:")
                for joint in ['J1', 'J2', 'J3', 'J5', 'J6']:
                    if joint in positions:
                        angle = positions[joint]
                        print(f"    {joint}: {angle:>8.2f}°")
        
        # Get Cartesian coordinates
        print("\nReading Cartesian coordinates (WH):")
        response = robot.get_coordinates()
        
        if response.is_success:
            coords = robot.parser.parse_coordinates(response.raw)
            if coords:
                print("  XYZ Coordinates:")
                for axis in ['X', 'Y', 'Z']:
                    if axis in coords:
                        print(f"    {axis}: {coords[axis]:>8.2f} mm")
                print("  Orientation:")
                for axis in ['A', 'B', 'C']:
                    if axis in coords:
                        print(f"    {axis}: {coords[axis]:>8.2f}°")
        
        robot.shutdown_robot()
        robot.disconnect()
        print("\n✓ Example completed successfully\n")
        
    except RV2AJSerialException as e:
        print(f"   ✗ Error: {e}\n")


def example_custom_commands():
    """Example: Send custom commands with parsing."""
    print("=" * 70)
    print("Example 4: Custom Commands")
    print("=" * 70)
    
    try:
        robot = RV2AJSerial()
        robot.connect()
        
        # Send custom command
        print("\n1. Custom command with prefix:")
        response = robot.send_and_read("JPOSF", use_prefix=True)
        print(f"   Response type: {response.response_type.value}")
        print(f"   Is success: {response.is_success}")
        
        # Send command without prefix (if needed)
        print("\n2. Command without prefix:")
        response = robot.send_and_read("CUSTOM_CMD", use_prefix=False, parse=False)
        print(f"   Raw response: {response}")
        
        # Send and parse manually
        print("\n3. Manual parsing:")
        robot.send_command("JPOSF")
        import time
        time.sleep(0.2)
        raw_response = robot.read_response(parse=False)
        print(f"   Raw: {raw_response}")
        
        if robot.parser:
            parsed = robot.parser.parse(raw_response)
            print(f"   Parsed type: {parsed.response_type.value}")
            print(f"   Success: {parsed.is_success}")
        
        robot.disconnect()
        print("\n✓ Example completed successfully\n")
        
    except RV2AJSerialException as e:
        print(f"   ✗ Error: {e}\n")


def example_without_parser():
    """Example: Use library without automatic parsing (raw strings)."""
    print("=" * 70)
    print("Example 5: Without Parser (Raw String Mode)")
    print("=" * 70)
    
    try:
        # Disable parser to get raw string responses
        robot = RV2AJSerial(use_parser=False)
        robot.connect()
        
        print("\n1. Sending SRVON command...")
        response = robot.servo_on()
        print(f"   Raw response: '{response}'")
        print(f"   Type: {type(response)}")
        
        # Manual checking
        if response.startswith("QoK"):
            print("   ✓ Command successful (QoK)")
        elif response.startswith("QeR"):
            print("   ✗ Command failed (QeR)")
        
        print("\n2. Getting position...")
        response = robot.get_position()
        print(f"   Raw response: {response}")
        
        # Manual parsing of semicolon-delimited data
        if response.startswith("QoK"):
            data = response[3:].split(';')
            print(f"   Data parts: {data[:10]}...")  # Show first 10 parts
        
        robot.servo_off()
        robot.disconnect()
        print("\n✓ Example completed successfully\n")
        
    except RV2AJSerialException as e:
        print(f"   ✗ Error: {e}\n")


def example_context_manager():
    """Example: Using context manager for automatic cleanup."""
    print("=" * 70)
    print("Example 6: Context Manager Usage")
    print("=" * 70)
    
    try:
        # Context manager automatically connects and disconnects
        with RV2AJSerial() as robot:
            print("\n✓ Connected via context manager")
            
            # Use robot
            response = robot.control_on()
            if response.is_success:
                print("✓ Controller enabled")
            
            response = robot.servo_on()
            if response.is_success:
                print("✓ Servos enabled")
            
            # Position check
            pos_response = robot.get_position()
            if pos_response.is_success:
                print("✓ Position read successfully")
            
            # Cleanup
            robot.servo_off()
            print("✓ Servos disabled")
        
        print("✓ Automatically disconnected\n")
        
    except RV2AJSerialException as e:
        print(f"   ✗ Error: {e}\n")


def main():
    """Run all examples."""
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  RV-2AJ Serial Communication - Complete Examples".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print("\n")
    
    # Run examples
    # NOTE: Comment out examples if robot is not connected
    
    # example_basic_commands()
    # example_error_handling()
    # example_position_monitoring()
    # example_custom_commands()
    # example_without_parser()
    # example_context_manager()
    
    print("\n" + "=" * 70)
    print("To run examples, uncomment the function calls in main()")
    print("Make sure robot is connected on the configured COM port")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Demonstrate parser independently (without robot connection)
    print("\n" + "=" * 70)
    print("Response Parser Test (No Robot Required)")
    print("=" * 70 + "\n")
    
    parser = RV2AJResponseParser()
    
    # Test various response formats
    test_responses = [
        "QoK",
        "QeR6020",
        "QoK;J1;10.50;J2;-5.30;J3;45.00;J5;0.00;J6;90.00",
        "QoK;X;100.5;Y;200.3;Z;300.1;A;0.0;B;0.0;C;90.0",
        "QeR1110",
        "Q;1;2;3;4;5",
    ]
    
    for test_resp in test_responses:
        result = parser.parse(test_resp)
        print(f"Input:  {test_resp}")
        print(f"Type:   {result.response_type.value}")
        print(f"Status: {result}")
        if result.data:
            print(f"Data:   {result.data}")
        print()
    
    # Run main examples if desired
    main()
