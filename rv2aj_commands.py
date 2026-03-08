"""
RV-2AJ Command Library

High-level command interface for the Mitsubishi RV-2AJ robot.
Provides easy-to-use methods for all robot commands including:
- Motion commands (move, position control)
- Program control (branching, loops)
- Hand/Gripper control
- I/O operations
- Status queries

RS-232 COMMAND RULE:
Commands are sent as-is with robot/slot prefix (e.g., "1;1;") and do NOT
require "EXEC" to be prepended to command words.

Examples:
    - "HE 1" is sent as "1;1;HE 1"
    - "MJ 10,20" is sent as "1;1;MJ 10,20"
    - "CNTLON" is sent as "1;1;CNTLON"

Response Format:
  - QoK - Success response (command executed)
  - QeRXXXX - Error response (XXXX = error code)
  - Q... - Data response (query results)

Usage:
    from rv2aj_commands import RV2AJCommands
    
    robot = RV2AJCommands()
    robot.connect()
    robot.servo_on()  # Sends: 1;1;SRVON
    robot.move_joint(j1=10.0, j2=20.0)  # Sends: 1;1;MJ 10.00,20.00
    robot.disconnect()
"""

from typing import Optional, List, Dict, Any, Tuple, Union
from rv2aj_serial import RV2AJSerial, RV2AJSerialException
from rv2aj_response_parser import ParsedResponse


