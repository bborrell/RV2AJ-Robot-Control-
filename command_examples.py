"""
RV-2AJ Command Library - Usage Examples

Comprehensive examples demonstrating the high-level command interface.
"""

from rv2aj_commands import RV2AJCommands
from rv2aj_serial import RV2AJSerialException
import time


def example_basic_motion():
    """Example: Basic motion control."""
    print("=" * 70)
    print("Example 1: Basic Motion Control")
    print("=" * 70)
    
    try:
        robot = RV2AJCommands()
        robot.connect()
        
        # Initialize
        print("\n1. Initializing robot...")
        robot.initialize()
        print("   ✓ Robot initialized")
        
        # Get current position
        print("\n2. Reading current position...")
        response = robot.get_position()
        if response.is_success:
            positions = robot.parser.parse_position(response.raw)
            print("   Current joint angles:")
            for joint in ['J1', 'J2', 'J3', 'J5', 'J6']:
                if joint in positions:
                    print(f"     {joint}: {positions[joint]:>7.2f}°")
        
        # Move joints relatively
        print("\n3. Moving joints (relative)...")
        response = robot.move_joint(j1=5.0, j2=-3.0)
        if response.is_success:
            print("   ✓ Joint move complete")
        
        # Wait
        print("\n4. Waiting 1 second...")
        robot.timer(1.0)
        
        # Move back
        print("\n5. Moving joints back...")
        robot.move_joint(j1=-5.0, j2=3.0)
        
        # Shutdown
        print("\n6. Shutting down...")
        robot.shutdown()
        robot.disconnect()
        print("   ✓ Example complete\n")
        
    except RV2AJSerialException as e:
        print(f"   ✗ Error: {e}\n")


def example_position_teaching():
    """Example: Position teaching and recall."""
    print("=" * 70)
    print("Example 2: Position Teaching and Recall")
    print("=" * 70)
    
    try:
        with RV2AJCommands() as robot:
            robot.initialize()
            
            # Save current position
            print("\n1. Saving current position as P50...")
            response = robot.here(50)
            if response.is_success:
                print("   ✓ Position 50 saved")
            
            # Move joints
            print("\n2. Moving to new position...")
            robot.move_joint(j1=10.0, j2=15.0, j3=-10.0)
            time.sleep(1)
            
            # Save this position too
            print("\n3. Saving new position as P51...")
            robot.here(51)
            
            # Move back to P50
            print("\n4. Moving back to position 50...")
            response = robot.move_to_position(50)
            if response.is_success:
                print("   ✓ Moved to position 50")
            
            time.sleep(1)
            
            # Move to P51 with linear interpolation
            print("\n5. Moving straight to position 51...")
            robot.move_straight(51)
            
            robot.shutdown()
            print("\n✓ Example complete\n")
        
    except RV2AJSerialException as e:
        print(f"   ✗ Error: {e}\n")


def example_cartesian_motion():
    """Example: Cartesian space motion."""
    print("=" * 70)
    print("Example 3: Cartesian Space Motion")
    print("=" * 70)
    
    try:
        with RV2AJCommands() as robot:
            robot.initialize()
            
            # Get current Cartesian position
            print("\n1. Reading current Cartesian position...")
            response = robot.where()
            if response.is_success:
                coords = robot.parser.parse_coordinates(response.raw)
                print("   Current coordinates:")
                if coords:
                    for axis in ['X', 'Y', 'Z']:
                        if axis in coords:
                            print(f"     {axis}: {coords[axis]:>8.2f} mm")
                    for axis in ['A', 'B', 'C']:
                        if axis in coords:
                            print(f"     {axis}: {coords[axis]:>8.2f}°")
            
            # Move to specific Cartesian position
            print("\n2. Moving to Cartesian position...")
            robot.move_position(150.0, 200.0, 350.0, a=0.0, b=0.0, c=90.0)
            
            robot.shutdown()
            print("\n✓ Example complete\n")
        
    except RV2AJSerialException as e:
        print(f"   ✗ Error: {e}\n")


