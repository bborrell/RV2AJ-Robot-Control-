"""
RV-2AJ Robot Control - Main Application

Interactive control program for the Mitsubishi RV-2AJ robot.
Brings together all the libraries for easy robot operation.

Author: Auto-generated
Date: 2026-02-15
"""

import sys
import time
from typing import Optional
from rv2aj_commands import RV2AJCommands
from rv2aj_serial import RV2AJSerialException


class RobotControlApp:
    """Main application for RV-2AJ robot control."""
    
    def __init__(self):
        self.robot: Optional[RV2AJCommands] = None
        self.connected = False
        self.initialized = False
    
    def clear_screen(self):
        """Clear the terminal screen."""
        print("\n" * 2)
    
    def print_header(self):
        """Print application header."""
        print("=" * 70)
        print("            RV-2AJ Robot Control System".center(70))
        print("=" * 70)
    
    def print_status(self):
        """Print current robot status."""
        conn_status = "✓ Connected" if self.connected else "✗ Disconnected"
        init_status = "✓ Initialized" if self.initialized else "✗ Not Initialized"
        
        print(f"\nStatus: {conn_status} | {init_status}")
        print("-" * 70)
    
    def print_menu(self):
        """Print main menu."""
        print("\nMain Menu:")
        print("  1. Connect to Robot")
        print("  2. Initialize Robot (Reset alarm, Enable servos)")
        print("  3. Get Current Position")
        print("  4. Move Joints (Relative)")
        print("  5. Save Current Position")
        print("  6. Move to Saved Position")
        print("  7. Gripper Control")
        print("  8. Speed Control")
        print("  9. I/O Control")
        print(" 10. Check for Errors")
        print(" 11. Manual Command")
        print(" 12. Run Pick & Place Demo")
        print(" 13. Shutdown Robot")
        print("  0. Exit")
        print("-" * 70)
    
    def connect_robot(self):
        """Connect to the robot."""
        print("\n→ Connecting to robot...")
        try:
            if self.robot is None:
                self.robot = RV2AJCommands()
            
            self.robot.connect()
            self.connected = True
            print("✓ Successfully connected to robot!")
            time.sleep(1)
        except RV2AJSerialException as e:
            print(f"✗ Connection failed: {e}")
            print("  • Check COM port in rv2aj_config.json")
            print("  • Verify robot controller is powered on")
            print("  • Ensure cable is connected")
            time.sleep(2)
    
    def initialize_robot(self):
        """Initialize the robot."""
        if not self.connected:
            print("✗ Robot not connected! Connect first.")
            time.sleep(1)
            return
        
        print("\n→ Initializing robot...")
        print("  1. Resetting alarms...")
        
        try:
            responses = self.robot.initialize()
            
            print("  2. Enabling controller...")
            print("  3. Turning on servos...")
            
            # Check if initialization was successful
            all_success = True
            for cmd, response in responses.items():
                if hasattr(response, 'is_success'):
                    if not response.is_success:
                        all_success = False
                        print(f"  ✗ {cmd} failed")
            
            if all_success:
                self.initialized = True
                print("✓ Robot initialized successfully!")
            else:
                print("⚠ Initialization completed with warnings")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"✗ Initialization failed: {e}")
            time.sleep(2)
    
    def get_position(self):
        """Get and display current position."""
        if not self.connected or not self.initialized:
            print("✗ Robot must be connected and initialized!")
            time.sleep(1)
            return
        
        print("\n→ Reading current position...")
        
        try:
            # Get joint positions
            response = self.robot.get_position()
            
            if response.is_success:
                positions = self.robot.parser.parse_position(response.raw)
                
                if positions:
                    print("\n  Joint Positions:")
                    for joint in ['J1', 'J2', 'J3', 'J5', 'J6']:
                        if joint in positions:
                            print(f"    {joint}: {positions[joint]:>8.2f}°")
                else:
                    print(f"  Raw response: {response.raw}")
            else:
                print(f"✗ Failed to get position: {response}")
            
            # Get Cartesian coordinates
            print("\n→ Reading Cartesian coordinates...")
            coord_response = self.robot.where()
            
            if coord_response.is_success:
                coords = self.robot.parser.parse_coordinates(coord_response.raw)
                
                if coords:
                    print("\n  Cartesian Position:")
                    for axis in ['X', 'Y', 'Z']:
                        if axis in coords:
                            print(f"    {axis}: {coords[axis]:>8.2f} mm")
                    print("\n  Orientation:")
                    for axis in ['A', 'B', 'C']:
                        if axis in coords:
                            print(f"    {axis}: {coords[axis]:>8.2f}°")
            
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            time.sleep(2)
    
    def move_joints(self):
        """Move joints with user input."""
        if not self.connected or not self.initialized:
            print("✗ Robot must be connected and initialized!")
            time.sleep(1)
            return
        
        print("\n→ Move Joints (Relative)")
        print("  Enter joint angles in degrees (leave blank to skip)")
        print("  Note: Movements are relative to current position")
        
        try:
            j1_str = input("  J1 (degrees): ").strip()
            j2_str = input("  J2 (degrees): ").strip()
            j3_str = input("  J3 (degrees): ").strip()
            j5_str = input("  J5 (degrees): ").strip()
            j6_str = input("  J6 (degrees): ").strip()
            
            j1 = float(j1_str) if j1_str else None
            j2 = float(j2_str) if j2_str else None
            j3 = float(j3_str) if j3_str else None
            j5 = float(j5_str) if j5_str else None
            j6 = float(j6_str) if j6_str else None
            
            if all(v is None for v in [j1, j2, j3, j5, j6]):
                print("  No movements specified.")
                time.sleep(1)
                return
            
            print("\n  Moving robot...")
            response = self.robot.move_joint(j1=j1, j2=j2, j3=j3, j5=j5, j6=j6)
            
            if response.is_success:
                print("✓ Movement completed!")
            else:
                print(f"✗ Movement failed: {response}")
            
            time.sleep(1)
            
        except ValueError:
            print("✗ Invalid input! Please enter numbers only.")
            time.sleep(2)
        except Exception as e:
            print(f"✗ Error: {e}")
            time.sleep(2)
    
    def save_position(self):
        """Save current position."""
        if not self.connected or not self.initialized:
            print("✗ Robot must be connected and initialized!")
            time.sleep(1)
            return
        
        print("\n→ Save Current Position")
        
        try:
            pos_str = input("  Position number (1-999): ").strip()
            position = int(pos_str)
            
            if position < 1 or position > 999:
                print("✗ Position must be between 1 and 999")
                time.sleep(1)
                return
            
            print(f"  Saving to position {position}...")
            response = self.robot.here(position)
            
            if response.is_success:
                print(f"✓ Current position saved as P{position}!")
            else:
                print(f"✗ Failed to save position: {response}")
            
            time.sleep(1)
            
        except ValueError:
            print("✗ Invalid position number!")
            time.sleep(2)
        except Exception as e:
            print(f"✗ Error: {e}")
            time.sleep(2)
    
    def move_to_position(self):
        """Move to a saved position."""
        if not self.connected or not self.initialized:
            print("✗ Robot must be connected and initialized!")
            time.sleep(1)
            return
        
        print("\n→ Move to Saved Position")
        
        try:
            pos_str = input("  Position number (1-999): ").strip()
            position = int(pos_str)
            
            if position < 1 or position > 999:
                print("✗ Position must be between 1 and 999")
                time.sleep(1)
                return
            
            print(f"  Moving to position P{position}...")
            response = self.robot.move_to_position(position)
            
            if response.is_success:
                print(f"✓ Moved to position P{position}!")
            else:
                print(f"✗ Movement failed: {response}")
            
            time.sleep(1)
            
        except ValueError:
            print("✗ Invalid position number!")
            time.sleep(2)
        except Exception as e:
            print(f"✗ Error: {e}")
            time.sleep(2)
    
    def gripper_control(self):
        """Control gripper."""
        if not self.connected or not self.initialized:
            print("✗ Robot must be connected and initialized!")
            time.sleep(1)
            return
        
        print("\n→ Gripper Control")
        print("  1. Open Gripper")
        print("  2. Close Gripper")
        print("  0. Back")
        
        choice = input("\nSelect option: ").strip()
        
        try:
            if choice == "1":
                print("  Opening gripper...")
                response = self.robot.grip_open()
                if response.is_success:
                    print("✓ Gripper opened!")
                else:
                    print(f"✗ Failed: {response}")
            
            elif choice == "2":
                print("  Closing gripper...")
                response = self.robot.grip_close()
                if response.is_success:
                    print("✓ Gripper closed!")
                else:
                    print(f"✗ Failed: {response}")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"✗ Error: {e}")
            time.sleep(2)
    
    def speed_control(self):
        """Control robot speed."""
        if not self.connected or not self.initialized:
            print("✗ Robot must be connected and initialized!")
            time.sleep(1)
            return
        
        print("\n→ Speed Control")
        
        try:
            speed_str = input("  Enter speed (1-100%): ").strip()
            speed = int(speed_str)
            
            if speed < 1 or speed > 100:
                print("✗ Speed must be between 1 and 100")
                time.sleep(1)
                return
            
            print(f"  Setting speed to {speed}%...")
            response = self.robot.set_speed(speed)
            
            if response.is_success:
                print(f"✓ Speed set to {speed}%!")
            else:
                print(f"✗ Failed: {response}")
            
            time.sleep(1)
            
        except ValueError:
            print("✗ Invalid speed value!")
            time.sleep(2)
        except Exception as e:
            print(f"✗ Error: {e}")
            time.sleep(2)
    
    def io_control(self):
        """Control I/O."""
        if not self.connected:
            print("✗ Robot must be connected!")
            time.sleep(1)
            return
        
        print("\n→ I/O Control")
        print("  1. Turn ON output bit")
        print("  2. Turn OFF output bit")
        print("  3. Read input bit")
        print("  0. Back")
        
        choice = input("\nSelect option: ").strip()
        
        try:
            if choice == "1":
                bit_str = input("  Output bit number: ").strip()
                bit = int(bit_str)
                print(f"  Turning ON output bit {bit}...")
                response = self.robot.output_bit(bit, True)
                if response.is_success:
                    print(f"✓ Output bit {bit} is ON")
                else:
                    print(f"✗ Failed: {response}")
            
            elif choice == "2":
                bit_str = input("  Output bit number: ").strip()
                bit = int(bit_str)
                print(f"  Turning OFF output bit {bit}...")
                response = self.robot.output_bit(bit, False)
                if response.is_success:
                    print(f"✓ Output bit {bit} is OFF")
                else:
                    print(f"✗ Failed: {response}")
            
            elif choice == "3":
                bit_str = input("  Input bit number: ").strip()
                bit = int(bit_str)
                print(f"  Reading input bit {bit}...")
                response = self.robot.input_direct(bit)
                print(f"  Response: {response.raw}")
            
            time.sleep(2)
            
        except ValueError:
            print("✗ Invalid bit number!")
            time.sleep(2)
        except Exception as e:
            print(f"✗ Error: {e}")
            time.sleep(2)
    
    def check_errors(self):
        """Check for robot errors."""
        if not self.connected:
            print("✗ Robot must be connected!")
            time.sleep(1)
            return
        
        print("\n→ Checking for errors...")
        
        try:
            response = self.robot.get_error()
            
            if response.is_error:
                print("\n✗ Error Detected!")
                print(f"  Code: {response.error_code}")
                print(f"  Level: {response.error_level} ", end="")
                
                if response.error_level == 'H':
                    print("(High - Servo OFF)")
                elif response.error_level == 'L':
                    print("(Low - Operation stopped)")
                elif response.error_level == 'C':
                    print("(Warning - Operation continues)")
                else:
                    print()
                
                if response.error_info:
                    print(f"\n  Message: {response.error_info.message}")
                    if response.error_info.cause:
                        print(f"  Cause: {response.error_info.cause}")
                    if response.error_info.measures:
                        print(f"  Measures: {response.error_info.measures}")
                    if response.error_info.power_cycle_reset:
                        print("  ⚠ Requires power cycle to reset")
                
                reset = input("\n  Try to reset alarm? (y/n): ").strip().lower()
                if reset == 'y':
                    print("  Resetting alarm...")
                    reset_response = self.robot.reset_alarm()
                    if reset_response.is_success:
                        print("✓ Alarm reset successful!")
                    else:
                        print("✗ Alarm reset failed")
            else:
                print("✓ No errors detected!")
                print(f"  Response: {response.raw}")
            
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            time.sleep(2)
    
    def manual_command(self):
        """Send a manual command."""
        if not self.connected:
            print("✗ Robot must be connected!")
            time.sleep(1)
            return
        
        print("\n→ Manual Command")
        print("  Enter raw command (without prefix)")
        
        command = input("  Command: ").strip()
        
        if not command:
            return
        
        try:
            print(f"  Sending: {command}")
            response = self.robot.send_command(command)
            
            print(f"\n  Response: {response.raw}")
            print(f"  Type: {response.response_type.value}")
            print(f"  Success: {response.is_success}")
            
            if response.data:
                print(f"  Data: {response.data}")
            
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            time.sleep(2)
    
    def run_demo(self):
        """Run pick and place demo."""
        if not self.connected or not self.initialized:
            print("✗ Robot must be connected and initialized!")
            time.sleep(1)
            return
        
        print("\n→ Pick & Place Demo")
        print("\n  This demo will:")
        print("  1. Move to home position (P1)")
        print("  2. Open gripper")
        print("  3. Move to pick position (P10)")
        print("  4. Close gripper")
        print("  5. Move to place position (P20)")
        print("  6. Open gripper")
        print("  7. Return to home (P1)")
        print("\n  Make sure positions P1, P10, and P20 are defined!")
        
        confirm = input("\n  Continue? (y/n): ").strip().lower()
        
        if confirm != 'y':
            return
        
        try:
            print("\n  Starting demo...")
            
            print("  → Moving to home position...")
            self.robot.move_to_position(1)
            time.sleep(1)
            
            print("  → Opening gripper...")
            self.robot.grip_open()
            time.sleep(0.5)
            
            print("  → Moving to pick position...")
            self.robot.move_to_position(10)
            time.sleep(1)
            
            print("  → Closing gripper...")
            self.robot.grip_close()
            time.sleep(0.5)
            
            print("  → Lifting...")
            self.robot.move_joint(j3=-5.0)
            time.sleep(1)
            
            print("  → Moving to place position...")
            self.robot.move_to_position(20)
            time.sleep(1)
            
            print("  → Opening gripper...")
            self.robot.grip_open()
            time.sleep(0.5)
            
            print("  → Returning home...")
            self.robot.move_to_position(1)
            
            print("\n✓ Demo completed successfully!")
            time.sleep(2)
            
        except Exception as e:
            print(f"\n✗ Demo failed: {e}")
            time.sleep(2)
    
    def shutdown_robot(self):
        """Safely shutdown the robot."""
        if not self.connected:
            print("✗ Robot not connected!")
            time.sleep(1)
            return
        
        print("\n→ Shutting down robot...")
        
        try:
            response = self.robot.shutdown()
            self.initialized = False
            print("✓ Robot shutdown complete!")
            time.sleep(1)
            
        except Exception as e:
            print(f"✗ Error: {e}")
            time.sleep(2)
    
    def disconnect(self):
        """Disconnect from robot."""
        if self.robot and self.connected:
            print("\n→ Disconnecting...")
            self.robot.disconnect()
            self.connected = False
            self.initialized = False
            print("✓ Disconnected")
    
    def run(self):
        """Run the main application loop."""
        try:
            while True:
                self.clear_screen()
                self.print_header()
                self.print_status()
                self.print_menu()
                
                choice = input("\nSelect option: ").strip()
                
                if choice == "0":
                    print("\n→ Exiting application...")
                    self.disconnect()
                    print("Goodbye!")
                    break
                
                elif choice == "1":
                    self.connect_robot()
                
                elif choice == "2":
                    self.initialize_robot()
                
                elif choice == "3":
                    self.get_position()
                
                elif choice == "4":
                    self.move_joints()
                
                elif choice == "5":
                    self.save_position()
                
                elif choice == "6":
                    self.move_to_position()
                
                elif choice == "7":
                    self.gripper_control()
                
                elif choice == "8":
                    self.speed_control()
                
                elif choice == "9":
                    self.io_control()
                
                elif choice == "10":
                    self.check_errors()
                
                elif choice == "11":
                    self.manual_command()
                
                elif choice == "12":
                    self.run_demo()
                
                elif choice == "13":
                    self.shutdown_robot()
                
                else:
                    print("\n✗ Invalid option!")
                    time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\n→ Interrupted by user...")
            self.disconnect()
            print("Goodbye!")
        
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
            self.disconnect()
            sys.exit(1)


def main():
    """Main entry point."""
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  RV-2AJ Robot Control System".center(68) + "*")
    print("*" + "  Interactive Control Application".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print("\n")
    print("Select Interface Mode:")
    print("  1. GUI (Graphical User Interface)")
    print("  2. CLI (Console/Terminal Interface)")
    print("  0. Exit")
    print()
    
    choice = input("Select mode (1/2): ").strip()
    
    if choice == "1":
        print("\nLaunching GUI...")
        try:
            from rv2aj_gui import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"Error: Could not import GUI module: {e}")
            print("Make sure tkinter is installed (comes with Python)")
            sys.exit(1)
    
    elif choice == "2":
        print("\nLoading CLI...")
        time.sleep(1)
        app = RobotControlApp()
        app.run()
    
    elif choice == "0":
        print("Goodbye!")
        sys.exit(0)
    
    else:
        print("Invalid choice!")
        sys.exit(1)


if __name__ == "__main__":
    main()