class RV2AJCommands:
    """
    High-level command interface for RV-2AJ robot controller.
    
    This class provides convenient methods for all robot commands,
    handling parameter formatting and response parsing automatically.
    """
    
    def __init__(self, config_path: str = "RV2AJ_Reference_JSONs/rv2aj_config.json", 
                 use_parser: bool = True, verbose_callback=None):
        """
        Initialize the command interface.
        
        Args:
            config_path: Path to configuration JSON file
            use_parser: Enable automatic response parsing
            verbose_callback: Optional callback function for verbose logging (func(message: str))
        """
        self.serial = RV2AJSerial(config_path=config_path, use_parser=use_parser, 
                                   verbose_callback=verbose_callback)
        self.parser = self.serial.parser
    
    def set_verbose_callback(self, callback):
        """Set or update the verbose logging callback."""
        self.serial.verbose_callback = callback

    def _send_edit_slot_command(self, command: str):
        """Send command explicitly to edit slot (typically TASKMAX+1 => 9)."""
        raw_prefix = getattr(self.serial, 'prefix', '1;1;')
        robot_id = str(raw_prefix).split(';')[0].strip() or '1'
        edit_slot = int(getattr(self.serial, 'edit_slot', 9))
        full_command = f"{robot_id};{edit_slot};{command}"
        return self.serial.send_and_read(full_command, use_prefix=False)

    def _send_edit_command_with_slot_fallback(self, command: str):
        """Send edit command to configured edit slot, fallback to default prefix slot if needed."""
        primary_response = self._send_edit_slot_command(command)

        is_error = bool(getattr(primary_response, 'is_error', False))
        raw_text = getattr(primary_response, 'raw', '') if hasattr(primary_response, 'raw') else str(primary_response)
        if "QER" in str(raw_text).upper():
            is_error = True

        if not is_error:
            return primary_response

        raw_prefix = getattr(self.serial, 'prefix', '1;1;')
        prefix_parts = str(raw_prefix).split(';')
        default_slot = 1
        if len(prefix_parts) > 1:
            try:
                default_slot = int(prefix_parts[1])
            except (TypeError, ValueError):
                default_slot = 1

        edit_slot = int(getattr(self.serial, 'edit_slot', 9))
        if default_slot == edit_slot:
            return primary_response

        fallback_response = self.serial.send_and_read(command)
        return fallback_response
    
    # ========================================================================
    # Connection Management
    # ========================================================================
    
    def connect(self) -> bool:
        """
        Connect to the robot controller.
        
        Returns:
            True if connection successful
        """
        return self.serial.connect()
    
    def disconnect(self) -> None:
        """Disconnect from the robot controller."""
        self.serial.disconnect()
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    # ========================================================================
    # Servo and Motion Control
    # ========================================================================
    
    def servo_on(self):
        """Turn on robot servos (SRVON)."""
        return self.serial.send_and_read("SRVON")
    
    def servo_off(self):
        """Turn off robot servos (SRVOFF)."""
        return self.serial.send_and_read("SRVOFF")
    
    def control_on(self):
        """Turn on controller (CNTLON)."""
        return self.serial.send_and_read("CNTLON")

    def control_off(self):
        """Turn off controller operation right (CNTLOFF)."""
        return self.serial.send_and_read("CNTLOFF")
    
    def reset_alarm(self):
        """Reset controller alarm (RSTALRM)."""
        return self.serial.send_and_read("RSTALRM")
    
    def initialize(self) -> Dict[str, Any]:
        """
        Complete robot initialization sequence.
        Resets alarm, enables controller, and turns on servos.
        
        Returns:
            Dictionary with responses for each step
        """
        return self.serial.initialize_robot()
    
    def shutdown(self):
        """Safely shut down robot by turning off servos."""
        return self.serial.shutdown_robot()
    
    # ========================================================================
    # Motion Commands - Joint Space
    # ========================================================================
    
    def move_joint(self, j1: Optional[float] = None, j2: Optional[float] = None,
                   j3: Optional[float] = None, j4: Optional[float] = None,
                   j5: Optional[float] = None, j6: Optional[float] = None):
        """
        Move joints by specified angles (relative move using joint interpolation).
        Command: MJ [J1],[J2],[J3],[J4],[J5],[J6]
        
        Args:
            j1-j6: Joint angles in degrees (omit or None to skip)
            
        Returns:
            Parsed response
            
        Example:
            robot.move_joint(j1=10.0, j2=-5.0, j3=15.0)
        """
        angles = []
        for angle in [j1, j2, j3, j4, j5, j6]:
            if angle is not None:
                angles.append(f"{angle:.2f}")
            else:
                angles.append("")
        
        command = f"EXECMJ {','.join(angles)}"
        return self.serial.send_and_read(command)
    
    def move_to_position(self, position: int, posture: Optional[str] = None):
        """
        Move to taught position number.
        Command: MO a[,[O/C]]
        
        Args:
            position: Position number (1-999)
            posture: Posture flag 'O' (open) or 'C' (close), optional
            
        Returns:
            Parsed response
            
        Example:
            robot.move_to_position(10)
            robot.move_to_position(10, 'O')
        """
        if posture:
            command = f"EXECMO {position},{posture}"
        else:
            command = f"EXECMO {position}"
        return self.serial.send_and_read(command)
    
    def move_straight(self, position: int, posture: Optional[str] = None):
        """
        Move linearly to taught position.
        Command: MS a[,[O/C]]
        
        Args:
            position: Position number (1-999)
            posture: Posture flag 'O' (open) or 'C' (close), optional
            
        Returns:
            Parsed response
        """
        if posture:
            command = f"EXECMS {position},{posture}"
        else:
            command = f"EXECMS {position}"
        return self.serial.send_and_read(command)
    
    # ========================================================================
    # Motion Commands - Cartesian Space
    # ========================================================================
    
    def move_position(self, x: float, y: float, z: float,
                     a: Optional[float] = None, b: Optional[float] = None,
                     c: Optional[float] = None):
        """
        Move to explicit coordinate position.
        Command: MP X,Y,Z,A,B,C
        
        Args:
            x, y, z: Cartesian coordinates in mm
            a, b, c: Orientation angles in degrees (optional)
            
        Returns:
            Parsed response
            
        Example:
            robot.move_position(100.0, 200.0, 300.0)
            robot.move_position(100.0, 200.0, 300.0, a=0.0, b=0.0, c=90.0)
        """
        coords = [x, y, z]
        if a is not None:
            coords.append(a)
        if b is not None:
            coords.append(b)
        if c is not None:
            coords.append(c)
        
        coord_str = ','.join(f"{c:.2f}" for c in coords)
        command = f"EXECMP {coord_str}"
        return self.serial.send_and_read(command)
    
    def jog(self, coord_system: str, axis_mask: str, direction: int, inching: str = "00"):
        """
        Real-time jog control - pulse motion in specified direction.
        Command: JOG{coord_system};00;{pos_axis};{neg_axis};{inching}
        
        Args:
            coord_system: Coordinate system code
                         "00" = Joint (J1-J6)
                         "01" = XYZ (Cartesian)
                         "02" = Tool
                         "04" = 3-axis XYZ
                         "05" = Cylinder
            axis_mask: 2-digit HEX bitmask for axis selection
                      Joint mode: "01"=J1, "02"=J2, "04"=J3, "08"=J4, "10"=J5, "20"=J6
                      XYZ mode:   "01"=X,  "02"=Y,  "04"=Z,  "08"=A,  "10"=B,  "20"=C
                      (LSB = bit 0, can OR together for multi-axis)
            direction: Direction code
                      0 = Positive (+)
                      1 = Negative (-)
            inching: Inching parameter (default "00")
            
        Returns:
            Parsed response
            
        Example:
            # Jog J1 positive in joint coordinates
            robot.jog("00", "01", 0)  # Sends: 1;1;JOG00;00;01;00;00
            # Jog J1 negative
            robot.jog("00", "01", 1)  # Sends: 1;1;JOG00;00;00;01;00
            # Jog X positive in XYZ coordinates
            robot.jog("01", "01", 0)  # Sends: 1;1;JOG01;00;01;00;00
            
        Note:
            Format: JOG{coord};00(reserved);{pos_axis};{neg_axis};{inching}
            Direction determines which axis field gets the bitmask.
            Axis mask: J1/X=01, J2/Y=02, J3/Z=04, J4/A=08, J5/B=10, J6/C=20
        """
        # Build command with axis mask in correct position based on direction
        if direction == 0:  # Positive
            pos_axis = axis_mask
            neg_axis = "00"
        else:  # Negative
            pos_axis = "00"
            neg_axis = axis_mask
        
        command = f"JOG{coord_system};00;{pos_axis};{neg_axis};{inching}"
        return self.serial.send_and_read(command)
    
    def jog_start(self, coord_system: str, axis_mask: str, direction: int, inching: str = "00"):
        """
        Start continuous jogging (fire-and-forget, no response wait).
        Robot continues moving until jog_stop() is called.
        
        Args:
            coord_system: Coordinate system ("00"=Joint, "01"=XYZ, etc.)
            axis_mask: Axis bitmask (01=J1/X, 02=J2/Y, 04=J3/Z, etc.)
            direction: 0=positive, 1=negative
            inching: Inching parameter (default "00")
            
        Example:
            robot.jog_start("00", "01", 0)  # Start J1 positive
            # Robot keeps moving...
            robot.jog_stop("00")  # Stop
            
        Note:
            Use for continuous motion while key/button is held.
            MUST call jog_stop() to halt motion!
        """
        # Build command with axis mask in correct position
        if direction == 0:  # Positive
            pos_axis = axis_mask
            neg_axis = "00"
        else:  # Negative
            pos_axis = "00"
            neg_axis = axis_mask
        
        command = f"JOG{coord_system};00;{pos_axis};{neg_axis};{inching}"
        
        # Send without waiting for response (fire-and-forget for speed)
        # Clear buffer to prevent overflow from QoK responses
        self.serial.send_no_response(command, use_prefix=True, clear_buffer=True)
    
    def jog_stop(self, coord_system: str, inching: str = "00"):
        """
        Stop continuous jogging (fire-and-forget).
        
        Args:
            coord_system: Same coordinate system used in jog_start
            inching: Same inching value used in jog_start (default "00")
            
        Example:
            robot.jog_stop("00")  # Stop joint jog
            robot.jog_stop("01")  # Stop XYZ jog
            
        Note:
            Sends JOG command with both axis fields = 00 (no motion).
        """
        command = f"JOG{coord_system};00;00;00;{inching}"
        
        # Send without waiting for response (fire-and-forget for speed)
        self.serial.send_no_response(command, use_prefix=True, clear_buffer=False)
    
    # ========================================================================
    # Position Teaching and Origin
    # ========================================================================
    
    def here(self, position: int):
        """
        Store current robot position into position number.
        Command: HE a
        
        Args:
            position: Position number to store (1-999)
            
        Returns:
            Parsed response
            
        Example:
            robot.here(10)  # Save current position as position 10
        """
        command = f"EXECHE {position}"
        return self.serial.send_and_read(command)
    
    def define_origin(self, origin_type: Optional[int] = None):
        """
        Define current position as origin.
        Command: HO [a]
        
        Args:
            origin_type: Origin type (0=mechanical, 1=jig, 2=user), optional
            
        Returns:
            Parsed response
        """
        if origin_type is not None:
            command = f"HO {origin_type}"
        else:
            command = "HO"
        return self.serial.send_and_read(command)
    
    def nest(self):
        """
        Move to defined user origin.
        Command: NT
        
        Returns:
            Parsed response
        """
        return self.serial.send_and_read("NT")
    
    def origin_move(self):
        """
        Move to user-defined origin position.
        Command: OG
        
        Returns:
            Parsed response
        """
        return self.serial.send_and_read("OG")
    
    # ========================================================================
    # Speed and Acceleration Control
    # ========================================================================
    
    def set_speed(self, speed: int):
        """
        Set robot speed level.
        Command: EXECSP a (no 1;1; prefix)
        
        Args:
            speed: Controller speed level (1-30)
            
        Returns:
            Parsed response
            
        Example:
            robot.set_speed(30)  # Set to max speed level
        """
        if speed < 1 or speed > 30:
            raise ValueError("Speed level must be between 1 and 30")

        command = f"EXECSP {speed}"
        return self.serial.send_and_read(command)
    
    def set_override(self, percentage: int):
        """
        Set operation override percentage.
        Command: OVRD= a
        
        Args:
            percentage: Override percentage (1-100)
            
        Returns:
            Parsed response
        """
        command = f"OVRD={percentage}"
        return self.serial.send_and_read(command)

    def get_override(self):
        """Read operation override value (OVRD)."""
        return self.serial.send_and_read("OVRD")
    
    def define_speed(self, parameters: str):
        """
        Define detailed speed and acceleration parameters.
        Command: SD parameters
        
        Args:
            parameters: Speed definition parameters
            
        Returns:
            Parsed response
        """
        command = f"SD {parameters}"
        return self.serial.send_and_read(command)
    
    # ========================================================================
    # Tool Control
    # ========================================================================
    
    def set_tool_length(self, length: float):
        """
        Set tool length offset.
        Command: TL a
        
        Args:
            length: Tool length in mm
            
        Returns:
            Parsed response
        """
        command = f"TL {length:.2f}"
        return self.serial.send_and_read(command)
    
    def set_tool_matrix(self, x: float, y: float, z: float,
                       a: float, b: float, c: float):
        """
        Set tool coordinate transformation matrix.
        Command: TLM X,Y,Z,A,B,C
        
        Args:
            x, y, z: Tool offset in mm
            a, b, c: Tool orientation in degrees
            
        Returns:
            Parsed response
        """
        command = f"TLM {x:.2f},{y:.2f},{z:.2f},{a:.2f},{b:.2f},{c:.2f}"
        return self.serial.send_and_read(command)
    
    # ========================================================================
    # Timing Control
    # ========================================================================
    
    def timer(self, seconds: float):
        """
        Pause program execution for specified time.
        Command: TI a
        
        Args:
            seconds: Time to pause in seconds
            
        Returns:
            Parsed response
            
        Example:
            robot.timer(2.5)  # Wait 2.5 seconds
        """
        command = f"TI {seconds:.2f}"
        return self.serial.send_and_read(command)
    
    # ========================================================================
    # Hand/Gripper Control
    # ========================================================================
    
    def grip_close(self):
        """
        Close gripper.
        Command: GC
        
        Returns:
            Parsed response
        """
        return self.serial.send_and_read("GC")
    
    def grip_open(self):
        """
        Open gripper.
        Command: GO
        
        Returns:
            Parsed response
        """
        return self.serial.send_and_read("GO")
    
    def grip_pressure(self, a1: int, a2: int, a3: int):
        """
        Set gripping force parameters.
        Command: GP a1,a2,a3
        
        Args:
            a1, a2, a3: Gripping force parameters
            
        Returns:
            Parsed response
        """
        command = f"GP {a1},{a2},{a3}"
        return self.serial.send_and_read(command)
    
    # ========================================================================
    # Program Control Commands
    # ========================================================================
    
    def goto(self, line: int):
        """
        Jump to program line.
        Command: GT a
        
        Args:
            line: Line number to jump to
            
        Returns:
            Parsed response
        """
        command = f"GT {line}"
        return self.serial.send_and_read(command)
    
    def gosub(self, line: int):
        """
        Call subroutine at line.
        Command: GS a
        
        Args:
            line: Line number of subroutine
            
        Returns:
            Parsed response
        """
        command = f"GS {line}"
        return self.serial.send_and_read(command)
    
    def return_sub(self):
        """
        Return from subroutine.
        Command: RT
        
        Returns:
            Parsed response
        """
        return self.serial.send_and_read("RT")
    
    def end(self):
        """
        End program execution.
        Command: ED
        
        Returns:
            Parsed response
        """
        return self.serial.send_and_read("ED")
    
    def halt(self):
        """
        Stop program with controlled deceleration.
        Command: HLT
        
        Returns:
            Parsed response
        """
        return self.serial.send_and_read("HLT")
    
    # ========================================================================
    # Conditional Branching
    # ========================================================================
    
    def if_equal(self, value: float, line: int):
        """
        If register equals value, jump to line.
        Command: EQ a,b
        
        Args:
            value: Value to compare
            line: Line number to jump to if equal
            
        Returns:
            Parsed response
        """
        command = f"EQ {value},{line}"
        return self.serial.send_and_read(command)
    
    def if_not_equal(self, value: float, line: int):
        """
        If register does not equal value, jump to line.
        Command: NE a,b
        
        Args:
            value: Value to compare
            line: Line number to jump to if not equal
            
        Returns:
            Parsed response
        """
        command = f"NE {value},{line}"
        return self.serial.send_and_read(command)
    
    def if_larger(self, value: float, line: int):
        """
        If register greater than value, jump to line.
        Command: LG a,b
        
        Args:
            value: Value to compare
            line: Line number to jump to if larger
            
        Returns:
            Parsed response
        """
        command = f"LG {value},{line}"
        return self.serial.send_and_read(command)
    
    def if_smaller(self, value: float, line: int):
        """
        If register smaller than value, jump to line.
        Command: SM a,b
        
        Args:
            value: Value to compare
            line: Line number to jump to if smaller
            
        Returns:
            Parsed response
        """
        command = f"SM {value},{line}"
        return self.serial.send_and_read(command)
    
    # ========================================================================
    # I/O Commands
    # ========================================================================
    
    def output_bit(self, bit: int, state: bool = True):
        """
        Turn output bit on or off.
        Command: OB +/-a
        
        Args:
            bit: Output bit number
            state: True for ON (+), False for OFF (-)
            
        Returns:
            Parsed response
            
        Example:
            robot.output_bit(1, True)   # Turn ON output bit 1
            robot.output_bit(2, False)  # Turn OFF output bit 2
        """
        sign = "+" if state else "-"
        command = f"OB {sign}{bit}"
        return self.serial.send_and_read(command)
    
    def input_direct(self, bit: int):
        """
        Read external input bit.
        Command: ID a
        
        Args:
            bit: Input bit number to read
            
        Returns:
            Parsed response with bit state
        """
        command = f"ID {bit}"
        return self.serial.send_and_read(command)

    # ========================================================================
    # Communication / Run-State Commands (RS-232)
    # ========================================================================

    def open_communication(self, name: str = "USERTOOL"):
        """Open communication session (OPEN=name)."""
        return self.serial.send_and_read(f"OPEN={name}")

    def close_communication(self):
        """Close communication session (CLOSE)."""
        return self.serial.send_and_read("CLOSE")

    def run(self, program_name: Optional[str] = None, cycle_mode: Optional[bool] = None):
        """
        Start program execution (RUN).

        Args:
            program_name: Optional program name (e.g., "100")
            cycle_mode: None=omit, False=repeat(0), True=cycle(1)
        """
        command = "RUN"
        if program_name is not None and cycle_mode is not None:
            command = f"RUN{program_name};{1 if cycle_mode else 0}"
        elif program_name is not None:
            command = f"RUN{program_name}"
        elif cycle_mode is not None:
            command = f"RUN;{1 if cycle_mode else 0}"
        return self.serial.send_and_read(command)

    def load_program_to_slot(self, program_name: str):
        """Load program into task slot (PRGLOAD=)."""
        return self.serial.send_and_read(f"PRGLOAD={program_name}")

    def select_program(self, direction: str = "UP"):
        """
        Select loaded program in slot (PRGUP / PRGDOWN).

        Args:
            direction: "UP" or "DOWN"
        """
        direction = direction.upper().strip()
        if direction not in ("UP", "DOWN"):
            raise ValueError("direction must be 'UP' or 'DOWN'")
        return self.serial.send_and_read(f"PRG{direction}")

    def read_execution_program(self):
        """Read execution program name (PRGRD)."""
        return self.serial.send_and_read("PRGRD")

    def open_program_for_edit(self, program_name: str):
        """Open program for editing (LOAD=)."""
        return self._send_edit_command_with_slot_fallback(f"LOAD={program_name}")

    def save_program(self):
        """Save and close edit program (SAVE)."""
        return self._send_edit_command_with_slot_fallback("SAVE")

    def close_program_without_save(self):
        """Close edit program without saving (NEW)."""
        return self._send_edit_command_with_slot_fallback("NEW")

    def program_directory(self, position: str = "TOP"):
        """
        Read program directory entry (PDIR).

        Args:
            position: "TOP", "+1", or numeric string/index
        """
        return self.serial.send_and_read(f"PDIR{position}")

    def program_list_start(self, position: str = "TOP"):
        """Read line/content from opened edit program (LISTI)."""
        return self._send_edit_command_with_slot_fallback(f"LISTI{position}")

    def program_list_more(self, position: str = "+1"):
        """Read more line/content from opened edit program (LISTL)."""
        return self._send_edit_command_with_slot_fallback(f"LISTL{position}")

    def program_line_count(self, start_line: int = 0, end_line: int = 0):
        """Read line count for opened edit program (LISTCNT)."""
        return self._send_edit_command_with_slot_fallback(f"LISTCNT{start_line};{end_line}")

    def clear_program_contents(self):
        """Clear currently opened edit program contents (ECLR)."""
        return self._send_edit_command_with_slot_fallback("ECLR")

    def edit_program_line(self, line_number: int, line_data: str):
        """Write/replace one program line in opened edit program (EDATA)."""
        return self._send_edit_command_with_slot_fallback(f"EDATA{line_number} {line_data}")

    def insert_program_line(self, line_number: int, line_data: str):
        """Insert one program line into opened edit program (EDINS=)."""
        return self._send_edit_command_with_slot_fallback(f"EDINS={line_number};{line_data}")

    def stop(self):
        """Stop execution (STOP)."""
        return self.serial.send_and_read("STOP")

    def cycle_stop(self):
        """Stop at cycle boundary (CSTOP)."""
        return self.serial.send_and_read("CSTOP")

    def read_state(self):
        """Read run status (STATE)."""
        return self.serial.send_and_read("STATE")

    def read_stop_state(self):
        """Read stop status (DSTATE)."""
        return self.serial.send_and_read("DSTATE")
    
    # ========================================================================
    # Status Query Commands (RS-232)
    # ========================================================================

    def get_jpos(self, axis_info: str = "F"):
        """
        Read current joint position (JPOS).
        Command: JPOS<Axis info>

        Args:
            axis_info: Axis selector ("F" for full axes, or single axis 1-8)
        """
        return self.serial.send_and_read(f"JPOS{axis_info}")

    def get_ppos(self, axis_info: str = "F"):
        """
        Read current XYZ position (PPOS).
        Command: PPOS<Axis info>

        Args:
            axis_info: Axis selector ("F" for full axes, or single axis 1-8)
        """
        return self.serial.send_and_read(f"PPOS{axis_info}")

    def get_xpos(self, axis_info: str = "F"):
        """
        Read current 3-axis XYZ position (XPOS).
        Command: XPOS<Axis info>

        Args:
            axis_info: Axis selector ("F" for full axes, or single axis 1-8)
        """
        return self.serial.send_and_read(f"XPOS{axis_info}")

    def get_rpos(self, axis_info: str = "F"):
        """
        Read current cylinder position (RPOS).
        Command: RPOS<Axis info>

        Args:
            axis_info: Axis selector ("F" for full axes, or single axis 1-8)
        """
        return self.serial.send_and_read(f"RPOS{axis_info}")
    
    def get_position(self):
        """
        Get current joint positions.
        Command: JPOSF
        
        Returns:
            Parsed response with position data
            
        Example:
            response = robot.get_position()
            if response.is_success:
                positions = robot.parser.parse_position(response.raw)
                print(f"J1: {positions['J1']}")
        """
        return self.get_jpos("F")
    
    def position_read(self, position: int):
        """
        Read stored position data via RS-232.
        Command: PR a
        
        Args:
            position: Position number to read
            
        Returns:
            Parsed response with position data
        """
        command = f"EXECPR {position}"
        return self.serial.send_and_read(command)
    
    def where(self):
        """
        Return current position coordinates.
        Command: WH
        
        Returns:
            Parsed response with XYZ coordinates
            
        Example:
            response = robot.where()
            if response.is_success:
                coords = robot.parser.parse_coordinates(response.raw)
                print(f"X: {coords['X']}, Y: {coords['Y']}, Z: {coords['Z']}")
        """
        return self.serial.send_and_read("WH")
    
    def what_tool(self):
        """
        Return current tool number.
        Command: TD (no prefix required)
        
        Returns:
            Parsed response with current tool number
            
        Example:
            response = robot.what_tool()
            if response.is_success:
                print(f"Current tool: {response.data}")
        """
        return self.serial.send_and_read("TD", use_prefix=False)
    
    def what_tool_matrix(self):
        """
        Return current tool transformation matrix.
        Command: TDM (no prefix required)
        
        Returns:
            Parsed response with tool transformation matrix (X,Y,Z,A,B,C)
            
        Example:
            response = robot.what_tool_matrix()
            if response.is_success:
                print(f"Tool matrix: {response.data}")
        """
        return self.serial.send_and_read("TDM", use_prefix=False)
    
    def get_error(self):
        """
        Read current error code.
        Command: ER
        
        Returns:
            Parsed response with error information
            
        Example:
            response = robot.get_error()
            if response.is_error:
                print(f"Error: {response.error_message}")
        """
        return self.serial.send_and_read("ER")
    
    def get_version(self):
        """
        Return controller firmware version.
        Command: VR (no prefix required)
        
        Returns:
            Parsed response with version information
        """
        return self.serial.send_and_read("VR", use_prefix=False)
    
    # ========================================================================
    # Custom Command
    # ========================================================================
    
    def send_command(self, command: str, use_prefix: bool = True, 
                    read_delay: float = 0.2, parse: Optional[bool] = None):
        """
        Send a custom command to the controller.
        
        Args:
            command: Command string to send
            use_prefix: Whether to prepend the command prefix (default: True)
            read_delay: Delay before reading response in seconds
            parse: Whether to parse response (defaults to use_parser setting)
            
        Returns:
            Parsed response or raw string based on parse parameter
            
        Example:
            response = robot.send_command("CUSTOM_CMD")
        """
        return self.serial.send_and_read(command, use_prefix=use_prefix, 
                                        read_delay=read_delay, parse=parse)


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("RV-2AJ Command Library - Example Usage")
    print("=" * 70)
    print()
    
    # Example 1: Basic usage
    print("Example 1: Basic robot control")
    print("-" * 70)
    print("""
    robot = RV2AJCommands()
    robot.connect()
    
    # Initialize robot
    robot.initialize()
    
    # Move joints
    robot.move_joint(j1=10.0, j2=-5.0, j3=15.0)
    
    # Move to position
    robot.move_to_position(10)
    
    # Get current position
    response = robot.get_position()
    if response.is_success:
        positions = robot.parser.parse_position(response.raw)
        print(f"Current position: {positions}")
    
    # Gripper control
    robot.grip_open()
    robot.grip_close()
    
    # Shutdown
    robot.shutdown()
    robot.disconnect()
    """)
    
    # Example 2: Context manager
    print()
    print("Example 2: Using context manager")
    print("-" * 70)
    print("""
    with RV2AJCommands() as robot:
        robot.initialize()
        
        # Save current position
        robot.here(20)
        
        # Move to Cartesian position
        robot.move_position(100.0, 200.0, 300.0, a=0.0, b=0.0, c=90.0)
        
        # Set speed
        robot.set_speed(75)
        
        # Move back to saved position
        robot.move_to_position(20)
        
        robot.shutdown()
    """)
    
    # Example 3: Error handling
    print()
    print("Example 3: Error handling")
    print("-" * 70)
    print("""
    robot = RV2AJCommands()
    robot.connect()
    
    # Check for errors
    error_response = robot.get_error()
    if error_response.is_error:
        print(f"Error detected: {error_response.error_message}")
        if error_response.error_info:
            print(f"Cause: {error_response.error_info.cause}")
            print(f"Measures: {error_response.error_info.measures}")
        
        # Try to reset
        robot.reset_alarm()
    
    robot.disconnect()
    """)
    
    print()
    print("=" * 70)
    print("NOTE: Connect your robot and uncomment code to test")
    print("=" * 70)