def example_gripper_control():
    """Example: Gripper/hand control."""
    print("=" * 70)
    print("Example 4: Gripper Control")
    print("=" * 70)
    
    try:
        with RV2AJCommands() as robot:
            robot.initialize()
            
            print("\n1. Opening gripper...")
            response = robot.grip_open()
            if response.is_success:
                print("   ✓ Gripper opened")
            
            time.sleep(1)
            
            print("\n2. Closing gripper...")
            response = robot.grip_close()
            if response.is_success:
                print("   ✓ Gripper closed")
            
            time.sleep(1)
            
            # Set grip pressure (if supported)
            print("\n3. Setting grip pressure...")
            robot.grip_pressure(50, 50, 50)
            
            robot.shutdown()
            print("\n✓ Example complete\n")
        
    except RV2AJSerialException as e:
        print(f"   ✗ Error: {e}\n")


def example_speed_control():
    """Example: Speed and override control."""
    print("=" * 70)
    print("Example 5: Speed Control")
    print("=" * 70)
    
    try:
        with RV2AJCommands() as robot:
            robot.initialize()
            
            # Set to slow speed
            print("\n1. Setting speed to 25%...")
            robot.set_speed(25)
            
            # Move slowly
            print("\n2. Moving slowly...")
            robot.move_joint(j1=5.0)
            time.sleep(2)
            
            # Increase speed
            print("\n3. Setting speed to 75%...")
            robot.set_speed(75)
            
            # Move faster
            print("\n4. Moving faster...")
            robot.move_joint(j1=-5.0)
            
            # Set override
            print("\n5. Setting override to 50%...")
            robot.set_override(50)
            
            robot.shutdown()
            print("\n✓ Example complete\n")
        
    except RV2AJSerialException as e:
        print(f"   ✗ Error: {e}\n")


def example_io_control():
    """Example: I/O operations."""
    print("=" * 70)
    print("Example 6: I/O Control")
    print("=" * 70)
    
    try:
        with RV2AJCommands() as robot:
            robot.connect()
            
            # Turn on output bits
            print("\n1. Turning ON output bit 1...")
            robot.output_bit(1, True)
            
            print("\n2. Turning ON output bit 2...")
            robot.output_bit(2, True)
            
            time.sleep(1)
            
            # Turn off output bits
            print("\n3. Turning OFF output bit 1...")
            robot.output_bit(1, False)
            
            print("\n4. Turning OFF output bit 2...")
            robot.output_bit(2, False)
            
            # Read input bit
            print("\n5. Reading input bit 1...")
            response = robot.input_direct(1)
            if response.is_success:
                print(f"   Input bit 1 state: {response.raw}")
            
            robot.disconnect()
            print("\n✓ Example complete\n")
        
    except RV2AJSerialException as e:
        print(f"   ✗ Error: {e}\n")


def example_tool_setup():
    """Example: Tool configuration."""
    print("=" * 70)
    print("Example 7: Tool Configuration")
    print("=" * 70)
    
    try:
        with RV2AJCommands() as robot:
            robot.connect()
            
            # Set tool length
            print("\n1. Setting tool length to 50.0 mm...")
            robot.set_tool_length(50.0)
            
            # Set tool transformation
            print("\n2. Setting tool coordinate system...")
            robot.set_tool_matrix(
                x=0.0, y=0.0, z=50.0,  # 50mm offset in Z
                a=0.0, b=0.0, c=0.0     # No rotation
            )
            
            robot.disconnect()
            print("\n✓ Example complete\n")
        
    except RV2AJSerialException as e:
        print(f"   ✗ Error: {e}\n")


def example_error_handling():
    """Example: Error checking and handling."""
    print("=" * 70)
    print("Example 8: Error Handling")
    print("=" * 70)
    
    try:
        robot = RV2AJCommands()
        robot.connect()
        
        # Check for errors
        print("\n1. Checking for errors...")
        response = robot.get_error()
        
        if response.is_error:
            print("   ✗ Error detected!")
            print(f"     Code: {response.error_code}")
            print(f"     Level: {response.error_level}")
            
            if response.error_info:
                print(f"     Message: {response.error_info.message}")
                print(f"     Cause: {response.error_info.cause}")
                print(f"     Measures: {response.error_info.measures}")
                
                if response.error_info.power_cycle_reset:
                    print("     ⚠ Requires power cycle to reset")
            
            # Try to reset alarm
            print("\n2. Attempting to reset alarm...")
            reset_response = robot.reset_alarm()
            if reset_response.is_success:
                print("   ✓ Alarm reset successful")
        else:
            print("   ✓ No errors detected")
        
        # Check version
        print("\n3. Reading controller version...")
        version_response = robot.get_version()
        if version_response.is_success:
            print(f"   Version: {version_response.raw}")
        
        robot.disconnect()
        print("\n✓ Example complete\n")
        
    except RV2AJSerialException as e:
        print(f"   ✗ Error: {e}\n")


def example_complex_sequence():
    """Example: Complex motion sequence."""
    print("=" * 70)
    print("Example 9: Complex Motion Sequence")
    print("=" * 70)
    
    try:
        with RV2AJCommands() as robot:
            robot.initialize()
            
            print("\n1. Pick and place sequence...")
            
            # Move to home position
            print("   → Moving to home position")
            robot.move_to_position(1)
            
            # Open gripper
            print("   → Opening gripper")
            robot.grip_open()
            
            # Move to pick position
            print("   → Moving to pick position")
            robot.move_to_position(10)
            
            # Close gripper
            print("   → Closing gripper")
            robot.grip_close()
            robot.timer(0.5)
            
            # Lift
            print("   → Lifting")
            robot.move_joint(j3=-10.0)
            
            # Move to place position
            print("   → Moving to place position")
            robot.move_to_position(20)
            
            # Open gripper
            print("   → Opening gripper")
            robot.grip_open()
            robot.timer(0.5)
            
            # Return home
            print("   → Returning home")
            robot.move_to_position(1)
            
            robot.shutdown()
            print("\n✓ Example complete\n")
        
    except RV2AJSerialException as e:
        print(f"   ✗ Error: {e}\n")


def example_custom_command():
    """Example: Sending custom commands."""
    print("=" * 70)
    print("Example 10: Custom Commands")
    print("=" * 70)
    
    try:
        with RV2AJCommands() as robot:
            robot.connect()
            
            # Send a custom command
            print("\n1. Sending custom command (JPOSF)...")
            response = robot.send_command("JPOSF")
            
            if response.is_success:
                print("   ✓ Command successful")
                print(f"   Data: {response.data}")
                
                # Parse position manually
                positions = robot.parser.parse_position(response.raw)
                if positions:
                    print("   Parsed positions:")
                    for joint, angle in sorted(positions.items()):
                        print(f"     {joint}: {angle:>7.2f}°")
            
            # Send raw command without prefix (advanced)
            print("\n2. Sending raw command...")
            response = robot.send_command("STATUS", use_prefix=False, parse=False)
            print(f"   Raw response: {response}")
            
            robot.disconnect()
            print("\n✓ Example complete\n")
        
    except RV2AJSerialException as e:
        print(f"   ✗ Error: {e}\n")


def main():
    """Main function to run selected examples."""
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  RV-2AJ Command Library - Usage Examples".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print("\n")
    
    # Uncomment the examples you want to run
    # NOTE: Make sure robot is connected before running!
    
    # example_basic_motion()
    # example_position_teaching()
    # example_cartesian_motion()
    # example_gripper_control()
    # example_speed_control()
    # example_io_control()
    # example_tool_setup()
    # example_error_handling()
    # example_complex_sequence()
    # example_custom_command()
    
    print("\n" + "=" * 70)
    print("To run examples, uncomment the function calls in main()")
    print("Make sure robot is connected on the configured COM port")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
