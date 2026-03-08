"""
RV-2AJ Robot Control - GUI Application

Graphical user interface for controlling the Mitsubishi RV-2AJ robot.
Provides buttons and controls for all high-level commands.

Author: Auto-generated
Date: 2026-02-15
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from typing import Optional
from rv2aj_commands import RV2AJCommands
from rv2aj_serial import RV2AJSerialException


class RobotControlGUI:
    """GUI application for RV-2AJ robot control."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("RV-2AJ Robot Control System")
        self.root.geometry("1200x850")
        
        # Set minimum window size and allow resizing
        self.root.minsize(1000, 700)
        self.root.resizable(True, True)
        
        self.robot: Optional[RV2AJCommands] = None
        self.connected = False
        self.initialized = False
        self.verbose_mode = tk.BooleanVar(value=False)
        self.active_program_name = ""
        
        # Configure colors
        self.bg_color = "#f0f0f0"
        self.panel_color = "#ffffff"
        self.button_color = "#4CAF50"
        self.danger_color = "#f44336"
        self.warning_color = "#ff9800"
        
        # Setup window close handler (safety: stop jogging on exit)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_ui()
        self.update_status()
    
    def setup_ui(self):
        """Setup the user interface."""
        # Configure root
        self.root.configure(bg=self.bg_color)
        
        # Create main containers (footer BEFORE content for proper pack ordering)
        self.create_header()
        self.create_footer()  # Create footer before content so it stays visible
        self.create_main_content()
    
    def create_header(self):
        """Create header with title and status."""
        header_frame = tk.Frame(self.root, bg="#2196F3", height=80)
        header_frame.pack(side=tk.TOP, fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="RV-2AJ Robot Control System",
            font=("Arial", 24, "bold"),
            bg="#2196F3",
            fg="white"
        )
        title_label.pack(pady=10)
        
        # Status bar
        status_frame = tk.Frame(header_frame, bg="#2196F3")
        status_frame.pack(fill=tk.X, padx=20)
        
        self.conn_status_label = tk.Label(
            status_frame,
            text="● Disconnected",
            font=("Arial", 12),
            bg="#2196F3",
            fg="#ffcccc"
        )
        self.conn_status_label.pack(side=tk.LEFT, padx=10)
        
        self.init_status_label = tk.Label(
            status_frame,
            text="● Not Initialized",
            font=("Arial", 12),
            bg="#2196F3",
            fg="#ffcccc"
        )
        self.init_status_label.pack(side=tk.LEFT, padx=10)
    
    def create_main_content(self):
        """Create main content area."""
        content_frame = tk.Frame(self.root, bg=self.bg_color)
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Controls
        left_panel = tk.Frame(content_frame, bg=self.panel_color, relief=tk.RAISED, borderwidth=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.create_control_panels(left_panel)
        
        # Right panel - Output
        right_panel = tk.Frame(content_frame, bg=self.panel_color, relief=tk.RAISED, borderwidth=1)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.create_output_panel(right_panel)
    
    def create_control_panels(self, parent):
        """Create control button panels."""
        # Create notebook for tabs
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.main_notebook = notebook
        
        # Connection Tab
        conn_tab = tk.Frame(notebook, bg=self.panel_color)
        notebook.add(conn_tab, text="Connection")
        self.create_connection_panel(conn_tab)
        
        # JOG Tab (Real-time control)
        jog_tab = tk.Frame(notebook, bg=self.panel_color)
        notebook.add(jog_tab, text="⚡ JOG")
        self.jog_tab = jog_tab
        self.create_jog_panel(jog_tab)
        
        # Motion Tab
        motion_tab = tk.Frame(notebook, bg=self.panel_color)
        notebook.add(motion_tab, text="Motion")
        self.create_motion_panel(motion_tab)
        
        # Position Tab
        position_tab = tk.Frame(notebook, bg=self.panel_color)
        notebook.add(position_tab, text="Positions")
        self.create_position_panel(position_tab)

        # Program Management Tab
        workspace_tab = tk.Frame(notebook, bg=self.panel_color)
        notebook.add(workspace_tab, text="Program Management")
        self.workspace_tab = workspace_tab
        self.create_workspace_panel(workspace_tab)
        
        # Gripper Tab
        gripper_tab = tk.Frame(notebook, bg=self.panel_color)
        notebook.add(gripper_tab, text="Gripper")
        self.create_gripper_panel(gripper_tab)
        
        # Speed/Control Tab
        control_tab = tk.Frame(notebook, bg=self.panel_color)
        notebook.add(control_tab, text="Speed & Control")
        self.create_control_panel(control_tab)
        
        # I/O Tab
        io_tab = tk.Frame(notebook, bg=self.panel_color)
        notebook.add(io_tab, text="I/O")
        self.create_io_panel(io_tab)
        
        # Status Tab
        status_tab = tk.Frame(notebook, bg=self.panel_color)
        notebook.add(status_tab, text="Status")
        self.create_status_panel(status_tab)

        # Safety: if user leaves JOG tab while jogging, stop motion immediately
        notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)

    def is_jog_tab_active(self):
        """Return True when a jog-enabled tab is selected (JOG only)."""
        try:
            if not hasattr(self, 'main_notebook') or not hasattr(self, 'jog_tab'):
                return False
            current = self.main_notebook.select()
            return current == str(self.jog_tab)
        except Exception:
            return False

    def on_tab_changed(self, event):
        """Stop active jog if user switches away from jog-enabled tabs."""
        if hasattr(self, 'jog_active') and self.jog_active and not self.is_jog_tab_active():
            self.log("⚠ Left jog-enabled tab - stopping jog", "WARNING")
            self.jog_key_release()
    
    def create_connection_panel(self, parent):
        """Create connection controls."""
        tk.Label(parent, text="Robot Connection", font=("Arial", 14, "bold"), bg=self.panel_color).pack(pady=10)
        
        btn_frame = tk.Frame(parent, bg=self.panel_color)
        btn_frame.pack(pady=10, fill=tk.X, padx=20)
        
        tk.Button(
            btn_frame,
            text="Connect",
            command=self.connect_robot,
            bg=self.button_color,
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            width=15
        ).pack(pady=5, fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="Initialize Robot",
            command=self.initialize_robot,
            bg=self.warning_color,
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            width=15
        ).pack(pady=5, fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="Shutdown Robot",
            command=self.shutdown_robot,
            bg=self.danger_color,
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            width=15
        ).pack(pady=5, fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="Disconnect",
            command=self.disconnect_robot,
            bg="#757575",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            width=15
        ).pack(pady=5, fill=tk.X)
        
        # Servo controls
        tk.Label(parent, text="Servo Control", font=("Arial", 12, "bold"), bg=self.panel_color).pack(pady=(20, 10))
        
        servo_frame = tk.Frame(parent, bg=self.panel_color)
        servo_frame.pack(pady=5, fill=tk.X, padx=20)
        
        tk.Button(
            servo_frame,
            text="Servo ON",
            command=lambda: self.execute_command("Servo ON", self.robot.servo_on),
            bg=self.button_color,
            fg="white",
            font=("Arial", 11),
            height=2
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        tk.Button(
            servo_frame,
            text="Servo OFF",
            command=lambda: self.execute_command("Servo OFF", self.robot.servo_off),
            bg=self.danger_color,
            fg="white",
            font=("Arial", 11),
            height=2
        ).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=2)
    
    def create_jog_panel(self, parent):
        """Create JOG control panel for real-time axis control."""
        # Initialize jog state
        self.jog_axis = tk.StringVar(value="J1")
        self.jog_coord_system = tk.StringVar(value="00")  # Default to Joint
        self.jog_step = tk.DoubleVar(value=1.0)
        self.jog_enabled = False
        self.jog_active = False  # Track if currently jogging
        self.jog_direction = None  # Track current jog direction (0=pos, 1=neg)
        self.jog_thread = None  # Thread for continuous jogging
        self.jog_stop_flag = False  # Flag to stop jog thread
        
        tk.Label(parent, text="Real-Time JOG Control", font=("Arial", 16, "bold"), bg=self.panel_color).pack(pady=10)
        
        # Warning label
        warning_frame = tk.Frame(parent, bg="#fff3cd", relief=tk.RAISED, borderwidth=2)
        warning_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(
            warning_frame,
            text="⚠ Robot must be INITIALIZED and SERVOS ON before jogging!",
            bg="#fff3cd",
            fg="#856404",
            font=("Arial", 10, "bold")
        ).pack(pady=5)
        
        # Coordinate System selection
        coord_sys_frame = tk.Frame(parent, bg=self.panel_color)
        coord_sys_frame.pack(pady=10)
        
        tk.Label(coord_sys_frame, text="Coordinate System:", font=("Arial", 12, "bold"), bg=self.panel_color).pack()
        
        coord_btn_frame = tk.Frame(coord_sys_frame, bg=self.panel_color)
        coord_btn_frame.pack(pady=5)
        
        coord_systems = [
            ("00", "Joint"),
            ("01", "XYZ"),
            ("02", "Tool"),
            ("04", "3-Axis XYZ"),
            ("05", "Cylinder")
        ]
        
        for code, name in coord_systems:
            tk.Radiobutton(
                coord_btn_frame,
                text=name,
                variable=self.jog_coord_system,
                value=code,
                font=("Arial", 10, "bold"),
                bg=self.panel_color,
                indicatoron=0,
                width=10,
                height=2,
                selectcolor="#9C27B0"
            ).pack(side=tk.LEFT, padx=2)
        
        # Axis selection
        axis_frame = tk.Frame(parent, bg=self.panel_color)
        axis_frame.pack(pady=15)
        
        tk.Label(axis_frame, text="Select Axis:", font=("Arial", 12, "bold"), bg=self.panel_color).pack()
        
        axis_buttons_frame = tk.Frame(axis_frame, bg=self.panel_color)
        axis_buttons_frame.pack(pady=10)
        
        # Joint axes
        joint_frame = tk.Frame(axis_buttons_frame, bg=self.panel_color)
        joint_frame.pack(side=tk.LEFT, padx=10)
        tk.Label(joint_frame, text="Joints:", font=("Arial", 10), bg=self.panel_color).pack()
        
        joint_btn_frame = tk.Frame(joint_frame, bg=self.panel_color)
        joint_btn_frame.pack()
        
        for axis in ['J1', 'J2', 'J3', 'J4', 'J5', 'J6']:
            tk.Radiobutton(
                joint_btn_frame,
                text=axis,
                variable=self.jog_axis,
                value=axis,
                font=("Arial", 11, "bold"),
                bg=self.panel_color,
                indicatoron=0,
                width=5,
                height=2,
                selectcolor="#4CAF50"
            ).pack(side=tk.LEFT, padx=2)
        
        # Cartesian axes
        cart_frame = tk.Frame(axis_buttons_frame, bg=self.panel_color)
        cart_frame.pack(side=tk.LEFT, padx=10)
        tk.Label(cart_frame, text="Cartesian:", font=("Arial", 10), bg=self.panel_color).pack()
        
        cart_btn_frame = tk.Frame(cart_frame, bg=self.panel_color)
        cart_btn_frame.pack()
        
        for axis in ['X', 'Y', 'Z', 'A', 'B', 'C']:
            tk.Radiobutton(
                cart_btn_frame,
                text=axis,
                variable=self.jog_axis,
                value=axis,
                font=("Arial", 11, "bold"),
                bg=self.panel_color,
                indicatoron=0,
                width=5,
                height=2,
                selectcolor="#2196F3"
            ).pack(side=tk.LEFT, padx=2)
        
        # Step size selection
        step_frame = tk.Frame(parent, bg=self.panel_color)
        step_frame.pack(pady=10)
        
        tk.Label(step_frame, text="Step Size:", font=("Arial", 12, "bold"), bg=self.panel_color).pack()
        
        step_btn_frame = tk.Frame(step_frame, bg=self.panel_color)
        step_btn_frame.pack(pady=5)
        
        for step in [0.1, 0.5, 1.0, 5.0, 10.0]:
            tk.Radiobutton(
                step_btn_frame,
                text=f"{step:g}°" if self.jog_axis.get().startswith('J') else f"{step:g}mm",
                variable=self.jog_step,
                value=step,
                font=("Arial", 10),
                bg=self.panel_color,
                indicatoron=0,
                width=8,
                selectcolor="#ff9800"
            ).pack(side=tk.LEFT, padx=2)
        
        # Jog controls
        controls_frame = tk.Frame(parent, bg=self.panel_color)
        controls_frame.pack(pady=20)
        
        tk.Label(controls_frame, text="Jog Controls", font=("Arial", 14, "bold"), bg=self.panel_color).pack(pady=5)
        
        # Arrow button layout
        arrow_frame = tk.Frame(controls_frame, bg=self.panel_color)
        arrow_frame.pack(pady=10)
        
        # Up arrow
        tk.Button(
            arrow_frame,
            text="▲\n+\nINCREASE",
            command=self.jog_positive,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 16, "bold"),
            width=12,
            height=4
        ).grid(row=0, column=1, padx=5, pady=5)
        
        # Current axis display (center)
        self.jog_axis_label = tk.Label(
            arrow_frame,
            textvariable=self.jog_axis,
            font=("Arial", 32, "bold"),
            bg="#e0e0e0",
            width=6,
            height=2,
            relief=tk.RAISED,
            borderwidth=3
        )
        self.jog_axis_label.grid(row=1, column=1, padx=5, pady=5)
        
        # Down arrow
        tk.Button(
            arrow_frame,
            text="DECREASE\n-\n▼",
            command=self.jog_negative,
            bg="#f44336",
            fg="white",
            font=("Arial", 16, "bold"),
            width=12,
            height=4
        ).grid(row=2, column=1, padx=5, pady=5)
        
        # Keyboard hint
        kb_frame = tk.Frame(parent, bg="#e3f2fd", relief=tk.RAISED, borderwidth=2)
        kb_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            kb_frame,
            text="⌨ Keyboard: HOLD Arrow Keys (↑/↓) for continuous jog - Release to STOP",
            bg="#e3f2fd",
            fg="#1976d2",
            font=("Arial", 11, "bold")
        ).pack(pady=5)
        
        # Bind keyboard for continuous jogging (press = start, release = stop)
        self.root.bind('<KeyPress-Up>', lambda e: self.jog_key_press(0))
        self.root.bind('<KeyRelease-Up>', lambda e: self.jog_key_release())
        self.root.bind('<KeyPress-Down>', lambda e: self.jog_key_press(1))
        self.root.bind('<KeyRelease-Down>', lambda e: self.jog_key_release())
        
        # Position display
        pos_display_frame = tk.Frame(parent, bg="#f5f5f5", relief=tk.SUNKEN, borderwidth=2)
        pos_display_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(pos_display_frame, text="Current Position", font=("Arial", 11, "bold"), bg="#f5f5f5").pack(pady=5)
        
        self.jog_position_text = tk.Text(
            pos_display_frame,
            height=4,
            width=40,
            font=("Consolas", 9),
            bg="#ffffff",
            fg="#000000"
        )
        self.jog_position_text.pack(padx=10, pady=5)
        self.jog_position_text.insert("1.0", "Position: Not available\nConnect and initialize robot")
        self.jog_position_text.config(state=tk.DISABLED)
        
        # Refresh position button
        tk.Button(
            pos_display_frame,
            text="🔄 Refresh Position",
            command=self.update_jog_position_display,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold")
        ).pack(pady=5)
    
    def _jog_loop(self, coord_system, axis_mask, direction):
        """Internal loop that continuously sends JOG commands while key is held.
        Runs in separate thread. No response parsing for maximum speed.
        """
        while not self.jog_stop_flag:
            try:
                # Build JOG command
                if direction == 0:  # Positive
                    pos_axis = axis_mask
                    neg_axis = "00"
                else:  # Negative
                    pos_axis = "00"
                    neg_axis = axis_mask
                
                command = f"JOG{coord_system};00;{pos_axis};{neg_axis};00"
                
                # Send without any waiting or parsing
                self.robot.serial.send_no_response(command, use_prefix=True, clear_buffer=True)
                
                # Small delay to prevent overwhelming serial (adjust as needed)
                time.sleep(0.01)  # 100Hz command rate
                
            except Exception as e:
                self.log(f"✗ Jog loop error: {e}", "ERROR")
                break
    
    def jog_key_press(self, direction):
        """Handle key press for continuous jogging.
        
        Args:
            direction: 0=positive (UP), 1=negative (DOWN)
        """
        # Prevent duplicate start if already jogging
        if self.jog_active:
            return

        # Only allow keyboard jog while JOG tab is active
        if not self.is_jog_tab_active():
            return
        
        if not self.connected or not self.initialized:
            self.log("⚠ Cannot jog: Robot not connected/initialized", "WARNING")
            return
        
        axis = self.jog_axis.get()
        coord_system = self.jog_coord_system.get()
        
        try:
            # Map axis to bitmask (HEX)
            if axis.startswith('J'):
                joint_num = int(axis[1])
                axis_mask = f"{1 << (joint_num - 1):02X}"
            elif axis in ['X', 'Y', 'Z', 'A', 'B', 'C']:
                axis_map = {'X': '01', 'Y': '02', 'Z': '04', 'A': '08', 'B': '10', 'C': '20'}
                axis_mask = axis_map[axis]
            else:
                self.log("Invalid axis selected", "WARNING")
                return
            
            dir_symbol = '+' if direction == 0 else '-'
            self.log(f"▶ JOG START: {axis} {dir_symbol} (Continuous mode)", "INFO")
            
            # Mark as active
            self.jog_active = True
            self.jog_direction = direction
            self.jog_stop_flag = False
            
            # Visual feedback
            self.jog_axis_label.config(bg="#ffeb3b")  # Yellow while jogging
            
            # Start jog loop in separate thread
            self.jog_thread = threading.Thread(
                target=self._jog_loop,
                args=(coord_system, axis_mask, direction),
                daemon=True
            )
            self.jog_thread.start()
            
        except Exception as e:
            self.log(f"✗ Jog start error: {e}", "ERROR")
            self.jog_active = False
    
    def jog_key_release(self):
        """Handle key release - stop continuous jogging."""
        if not self.jog_active:
            return
        
        coord_system = self.jog_coord_system.get()
        axis = self.jog_axis.get()
        
        try:
            # Signal thread to stop
            self.jog_stop_flag = True
            
            # Wait for thread to finish (with timeout)
            if self.jog_thread:
                self.jog_thread.join(timeout=0.1)
            
            self.log(f"■ JOG STOP: {axis}", "WARNING")
            
            # Send explicit stop command
            command = f"JOG{coord_system};00;00;00;00"
            self.robot.serial.send_no_response(command, use_prefix=True, clear_buffer=False)
            
            # Clear any remaining serial buffer
            time.sleep(0.05)
            self.robot.serial.clear_buffer()
            
            # Mark as inactive
            self.jog_active = False
            self.jog_direction = None
            self.jog_thread = None
            
            # Reset visual feedback
            self.jog_axis_label.config(bg="#e0e0e0")
            
            # Update position after stopping
            self.root.after(300, self.update_jog_position_display)
            
        except Exception as e:
            self.log(f"✗ Jog stop error: {e}", "ERROR")
            self.jog_active = False
            self.jog_axis_label.config(bg="#e0e0e0")
    
    def jog_positive(self):
        """Button handler for positive jog (pulse mode)."""
        if not self.connected or not self.initialized:
            self.log("⚠ Cannot jog: Robot not connected/initialized", "WARNING")
            messagebox.showwarning("JOG Error", "Robot must be connected and initialized!")
            return
        
        axis = self.jog_axis.get()
        coord_system = self.jog_coord_system.get()
        
        try:
            # Map axis to bitmask (HEX)
            if axis.startswith('J'):
                joint_num = int(axis[1])
                axis_mask = f"{1 << (joint_num - 1):02X}"
            elif axis in ['X', 'Y', 'Z', 'A', 'B', 'C']:
                axis_map = {'X': '01', 'Y': '02', 'Z': '04', 'A': '08', 'B': '10', 'C': '20'}
                axis_mask = axis_map[axis]
            else:
                self.log("Invalid axis selected", "WARNING")
                return
            
            self.log(f"JOG: {axis} + (Coord: {coord_system}, Mask: {axis_mask})", "INFO")
            
            # Pulse jog (with response)
            response = self.robot.jog(coord_system, axis_mask, direction=0)
            
            if response.is_success:
                self.log(f"✓ Jogged {axis} +", "SUCCESS")
                self.root.after(100, self.update_jog_position_display)
            else:
                self.log(f"✗ Jog failed: {response.raw}", "ERROR")
                
        except Exception as e:
            self.log(f"✗ Jog error: {e}", "ERROR")
            messagebox.showerror("JOG Error", str(e))
    
    def jog_negative(self):
        """Button handler for negative jog (pulse mode)."""
        if not self.connected or not self.initialized:
            self.log("⚠ Cannot jog: Robot not connected/initialized", "WARNING")
            messagebox.showwarning("JOG Error", "Robot must be connected and initialized!")
            return
        
        axis = self.jog_axis.get()
        coord_system = self.jog_coord_system.get()
        
        try:
            # Map axis to bitmask (HEX)
            if axis.startswith('J'):
                joint_num = int(axis[1])
                axis_mask = f"{1 << (joint_num - 1):02X}"
            elif axis in ['X', 'Y', 'Z', 'A', 'B', 'C']:
                axis_map = {'X': '01', 'Y': '02', 'Z': '04', 'A': '08', 'B': '10', 'C': '20'}
                axis_mask = axis_map[axis]
            else:
                self.log("Invalid axis selected", "WARNING")
                return
            
            self.log(f"JOG: {axis} - (Coord: {coord_system}, Mask: {axis_mask})", "INFO")
            
            # Pulse jog (with response)
            response = self.robot.jog(coord_system, axis_mask, direction=1)
            
            if response.is_success:
                self.log(f"✓ Jogged {axis} -", "SUCCESS")
                self.root.after(100, self.update_jog_position_display)
            else:
                self.log(f"✗ Jog failed: {response.raw}", "ERROR")
                
        except Exception as e:
            self.log(f"✗ Jog error: {e}", "ERROR")
            messagebox.showerror("JOG Error", str(e))
    
    def update_jog_position_display(self):
        """Update the position display in jog panel."""
        if not self.connected:
            return
        
        try:
            # Get joint position
            response = self.robot.get_position()
            
            if response.is_success:
                positions = self.robot.parser.parse_position(response.raw)
                
                self.jog_position_text.config(state=tk.NORMAL)
                self.jog_position_text.delete("1.0", tk.END)
                
                if positions:
                    display = "Joint Positions:\n"
                    for joint in ['J1', 'J2', 'J3', 'J4', 'J5', 'J6']:
                        if joint in positions:
                            display += f"  {joint}: {positions[joint]:>8.2f}°\n"
                    self.jog_position_text.insert("1.0", display)
                else:
                    self.jog_position_text.insert("1.0", f"Raw: {response.raw}")
                
                self.jog_position_text.config(state=tk.DISABLED)
                
        except Exception as e:
            self.log(f"Error updating position: {e}", "ERROR")
    
    def create_motion_panel(self, parent):
        """Create motion controls."""
        tk.Label(parent, text="Joint Motion", font=("Arial", 14, "bold"), bg=self.panel_color).pack(pady=10)
        
        # Joint controls
        joint_frame = tk.Frame(parent, bg=self.panel_color)
        joint_frame.pack(pady=10, fill=tk.X, padx=20)
        
        self.joint_entries = {}
        joints = ['J1', 'J2', 'J3', 'J5', 'J6']
        
        for joint in joints:
            frame = tk.Frame(joint_frame, bg=self.panel_color)
            frame.pack(fill=tk.X, pady=3)
            
            tk.Label(frame, text=f"{joint}:", font=("Arial", 11), bg=self.panel_color, width=5).pack(side=tk.LEFT)
            
            entry = tk.Entry(frame, font=("Arial", 11), width=10)
            entry.pack(side=tk.LEFT, padx=5)
            self.joint_entries[joint] = entry
            
            tk.Label(frame, text="degrees", font=("Arial", 9), bg=self.panel_color).pack(side=tk.LEFT)
        
        tk.Button(
            parent,
            text="Move Joints (Relative)",
            command=self.move_joints,
            bg=self.button_color,
            fg="white",
            font=("Arial", 12, "bold"),
            height=2
        ).pack(pady=10, padx=20, fill=tk.X)
        
        # Cartesian motion
        tk.Label(parent, text="Cartesian Motion", font=("Arial", 12, "bold"), bg=self.panel_color).pack(pady=(20, 10))
        
        cartesian_frame = tk.Frame(parent, bg=self.panel_color)
        cartesian_frame.pack(pady=10, fill=tk.X, padx=20)
        
        self.cartesian_entries = {}
        axes = [('X', 'mm'), ('Y', 'mm'), ('Z', 'mm'), ('A', '°'), ('B', '°'), ('C', '°')]
        
        for axis, unit in axes:
            frame = tk.Frame(cartesian_frame, bg=self.panel_color)
            frame.pack(fill=tk.X, pady=3)
            
            tk.Label(frame, text=f"{axis}:", font=("Arial", 11), bg=self.panel_color, width=5).pack(side=tk.LEFT)
            
            entry = tk.Entry(frame, font=("Arial", 11), width=10)
            entry.pack(side=tk.LEFT, padx=5)
            self.cartesian_entries[axis] = entry
            
            tk.Label(frame, text=unit, font=("Arial", 9), bg=self.panel_color).pack(side=tk.LEFT)
        
        tk.Button(
            parent,
            text="Move to Cartesian Position",
            command=self.move_cartesian,
            bg=self.button_color,
            fg="white",
            font=("Arial", 12, "bold"),
            height=2
        ).pack(pady=10, padx=20, fill=tk.X)
    
    def create_position_panel(self, parent):
        """Create position controls."""
        tk.Label(parent, text="Position Management", font=("Arial", 14, "bold"), bg=self.panel_color).pack(pady=10)
        
        # Save position
        save_frame = tk.Frame(parent, bg=self.panel_color)
        save_frame.pack(pady=10, fill=tk.X, padx=20)
        
        tk.Label(save_frame, text="Position Number:", font=("Arial", 11), bg=self.panel_color).pack(anchor=tk.W)
        
        pos_entry_frame = tk.Frame(save_frame, bg=self.panel_color)
        pos_entry_frame.pack(fill=tk.X, pady=5)
        
        self.save_position_entry = tk.Entry(pos_entry_frame, font=("Arial", 12), width=10)
        self.save_position_entry.pack(side=tk.LEFT)
        
        tk.Label(pos_entry_frame, text="(1-999)", font=("Arial", 9), bg=self.panel_color).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            save_frame,
            text="Save Current Position (HERE)",
            command=self.save_position,
            bg=self.button_color,
            fg="white",
            font=("Arial", 11, "bold"),
            height=2
        ).pack(pady=10, fill=tk.X)
        
        # Move to position
        move_frame = tk.Frame(parent, bg=self.panel_color)
        move_frame.pack(pady=10, fill=tk.X, padx=20)
        
        tk.Label(move_frame, text="Go to Position Number:", font=("Arial", 11), bg=self.panel_color).pack(anchor=tk.W)
        
        move_entry_frame = tk.Frame(move_frame, bg=self.panel_color)
        move_entry_frame.pack(fill=tk.X, pady=5)
        
        self.move_position_entry = tk.Entry(move_entry_frame, font=("Arial", 12), width=10)
        self.move_position_entry.pack(side=tk.LEFT)
        
        tk.Label(move_entry_frame, text="(1-999)", font=("Arial", 9), bg=self.panel_color).pack(side=tk.LEFT, padx=5)
        
        btn_row = tk.Frame(move_frame, bg=self.panel_color)
        btn_row.pack(fill=tk.X, pady=5)
        
        tk.Button(
            btn_row,
            text="Move (MOV)",
            command=self.move_to_position,
            bg=self.button_color,
            fg="white",
            font=("Arial", 11, "bold"),
            height=2
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        tk.Button(
            btn_row,
            text="Straight (MVS)",
            command=self.move_straight,
            bg="#2196F3",
            fg="white",
            font=("Arial", 11, "bold"),
            height=2
        ).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=2)
        
        # Quick positions
        tk.Label(parent, text="Quick Positions", font=("Arial", 12, "bold"), bg=self.panel_color).pack(pady=(20, 10))
        
        quick_frame = tk.Frame(parent, bg=self.panel_color)
        quick_frame.pack(pady=5, fill=tk.X, padx=20)
        
        positions = [1, 10, 20, 50, 100]
        for i, pos in enumerate(positions):
            if i % 2 == 0:
                row = tk.Frame(quick_frame, bg=self.panel_color)
                row.pack(fill=tk.X, pady=2)
            
            tk.Button(
                row,
                text=f"P{pos}",
                command=lambda p=pos: self.quick_move_to_position(p),
                bg="#607D8B",
                fg="white",
                font=("Arial", 10, "bold"),
                height=1,
                width=8
            ).pack(side=tk.LEFT, expand=True, padx=2)
    
    def create_gripper_panel(self, parent):
        """Create gripper controls."""
        tk.Label(parent, text="Gripper Control", font=("Arial", 14, "bold"), bg=self.panel_color).pack(pady=10)
        
        btn_frame = tk.Frame(parent, bg=self.panel_color)
        btn_frame.pack(pady=20, fill=tk.X, padx=40)
        
        tk.Button(
            btn_frame,
            text="Open Gripper",
            command=lambda: self.execute_command("Open Gripper", self.robot.grip_open),
            bg=self.button_color,
            fg="white",
            font=("Arial", 14, "bold"),
            height=3
        ).pack(pady=10, fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="Close Gripper",
            command=lambda: self.execute_command("Close Gripper", self.robot.grip_close),
            bg=self.danger_color,
            fg="white",
            font=("Arial", 14, "bold"),
            height=3
        ).pack(pady=10, fill=tk.X)
        
        # Gripper pressure
        tk.Label(parent, text="Gripper Pressure", font=("Arial", 12, "bold"), bg=self.panel_color).pack(pady=(30, 10))
        
        pressure_frame = tk.Frame(parent, bg=self.panel_color)
        pressure_frame.pack(pady=10, fill=tk.X, padx=40)
        
        self.pressure_entries = {}
        for param in ['A1', 'A2', 'A3']:
            frame = tk.Frame(pressure_frame, bg=self.panel_color)
            frame.pack(fill=tk.X, pady=5)
            
            tk.Label(frame, text=f"{param}:", font=("Arial", 11), bg=self.panel_color, width=5).pack(side=tk.LEFT)
            entry = tk.Entry(frame, font=("Arial", 11), width=10)
            entry.pack(side=tk.LEFT, padx=5)
            self.pressure_entries[param] = entry
        
        tk.Button(
            pressure_frame,
            text="Set Pressure",
            command=self.set_gripper_pressure,
            bg=self.warning_color,
            fg="white",
            font=("Arial", 11, "bold"),
            height=2
        ).pack(pady=10, fill=tk.X)
    
    def create_control_panel(self, parent):
        """Create speed and control panel."""
        tk.Label(parent, text="Speed Control", font=("Arial", 14, "bold"), bg=self.panel_color).pack(pady=10)
        
        # Speed slider
        speed_frame = tk.Frame(parent, bg=self.panel_color)
        speed_frame.pack(pady=10, fill=tk.X, padx=40)
        
        tk.Label(speed_frame, text="Speed (%)  →  EXECSP level (1-30)", font=("Arial", 11), bg=self.panel_color).pack(anchor=tk.W)
        
        slider_frame = tk.Frame(speed_frame, bg=self.panel_color)
        slider_frame.pack(fill=tk.X, pady=5)
        
        self.speed_var = tk.IntVar(value=50)
        initial_level = max(1, min(30, round(50 * 30 / 100)))
        self.speed_label = tk.Label(slider_frame, text=f"50% (L{initial_level})", font=("Arial", 14, "bold"), bg=self.panel_color, width=11)
        self.speed_label.pack(side=tk.RIGHT)
        
        speed_slider = tk.Scale(
            slider_frame,
            from_=1,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            command=self.update_speed_label,
            bg=self.panel_color,
            font=("Arial", 10)
        )
        speed_slider.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        tk.Button(
            speed_frame,
            text="Set Speed",
            command=self.set_speed,
            bg=self.button_color,
            fg="white",
            font=("Arial", 11, "bold"),
            height=2
        ).pack(pady=10, fill=tk.X)
        
        # Override
        tk.Label(parent, text="Override Control", font=("Arial", 12, "bold"), bg=self.panel_color).pack(pady=(20, 10))
        
        override_frame = tk.Frame(parent, bg=self.panel_color)
        override_frame.pack(pady=10, fill=tk.X, padx=40)
        
        tk.Label(override_frame, text="Override (%)", font=("Arial", 11), bg=self.panel_color).pack(anchor=tk.W)
        
        self.override_entry = tk.Entry(override_frame, font=("Arial", 12), width=10)
        self.override_entry.pack(pady=5)
        self.override_entry.insert(0, "100")
        
        tk.Button(
            override_frame,
            text="Set Override",
            command=self.set_override,
            bg="#2196F3",
            fg="white",
            font=("Arial", 11, "bold"),
            height=2
        ).pack(pady=10, fill=tk.X)
        
        # Timer
        tk.Label(parent, text="Timer/Delay", font=("Arial", 12, "bold"), bg=self.panel_color).pack(pady=(20, 10))
        
        timer_frame = tk.Frame(parent, bg=self.panel_color)
        timer_frame.pack(pady=10, fill=tk.X, padx=40)
        
        tk.Label(timer_frame, text="Seconds:", font=("Arial", 11), bg=self.panel_color).pack(anchor=tk.W)
        
        self.timer_entry = tk.Entry(timer_frame, font=("Arial", 12), width=10)
        self.timer_entry.pack(pady=5)
        
        tk.Button(
            timer_frame,
            text="Execute Timer",
            command=self.execute_timer,
            bg=self.warning_color,
            fg="white",
            font=("Arial", 11, "bold"),
            height=2
        ).pack(pady=10, fill=tk.X)
    
    def create_io_panel(self, parent):
        """Create I/O controls."""
        tk.Label(parent, text="Digital I/O", font=("Arial", 14, "bold"), bg=self.panel_color).pack(pady=10)
        
        # Output control
        tk.Label(parent, text="Output Control", font=("Arial", 12, "bold"), bg=self.panel_color).pack(pady=(10, 5))
        
        output_frame = tk.Frame(parent, bg=self.panel_color)
        output_frame.pack(pady=10, fill=tk.X, padx=40)
        
        tk.Label(output_frame, text="Output Bit:", font=("Arial", 11), bg=self.panel_color).pack(anchor=tk.W)
        
        self.output_bit_entry = tk.Entry(output_frame, font=("Arial", 12), width=10)
        self.output_bit_entry.pack(pady=5)
        
        btn_row = tk.Frame(output_frame, bg=self.panel_color)
        btn_row.pack(fill=tk.X, pady=5)
        
        tk.Button(
            btn_row,
            text="ON",
            command=lambda: self.set_output(True),
            bg=self.button_color,
            fg="white",
            font=("Arial", 11, "bold"),
            height=2
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        tk.Button(
            btn_row,
            text="OFF",
            command=lambda: self.set_output(False),
            bg=self.danger_color,
            fg="white",
            font=("Arial", 11, "bold"),
            height=2
        ).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=2)
        
        # Input reading
        tk.Label(parent, text="Input Reading", font=("Arial", 12, "bold"), bg=self.panel_color).pack(pady=(30, 5))
        
        input_frame = tk.Frame(parent, bg=self.panel_color)
        input_frame.pack(pady=10, fill=tk.X, padx=40)
        
        tk.Label(input_frame, text="Input Bit:", font=("Arial", 11), bg=self.panel_color).pack(anchor=tk.W)
        
        self.input_bit_entry = tk.Entry(input_frame, font=("Arial", 12), width=10)
        self.input_bit_entry.pack(pady=5)
        
        tk.Button(
            input_frame,
            text="Read Input",
            command=self.read_input,
            bg="#2196F3",
            fg="white",
            font=("Arial", 11, "bold"),
            height=2
        ).pack(pady=10, fill=tk.X)
    
    def create_status_panel(self, parent):
        """Create status and query panel."""
        tk.Label(parent, text="Robot Status & Queries", font=("Arial", 14, "bold"), bg=self.panel_color).pack(pady=10)
        
        btn_frame = tk.Frame(parent, bg=self.panel_color)
        btn_frame.pack(pady=10, fill=tk.X, padx=40)
        
        # Position queries
        tk.Label(btn_frame, text="Position Queries:", font=("Arial", 10, "bold"), bg=self.panel_color, anchor=tk.W).pack(pady=(5, 2), fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="Read Joint Position (JPOSF)",
            command=self.get_jpos_position,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2
        ).pack(pady=3, fill=tk.X)

        tk.Button(
            btn_frame,
            text="Read Cartesian Position (PPOSF)",
            command=self.get_ppos_position,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2
        ).pack(pady=3, fill=tk.X)

        tk.Button(
            btn_frame,
            text="Read 3-Axis Position (XPOSF)",
            command=self.get_xpos_position,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2
        ).pack(pady=3, fill=tk.X)

        tk.Button(
            btn_frame,
            text="Read Cylinder Position (RPOSF)",
            command=self.get_rpos_position,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2
        ).pack(pady=3, fill=tk.X)
        
        # Tool queries
        tk.Label(btn_frame, text="Tool Queries:", font=("Arial", 10, "bold"), bg=self.panel_color, anchor=tk.W).pack(pady=(15, 2), fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="What Tool (TD)",
            command=lambda: self.execute_command("What Tool", self.robot.what_tool),
            bg="#009688",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2
        ).pack(pady=3, fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="What Tool Matrix (TDM)",
            command=lambda: self.execute_command("What Tool Matrix", self.robot.what_tool_matrix),
            bg="#009688",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2
        ).pack(pady=3, fill=tk.X)
        
        # System queries
        tk.Label(btn_frame, text="System Queries:", font=("Arial", 10, "bold"), bg=self.panel_color, anchor=tk.W).pack(pady=(15, 2), fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="Check for Errors (ER)",
            command=self.check_errors,
            bg=self.warning_color,
            fg="white",
            font=("Arial", 10, "bold"),
            height=2
        ).pack(pady=3, fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="Get Controller Version (VR)",
            command=lambda: self.execute_command("Get Version", self.robot.get_version),
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2
        ).pack(pady=3, fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="Reset Alarm (RSTALRM)",
            command=lambda: self.execute_command("Reset Alarm", self.robot.reset_alarm),
            bg=self.danger_color,
            fg="white",
            font=("Arial", 10, "bold"),
            height=2
        ).pack(pady=3, fill=tk.X)
        
        # Manual command
        tk.Label(parent, text="Manual Command", font=("Arial", 12, "bold"), bg=self.panel_color).pack(pady=(30, 5))
        
        manual_frame = tk.Frame(parent, bg=self.panel_color)
        manual_frame.pack(pady=10, fill=tk.X, padx=40)
        
        tk.Label(manual_frame, text="Command:", font=("Arial", 11), bg=self.panel_color).pack(anchor=tk.W)
        
        self.manual_cmd_entry = tk.Entry(manual_frame, font=("Arial", 11))
        self.manual_cmd_entry.pack(fill=tk.X, pady=5)
        
        tk.Button(
            manual_frame,
            text="Send Command",
            command=self.send_manual_command,
            bg="#607D8B",
            fg="white",
            font=("Arial", 11, "bold"),
            height=2
        ).pack(pady=10, fill=tk.X)

    def create_workspace_panel(self, parent):
        """Create dedicated Program Management tab."""
        scroll_container = tk.Frame(parent, bg=self.panel_color)
        scroll_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(scroll_container, bg=self.panel_color, highlightthickness=0)
        v_scroll = tk.Scrollbar(scroll_container, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=v_scroll.set)

        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        content = tk.Frame(canvas, bg=self.panel_color)
        content_window = canvas.create_window((0, 0), window=content, anchor="nw")

        def _update_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _fit_content_width(event):
            canvas.itemconfigure(content_window, width=event.width)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        content.bind("<Configure>", _update_scroll_region)
        canvas.bind("<Configure>", _fit_content_width)
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        parent = content

        tk.Label(parent, text="Program Management", font=("Arial", 14, "bold"), bg=self.panel_color).pack(pady=10)

        active_row = tk.Frame(parent, bg=self.panel_color)
        active_row.pack(fill=tk.X, padx=20, pady=(0, 8))
        tk.Label(active_row, text="Active Program:", bg=self.panel_color, font=("Arial", 11, "bold")).pack(side=tk.LEFT)
        self.active_program_label = tk.Label(
            active_row,
            text="(none)",
            bg=self.panel_color,
            fg="#37474F",
            font=("Consolas", 11, "bold")
        )
        self.active_program_label.pack(side=tk.LEFT, padx=(8, 0))

        # Program management section
        program_frame = tk.LabelFrame(parent, text="Program Management", bg=self.panel_color, font=("Arial", 11, "bold"))
        program_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=8)

        list_controls = tk.Frame(program_frame, bg=self.panel_color)
        list_controls.pack(fill=tk.X, padx=10, pady=6)
        self.workspace_refresh_btn = tk.Button(
            list_controls,
            text="Refresh Program List",
            command=self.refresh_program_list_async,
            bg="#009688",
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.workspace_refresh_btn.pack(side=tk.LEFT)
        tk.Button(list_controls, text="Read Current (PRGRD)", command=self.read_current_program_name,
                  bg="#607D8B", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=6)

        list_frame = tk.Frame(program_frame, bg=self.panel_color)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        self.program_listbox = tk.Listbox(list_frame, height=8, font=("Consolas", 10))
        self.program_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.program_listbox.bind('<<ListboxSelect>>', self.on_program_selected)

        program_scroll = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.program_listbox.yview)
        program_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.program_listbox.config(yscrollcommand=program_scroll.set)

        select_row = tk.Frame(program_frame, bg=self.panel_color)
        select_row.pack(fill=tk.X, padx=10, pady=6)
        tk.Label(select_row, text="Program:", bg=self.panel_color, font=("Arial", 10)).pack(side=tk.LEFT)
        self.workspace_program_entry = tk.Entry(select_row, font=("Arial", 10))
        self.workspace_program_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

        action_row1 = tk.Frame(program_frame, bg=self.panel_color)
        action_row1.pack(fill=tk.X, padx=10, pady=4)
        tk.Button(action_row1, text="Load to Slot (PRGLOAD=)", command=self.workspace_load_program,
                  bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        tk.Button(action_row1, text="Select UP", command=lambda: self.execute_command("Select Program UP", self.robot.select_program, "UP"),
                  bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        tk.Button(action_row1, text="Select DOWN", command=lambda: self.execute_command("Select Program DOWN", self.robot.select_program, "DOWN"),
                  bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)

        action_row2 = tk.Frame(program_frame, bg=self.panel_color)
        action_row2.pack(fill=tk.X, padx=10, pady=4)
        tk.Button(action_row2, text="Open Edit (LOAD=)", command=self.workspace_open_program,
                  bg="#ff9800", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        tk.Button(action_row2, text="Save (SAVE)", command=lambda: self.execute_command("Save Program", self.robot.save_program),
                  bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        tk.Button(action_row2, text="Close No Save (NEW)", command=lambda: self.execute_command("Close Program (NEW)", self.robot.close_program_without_save),
                  bg="#f44336", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)

        action_row3 = tk.Frame(program_frame, bg=self.panel_color)
        action_row3.pack(fill=tk.X, padx=10, pady=(4, 10))
        tk.Button(action_row3, text="Run Repeat", command=lambda: self.workspace_run_program(False),
                  bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        tk.Button(action_row3, text="Run Cycle", command=lambda: self.workspace_run_program(True),
                  bg="#009688", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        tk.Button(action_row3, text="STOP", command=lambda: self.execute_command("Stop Program", self.robot.stop),
                  bg="#f44336", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        tk.Button(action_row3, text="CSTOP", command=lambda: self.execute_command("Cycle Stop", self.robot.cycle_stop),
                  bg="#ff9800", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)

        viewer_controls = tk.Frame(program_frame, bg=self.panel_color)
        viewer_controls.pack(fill=tk.X, padx=10, pady=(0, 6))
        self.workspace_read_steps_btn = tk.Button(
            viewer_controls,
            text="Read Steps (LISTI/LISTL)",
            command=self.workspace_read_program_steps_async,
            bg="#607D8B",
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.workspace_read_steps_btn.pack(side=tk.LEFT)
        tk.Button(
            viewer_controls,
            text="Clear Viewer",
            command=self.workspace_clear_program_viewer,
            bg="#9E9E9E",
            fg="white",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=6)

        self.workspace_program_text = scrolledtext.ScrolledText(
            program_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            height=10,
            bg="#101010",
            fg="#e0e0e0",
            insertbackground="white"
        )
        self.workspace_program_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        editor_frame = tk.LabelFrame(program_frame, text="Built-in Editor", bg=self.panel_color, font=("Arial", 11, "bold"))
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        editor_info = tk.Frame(editor_frame, bg=self.panel_color)
        editor_info.pack(fill=tk.X, padx=8, pady=(8, 4))
        tk.Label(
            editor_info,
            text="Write one line per row (example: 10 MOV P1). Click Upload to replace active program contents.",
            bg=self.panel_color,
            font=("Arial", 9)
        ).pack(anchor=tk.W)

        self.workspace_editor_text = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            height=10,
            bg="#0d1117",
            fg="#e6edf3",
            insertbackground="white"
        )
        self.workspace_editor_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        editor_actions = tk.Frame(editor_frame, bg=self.panel_color)
        editor_actions.pack(fill=tk.X, padx=8, pady=(4, 8))
        self.workspace_upload_btn = tk.Button(
            editor_actions,
            text="Upload Editor to Active Program",
            command=self.workspace_upload_editor_to_program_async,
            bg="#6A1B9A",
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.workspace_upload_btn.pack(side=tk.LEFT)
        tk.Button(
            editor_actions,
            text="Copy Viewer → Editor",
            command=self.workspace_copy_viewer_to_editor,
            bg="#455A64",
            fg="white",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=6)
        tk.Button(
            editor_actions,
            text="Clear Editor",
            command=lambda: self.workspace_editor_text.delete("1.0", tk.END),
            bg="#9E9E9E",
            fg="white",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT)
    
    def create_output_panel(self, parent):
        """Create output/log panel."""
        header_frame = tk.Frame(parent, bg=self.panel_color)
        header_frame.pack(fill=tk.X, pady=10, padx=10)
        
        tk.Label(header_frame, text="Output Log", font=("Arial", 14, "bold"), bg=self.panel_color).pack(side=tk.LEFT)
        
        # Verbose mode toggle
        verbose_check = tk.Checkbutton(
            header_frame,
            text="Verbose (Show Raw Commands)",
            variable=self.verbose_mode,
            font=("Arial", 10),
            bg=self.panel_color,
            command=self.toggle_verbose
        )
        verbose_check.pack(side=tk.RIGHT, padx=10)
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            height=30
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Clear button
        tk.Button(
            parent,
            text="Clear Output",
            command=self.clear_output,
            bg="#757575",
            fg="white",
            font=("Arial", 10, "bold")
        ).pack(pady=5, padx=10, fill=tk.X)
        
        self.log("RV-2AJ Robot Control GUI Started")
        self.log("Connect to robot to begin...")
    
    def create_footer(self):
        """Create footer with demo button."""
        footer_frame = tk.Frame(self.root, bg="#424242", height=60)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        footer_frame.pack_propagate(False)
        
        tk.Button(
            footer_frame,
            text="▶ Run Pick & Place Demo",
            command=self.run_demo,
            bg="#ff5722",
            fg="white",
            font=("Arial", 14, "bold"),
            height=2
        ).pack(side=tk.LEFT, padx=20, pady=10, fill=tk.X, expand=True)
        
        tk.Button(
            footer_frame,
            text="⚠️ Reset Alarm",
            command=self.reset_alarm_clicked,
            bg="#ff9800",
            fg="white",
            font=("Arial", 14, "bold"),
            height=2,
            width=20
        ).pack(side=tk.RIGHT, padx=(0, 10), pady=10)
        
        tk.Button(
            footer_frame,
            text="🛑 Emergency Stop",
            command=self.emergency_stop,
            bg="#b71c1c",
            fg="white",
            font=("Arial", 14, "bold"),
            height=2
        ).pack(side=tk.RIGHT, padx=(20, 0), pady=10)
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def log(self, message: str, level: str = "INFO"):
        """Log message to output."""
        timestamp = time.strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}\n"
        
        self.output_text.insert(tk.END, formatted)
        self.output_text.see(tk.END)
        
        # Color coding
        if level == "ERROR":
            self.output_text.tag_add("error", f"end-{len(formatted)+1}c", "end-1c")
            self.output_text.tag_config("error", foreground="#f44336")
        elif level == "SUCCESS":
            self.output_text.tag_add("success", f"end-{len(formatted)+1}c", "end-1c")
            self.output_text.tag_config("success", foreground="#4CAF50")
        elif level == "WARNING":
            self.output_text.tag_add("warning", f"end-{len(formatted)+1}c", "end-1c")
            self.output_text.tag_config("warning", foreground="#ff9800")
        elif level == "VERBOSE":
            self.output_text.tag_add("verbose", f"end-{len(formatted)+1}c", "end-1c")
            self.output_text.tag_config("verbose", foreground="#9E9E9E")
    
    def log_verbose(self, message: str):
        """Log verbose message (only if verbose mode is enabled)."""
        if self.verbose_mode.get():
            self.log(message, "VERBOSE")
    
    def toggle_verbose(self):
        """Toggle verbose logging mode."""
        if self.verbose_mode.get():
            self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "VERBOSE")
            self.log("Verbose mode ENABLED - Will log:", "WARNING")
            self.log("  • Raw TX/RX data (sent/received over serial)", "WARNING")
            self.log("  • Function calls with arguments", "WARNING")
            self.log("  • Detailed response information", "WARNING")
            self.log("  • Full exception tracebacks", "WARNING")
            self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "VERBOSE")
        else:
            self.log("Verbose mode disabled - Basic logging only", "INFO")
    
    def clear_output(self):
        """Clear output log."""
        self.output_text.delete(1.0, tk.END)
        self.log("Output cleared")
    
    def update_status(self):
        """Update status indicators."""
        if self.connected:
            self.conn_status_label.config(text="● Connected", fg="#4CAF50")
        else:
            self.conn_status_label.config(text="● Disconnected", fg="#ffcccc")
        
        if self.initialized:
            self.init_status_label.config(text="● Initialized", fg="#4CAF50")
        else:
            self.init_status_label.config(text="● Not Initialized", fg="#ffcccc")
    
    def update_speed_label(self, value):
        """Update speed label when slider moves."""
        percent = int(float(value))
        level = max(1, min(30, round(percent * 30 / 100)))
        self.speed_label.config(text=f"{percent}% (L{level})")
    
    def execute_command(self, name: str, command_func, *args, **kwargs):
        """Execute a robot command."""
        if not self.robot or not self.connected:
            self.log("Robot not connected!", "ERROR")
            messagebox.showerror("Error", "Please connect to robot first!")
            return
        
        try:
            self.log(f"Executing: {name}")
            
            # Log raw command if verbose mode is enabled
            if self.verbose_mode.get():
                # Try to get the actual command string for some common methods
                self.log_verbose(f"  Function: {command_func.__name__}")
                if args:
                    self.log_verbose(f"  Args: {args}")
                if kwargs:
                    self.log_verbose(f"  Kwargs: {kwargs}")
            
            response = command_func(*args, **kwargs)
            
            if hasattr(response, 'is_success'):
                raw_text = getattr(response, 'raw', '') if hasattr(response, 'raw') else ''
                raw_upper = raw_text.strip().upper()

                # Hard safety guard: any QeR/Qer/QER marker is an error
                if "QER" in raw_upper:
                    self.log(f"✗ {name} failed", "ERROR")
                    self.log(f"  Response: {response.raw}")
                    if hasattr(response, 'error_code') and response.error_code:
                        self.log_verbose(f"  Error Code: {response.error_code}")
                    if hasattr(response, 'error_info') and response.error_info:
                        self.log(f"  Error: {response.error_info.message}", "ERROR")
                    return

                # Success/data responses are successful.
                # Special-case: version query may return plain text without QoK.
                is_version_special = (
                    'version' in name.lower()
                    and not response.is_error
                    and bool(getattr(response, 'raw', '').strip())
                )

                if response.is_success or getattr(response, 'is_data', False) or is_version_special:
                    self.log(f"✓ {name} completed successfully", "SUCCESS")
                    self.log(f"  Response: {response.raw}")
                    self.log_verbose(f"  Response Type: {response.response_type.value if hasattr(response, 'response_type') else 'N/A'}")
                else:
                    self.log(f"✗ {name} failed", "ERROR")
                    self.log(f"  Response: {response.raw}")
                    if response.is_error and response.error_info:
                        self.log(f"  Error: {response.error_info.message}", "ERROR")
                        self.log_verbose(f"  Error Code: {response.error_code}")
                        self.log_verbose(f"  Error Level: {response.error_level}")
            else:
                self.log(f"  Response: {response}")
            
        except Exception as e:
            self.log(f"✗ Error executing {name}: {e}", "ERROR")
            self.log_verbose(f"  Exception Type: {type(e).__name__}")
            import traceback
            if self.verbose_mode.get():
                self.log_verbose(f"  Traceback: {traceback.format_exc()}")
            messagebox.showerror("Command Error", str(e))
    
    # ========================================================================
    # Command Methods
    # ========================================================================
    
    def connect_robot(self):
        """Connect to robot."""
        try:
            self.log("Connecting to robot...")
            if self.robot is None:
                # Create robot with verbose callback
                self.robot = RV2AJCommands(verbose_callback=self.log_verbose)
            else:
                # Update verbose callback if robot already exists
                self.robot.set_verbose_callback(self.log_verbose)
            
            self.robot.connect()
            self.connected = True
            self.update_status()
            self.log("✓ Connected successfully!", "SUCCESS")
            
        except RV2AJSerialException as e:
            self.log(f"✗ Connection failed: {e}", "ERROR")
            messagebox.showerror("Connection Error", str(e))
    
    def disconnect_robot(self):
        """Disconnect from robot."""
        if self.robot and self.connected:
            self.log("Disconnecting...")
            self.robot.disconnect()
            self.connected = False
            self.initialized = False
            self.update_status()
            self.log("✓ Disconnected", "SUCCESS")
    
    def initialize_robot(self):
        """Initialize robot."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return
        
        self.log("Initializing robot...")
        self.log("  1. Resetting alarms...")
        self.log("  2. Enabling controller...")
        self.log("  3. Turning on servos...")
        
        try:
            responses = self.robot.initialize()
            self.initialized = True
            self.update_status()
            self.log("✓ Robot initialized!", "SUCCESS")
            
        except Exception as e:
            self.log(f"✗ Initialization failed: {e}", "ERROR")
            messagebox.showerror("Initialization Error", str(e))
    
    def shutdown_robot(self):
        """Shutdown robot."""
        if not self.connected:
            return
        
        confirm = messagebox.askyesno("Confirm Shutdown", "Shutdown robot (turn off servos)?")
        if confirm:
            self.execute_command("Shutdown", self.robot.shutdown)
            self.initialized = False
            self.update_status()
    
    def move_joints(self):
        """Move joints based on entry values."""
        if not self.connected or not self.initialized:
            messagebox.showerror("Error", "Robot must be connected and initialized!")
            return
        
        try:
            j1 = float(self.joint_entries['J1'].get()) if self.joint_entries['J1'].get() else None
            j2 = float(self.joint_entries['J2'].get()) if self.joint_entries['J2'].get() else None
            j3 = float(self.joint_entries['J3'].get()) if self.joint_entries['J3'].get() else None
            j5 = float(self.joint_entries['J5'].get()) if self.joint_entries['J5'].get() else None
            j6 = float(self.joint_entries['J6'].get()) if self.joint_entries['J6'].get() else None
            
            if all(v is None for v in [j1, j2, j3, j5, j6]):
                messagebox.showwarning("Warning", "Enter at least one joint value!")
                return
            
            self.execute_command("Move Joints", self.robot.move_joint, j1=j1, j2=j2, j3=j3, j5=j5, j6=j6)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid number format!")
    
    def move_cartesian(self):
        """Move to Cartesian position."""
        if not self.connected or not self.initialized:
            messagebox.showerror("Error", "Robot must be connected and initialized!")
            return
        
        try:
            x = float(self.cartesian_entries['X'].get())
            y = float(self.cartesian_entries['Y'].get())
            z = float(self.cartesian_entries['Z'].get())
            a = float(self.cartesian_entries['A'].get())
            b = float(self.cartesian_entries['B'].get())
            c = float(self.cartesian_entries['C'].get())
            
            self.execute_command("Move Cartesian", self.robot.move_position, x, y, z, a, b, c)
            
        except ValueError:
            messagebox.showerror("Error", "All Cartesian values required!")
    
    def save_position(self):
        """Save current position."""
        if not self.connected or not self.initialized:
            messagebox.showerror("Error", "Robot must be connected and initialized!")
            return
        
        try:
            position = int(self.save_position_entry.get())
            if position < 1 or position > 999:
                messagebox.showerror("Error", "Position must be 1-999!")
                return
            
            self.execute_command(f"Save Position P{position}", self.robot.here, position)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid position number!")
    
    def move_to_position(self):
        """Move to saved position."""
        if not self.connected or not self.initialized:
            messagebox.showerror("Error", "Robot must be connected and initialized!")
            return
        
        try:
            position = int(self.move_position_entry.get())
            if position < 1 or position > 999:
                messagebox.showerror("Error", "Position must be 1-999!")
                return
            
            self.execute_command(f"Move to P{position}", self.robot.move_to_position, position)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid position number!")
    
    def move_straight(self):
        """Move straight to saved position."""
        if not self.connected or not self.initialized:
            messagebox.showerror("Error", "Robot must be connected and initialized!")
            return
        
        try:
            position = int(self.move_position_entry.get())
            if position < 1 or position > 999:
                messagebox.showerror("Error", "Position must be 1-999!")
                return
            
            self.execute_command(f"Move Straight to P{position}", self.robot.move_straight, position)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid position number!")
    
    def quick_move_to_position(self, position: int):
        """Quick move to predefined position."""
        if not self.connected or not self.initialized:
            messagebox.showerror("Error", "Robot must be connected and initialized!")
            return
        
        self.execute_command(f"Move to P{position}", self.robot.move_to_position, position)
    
    def set_gripper_pressure(self):
        """Set gripper pressure."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return
        
        try:
            a1 = int(self.pressure_entries['A1'].get())
            a2 = int(self.pressure_entries['A2'].get())
            a3 = int(self.pressure_entries['A3'].get())
            
            self.execute_command("Set Gripper Pressure", self.robot.grip_pressure, a1, a2, a3)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid pressure values!")
    
    def set_speed(self):
        """Set robot speed."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return
        
        percent = int(self.speed_var.get())
        speed_level = max(1, min(30, round(percent * 30 / 100)))
        self.execute_command(
            f"Set Speed {percent}% (EXECSP {speed_level})",
            self.robot.set_speed,
            speed_level
        )
    
    def set_override(self):
        """Set speed override."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return
        
        try:
            override = int(self.override_entry.get())
            if override < 1 or override > 100:
                messagebox.showerror("Error", "Override must be 1-100%!")
                return
            
            self.execute_command(f"Set Override to {override}%", self.robot.set_override, override)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid override value!")
    
    def execute_timer(self):
        """Execute timer delay."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return
        
        try:
            seconds = float(self.timer_entry.get())
            self.execute_command(f"Timer {seconds}s", self.robot.timer, seconds)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid timer value!")
    
    def set_output(self, state: bool):
        """Set output bit."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return
        
        try:
            bit = int(self.output_bit_entry.get())
            state_str = "ON" if state else "OFF"
            self.execute_command(f"Output Bit {bit} {state_str}", self.robot.output_bit, bit, state)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid bit number!")
    
    def read_input(self):
        """Read input bit."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return
        
        try:
            bit = int(self.input_bit_entry.get())
            self.execute_command(f"Read Input Bit {bit}", self.robot.input_direct, bit)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid bit number!")
    
    def get_current_position(self):
        """Get current position."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return
        
        try:
            self.log("Reading current position...")
            response = self.robot.get_position()
            
            if response.is_success:
                positions = self.robot.parser.parse_position(response.raw)
                
                if positions:
                    self.log("Joint Positions:", "SUCCESS")
                    for joint in ['J1', 'J2', 'J3', 'J5', 'J6']:
                        if joint in positions:
                            self.log(f"  {joint}: {positions[joint]:.2f}°")
                else:
                    self.log(f"  Raw: {response.raw}")
            else:
                self.log(f"✗ Failed to get position", "ERROR")
                
        except Exception as e:
            self.log(f"✗ Error: {e}", "ERROR")
    
    def get_where_position(self):
        """Get Cartesian position."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return
        
        try:
            self.log("Reading Cartesian position...")
            response = self.robot.where()
            
            if response.is_success:
                coords = self.robot.parser.parse_coordinates(response.raw)
                
                if coords:
                    self.log("Cartesian Position:", "SUCCESS")
                    for axis in ['X', 'Y', 'Z']:
                        if axis in coords:
                            self.log(f"  {axis}: {coords[axis]:.2f} mm")
                    for axis in ['A', 'B', 'C']:
                        if axis in coords:
                            self.log(f"  {axis}: {coords[axis]:.2f}°")
                else:
                    self.log(f"  Raw: {response.raw}")
            else:
                self.log(f"✗ Failed to get position", "ERROR")
                
        except Exception as e:
            self.log(f"✗ Error: {e}", "ERROR")

    def get_jpos_position(self):
        """Read JPOSF from controller."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return

        try:
            self.log("Reading JPOSF...")
            response = self.robot.get_jpos("F")

            if response.is_success or response.is_data:
                self.log("JPOSF response:", "SUCCESS")
                self.log(f"  {response.raw}")
            else:
                self.log("✗ Failed to read JPOSF", "ERROR")
                self.log(f"  {response.raw}")

        except Exception as e:
            self.log(f"✗ Error: {e}", "ERROR")

    def get_ppos_position(self):
        """Read PPOSF from controller."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return

        try:
            self.log("Reading PPOSF...")
            response = self.robot.get_ppos("F")

            if response.is_success or response.is_data:
                self.log("PPOSF response:", "SUCCESS")
                self.log(f"  {response.raw}")
            else:
                self.log("✗ Failed to read PPOSF", "ERROR")
                self.log(f"  {response.raw}")

        except Exception as e:
            self.log(f"✗ Error: {e}", "ERROR")

    def get_xpos_position(self):
        """Read XPOSF from controller."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return

        try:
            self.log("Reading XPOSF...")
            response = self.robot.get_xpos("F")

            if response.is_success or response.is_data:
                self.log("XPOSF response:", "SUCCESS")
                self.log(f"  {response.raw}")
            else:
                self.log("✗ Failed to read XPOSF", "ERROR")
                self.log(f"  {response.raw}")

        except Exception as e:
            self.log(f"✗ Error: {e}", "ERROR")

    def get_rpos_position(self):
        """Read RPOSF from controller."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return

        try:
            self.log("Reading RPOSF...")
            response = self.robot.get_rpos("F")

            if response.is_success or response.is_data:
                self.log("RPOSF response:", "SUCCESS")
                self.log(f"  {response.raw}")
            else:
                self.log("✗ Failed to read RPOSF", "ERROR")
                self.log(f"  {response.raw}")

        except Exception as e:
            self.log(f"✗ Error: {e}", "ERROR")
    
    def check_errors(self):
        """Check for robot errors."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return
        
        try:
            self.log("Checking for errors...")
            response = self.robot.get_error()
            
            if response.is_error:
                self.log(f"✗ Error Detected! Code: {response.error_code}", "ERROR")
                self.log(f"  Level: {response.error_level}", "ERROR")
                
                if response.error_info:
                    self.log(f"  Message: {response.error_info.message}", "ERROR")
                    if response.error_info.cause:
                        self.log(f"  Cause: {response.error_info.cause}", "ERROR")
                    if response.error_info.measures:
                        self.log(f"  Measures: {response.error_info.measures}", "ERROR")
                
                result = messagebox.askyesno("Error Detected", 
                    f"Error {response.error_code}: {response.error_info.message if response.error_info else 'Unknown error'}\n\nTry to reset alarm?")
                
                if result:
                    self.execute_command("Reset Alarm", self.robot.reset_alarm)
            else:
                self.log("✓ No errors detected!", "SUCCESS")
                self.log(f"  Response: {response.raw}")
                
        except Exception as e:
            self.log(f"✗ Error: {e}", "ERROR")
    
    def send_manual_command(self):
        """Send manual command."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return
        
        command = self.manual_cmd_entry.get().strip()
        if not command:
            return
        
        self.execute_command(f"Manual: {command}", self.robot.send_command, command)

    def _extract_program_name_from_pdir(self, raw: str):
        """Extract program/file name from PDIR raw response."""
        if not raw:
            return None

        text = raw.strip()
        if text.upper().startswith("QOK"):
            text = text[3:]
        text = text.lstrip(';')
        if not text:
            return None

        first = text.split(';')[0].strip()
        if not first:
            return None
        if '.' not in first:
            first = f"{first}.MB4"
        return first

    def _extract_program_count_from_pdir(self, raw: str):
        """Extract program count from PDIRTOP response when available."""
        if not raw:
            return None

        text = raw.strip()
        if text.upper().startswith("QOK"):
            text = text[3:]
        text = text.lstrip(';')
        if not text:
            return None

        parts = [p.strip() for p in text.split(';')]

        # PDIR format commonly includes program count near index 4:
        # name;bytes;date;time;count;...
        if len(parts) > 4:
            try:
                return int(parts[4])
            except (ValueError, TypeError):
                return None
        return None

    def _is_qok_without_payload(self, raw: str):
        """True when response is bare QoK/Qok with no payload fields."""
        if not raw:
            return False
        text = raw.strip()
        if not text.upper().startswith("QOK"):
            return False
        payload = text[3:].strip().lstrip(';').strip()
        return payload == ""

    def _extract_list_payload(self, raw: str):
        """Extract payload text from LISTI/LISTL/LISTCNT responses."""
        if not raw:
            return None

        text = raw.strip()
        upper = text.upper()

        if upper.startswith("QOK"):
            payload = text[3:].lstrip(';').strip()
            if not payload:
                return None

            parts = [p.strip() for p in payload.split(';')]
            if len(parts) >= 3 and parts[-1] in ("0", "1") and parts[-2].isdigit():
                payload = ';'.join(parts[:-2]).strip()
            return payload if payload else None

        if upper.startswith("Q") and not upper.startswith("QER"):
            payload = text[1:].lstrip(';').strip()
            return payload if payload else None

        return text

    def _parse_program_line_count(self, raw: str):
        """Parse integer line count from LISTCNT response when available."""
        payload = self._extract_list_payload(raw)
        if not payload:
            return None

        for part in [p.strip() for p in payload.split(';') if p.strip()]:
            if part.isdigit():
                try:
                    return int(part)
                except ValueError:
                    return None
        return None

    def _extract_first_line_number(self, payload: str):
        """Extract leading program line number from LISTI/LISTL payload."""
        if not payload:
            return None

        text = payload.strip()
        if not text:
            return None

        first_token = text.split(maxsplit=1)[0].strip()
        if first_token.isdigit():
            try:
                return int(first_token)
            except ValueError:
                return None
        return None

    def on_program_selected(self, event=None):
        """Populate program entry from selected list item."""
        if not hasattr(self, 'program_listbox'):
            return

        selection = self.program_listbox.curselection()
        if not selection:
            return

        selected_name = self.program_listbox.get(selection[0])
        self.workspace_program_entry.delete(0, tk.END)
        self.workspace_program_entry.insert(0, selected_name)

    def on_workspace_coord_changed(self, event=None):
        """Map workspace coordinate display name to jog command code."""
        if not hasattr(self, 'workspace_coord_name'):
            return
        selected_name = self.workspace_coord_name.get()
        if hasattr(self, 'workspace_coord_map') and selected_name in self.workspace_coord_map:
            self.jog_coord_system.set(self.workspace_coord_map[selected_name])

    def refresh_program_list(self):
        """Refresh controller program list using PDIR."""
        # Backward-compatible entry point
        self.refresh_program_list_async()

    def refresh_program_list_async(self):
        """Refresh controller program list without blocking the GUI."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return

        if getattr(self, 'program_refresh_in_progress', False):
            return

        self.program_refresh_in_progress = True
        if hasattr(self, 'workspace_refresh_btn'):
            self.workspace_refresh_btn.config(state=tk.DISABLED)
        self.log("Refreshing program list...", "INFO")

        thread = threading.Thread(target=self._refresh_program_list_worker, daemon=True)
        thread.start()

    def _refresh_program_list_worker(self):
        """Background worker for program listing via PDIR."""
        try:
            seen = set()
            names = []

            # Read TOP entry first
            response = self.robot.program_directory("TOP")
            raw = response.raw if hasattr(response, 'raw') else str(response)

            if self._is_qok_without_payload(raw):
                self.root.after(0, lambda: self._refresh_program_list_done([], None))
                return

            first_name = self._extract_program_name_from_pdir(raw)
            total_count = self._extract_program_count_from_pdir(raw)

            if first_name:
                seen.add(first_name)
                names.append(first_name)

            # Preferred path: deterministic indexed read (PDIR1..PDIRN)
            if total_count and total_count > 0:
                for idx in range(1, total_count + 1):
                    response = self.robot.program_directory(str(idx))
                    raw = response.raw if hasattr(response, 'raw') else str(response)

                    if self._is_qok_without_payload(raw):
                        break

                    program_name = self._extract_program_name_from_pdir(raw)
                    if not program_name:
                        continue

                    if program_name not in seen:
                        seen.add(program_name)
                        names.append(program_name)
            else:
                # Fallback: sequential +1 traversal (+1 means "next entry")
                # End condition: controller returns bare QoK (no payload).
                consecutive_misses = 0
                for _ in range(500):
                    response = self.robot.program_directory("+1")
                    raw = response.raw if hasattr(response, 'raw') else str(response)

                    if self._is_qok_without_payload(raw):
                        break

                    program_name = self._extract_program_name_from_pdir(raw)
                    if not program_name:
                        consecutive_misses += 1
                        if consecutive_misses >= 3:
                            break
                        continue

                    consecutive_misses = 0
                    if program_name not in seen:
                        seen.add(program_name)
                        names.append(program_name)

            self.root.after(0, lambda: self._refresh_program_list_done(names, None))
        except Exception as e:
            self.root.after(0, lambda: self._refresh_program_list_done([], e))

    def _refresh_program_list_done(self, names, error):
        """UI-thread completion handler for background program refresh."""
        self.program_refresh_in_progress = False
        if hasattr(self, 'workspace_refresh_btn'):
            self.workspace_refresh_btn.config(state=tk.NORMAL)

        if error is not None:
            self.log(f"✗ Failed to refresh program list: {error}", "ERROR")
            return

        self.program_listbox.delete(0, tk.END)
        for name in names:
            self.program_listbox.insert(tk.END, name)
        self.log(f"✓ Program list refreshed ({len(names)} found)", "SUCCESS")

    def _workspace_program_name(self):
        """Get selected/typed program name from workspace controls."""
        if not hasattr(self, 'workspace_program_entry'):
            return ""
        return self.workspace_program_entry.get().strip()

    def _set_active_program(self, program_name: str):
        """Set application-wide active program and update UI."""
        self.active_program_name = (program_name or "").strip()
        label_text = self.active_program_name if self.active_program_name else "(none)"
        if hasattr(self, 'active_program_label'):
            self.active_program_label.config(text=label_text)

    def _response_has_error(self, response) -> bool:
        """Return True when a response indicates QeR/Qer error."""
        if response is None:
            return True

        raw = response.raw if hasattr(response, 'raw') else str(response)
        if "QER" in raw.upper():
            return True
        return bool(getattr(response, 'is_error', False))

    def _extract_program_name_from_response(self, raw: str):
        """Extract program name from QoK<name> style response."""
        if not raw:
            return None

        text = raw.strip()
        if text.upper().startswith("QOK"):
            text = text[3:]
        text = text.lstrip(';').strip()
        if not text:
            return None

        first = text.split(';')[0].strip()
        return first if first else None

    def workspace_load_program(self):
        """Load selected program to slot (PRGLOAD=)."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return

        program_name = self._workspace_program_name()
        if not program_name:
            messagebox.showwarning("Program", "Select or enter a program name first.")
            return

        try:
            response = self.robot.load_program_to_slot(program_name)
            raw = response.raw if hasattr(response, 'raw') else str(response)
            if self._response_has_error(response):
                self.log(f"✗ Load Program {program_name} failed", "ERROR")
                self.log(f"  Response: {raw}")
                return

            self._set_active_program(program_name)
            self.log(f"✓ Load Program {program_name} completed successfully", "SUCCESS")
            self.log(f"  Response: {raw}")
        except Exception as e:
            self.log(f"✗ Error loading program {program_name}: {e}", "ERROR")

    def workspace_open_program(self):
        """Open selected program for edit (LOAD=)."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return

        program_name = self._workspace_program_name()
        if not program_name:
            messagebox.showwarning("Program", "Select or enter a program name first.")
            return

        try:
            response = self.robot.open_program_for_edit(program_name)
            raw = response.raw if hasattr(response, 'raw') else str(response)
            if self._response_has_error(response):
                self.log(f"✗ Open Program {program_name} failed", "ERROR")
                self.log(f"  Response: {raw}")
                return

            self._set_active_program(program_name)
            self.log(f"✓ Open Program {program_name} completed successfully", "SUCCESS")
            self.log(f"  Response: {raw}")
        except Exception as e:
            self.log(f"✗ Error opening program {program_name}: {e}", "ERROR")

    def workspace_clear_program_viewer(self):
        """Clear workspace program text viewer."""
        if hasattr(self, 'workspace_program_text'):
            self.workspace_program_text.delete("1.0", tk.END)

    def workspace_read_program_steps_async(self):
        """Read full opened program text using LISTI/LISTL without blocking UI."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return

        if getattr(self, 'program_steps_refresh_in_progress', False):
            return

        program_name = self._workspace_program_name() or self.active_program_name
        self.program_steps_refresh_in_progress = True
        if hasattr(self, 'workspace_read_steps_btn'):
            self.workspace_read_steps_btn.config(state=tk.DISABLED)

        target = program_name if program_name else "currently open"
        self.log(f"Reading program steps for {target}...", "INFO")

        worker = threading.Thread(
            target=self._workspace_read_program_steps_worker,
            args=(program_name,),
            daemon=True
        )
        worker.start()

    def _workspace_read_program_steps_worker(self, program_name: str):
        """Background worker: open (optional), then read LISTI/LISTL sequence."""
        try:
            lines = []
            seen_line_numbers = set()
            last_line_number = None

            if program_name:
                open_resp = self.robot.open_program_for_edit(program_name)
                open_raw = open_resp.raw if hasattr(open_resp, 'raw') else str(open_resp)
                if "QER" in open_raw.upper():
                    raise RuntimeError(f"LOAD failed: {open_raw}")

            count_hint = None
            try:
                count_resp = self.robot.program_line_count()
                count_raw = count_resp.raw if hasattr(count_resp, 'raw') else str(count_resp)
                if "QER" not in count_raw.upper():
                    count_hint = self._parse_program_line_count(count_raw)
            except Exception:
                count_hint = None

            first_resp = self.robot.program_list_start("TOP")
            first_raw = first_resp.raw if hasattr(first_resp, 'raw') else str(first_resp)
            if "QER" in first_raw.upper():
                raise RuntimeError(f"LISTI failed: {first_raw}")

            first_payload = self._extract_list_payload(first_raw)
            if first_payload:
                first_line_no = self._extract_first_line_number(first_payload)
                if first_line_no is not None:
                    seen_line_numbers.add(first_line_no)
                    last_line_number = first_line_no
                lines.append(first_payload)

            if not self._is_qok_without_payload(first_raw):
                if count_hint and count_hint > 1:
                    for _ in range(count_hint - 1):
                        more_resp = self.robot.program_list_more("+1")
                        more_raw = more_resp.raw if hasattr(more_resp, 'raw') else str(more_resp)

                        if "QER" in more_raw.upper():
                            raise RuntimeError(f"LISTL failed: {more_raw}")
                        if self._is_qok_without_payload(more_raw):
                            break

                        payload = self._extract_list_payload(more_raw)
                        if payload:
                            line_no = self._extract_first_line_number(payload)
                            if line_no is not None:
                                if line_no == last_line_number or line_no in seen_line_numbers:
                                    break
                                seen_line_numbers.add(line_no)
                                last_line_number = line_no
                            lines.append(payload)
                else:
                    consecutive_empty = 0
                    for _ in range(2000):
                        more_resp = self.robot.program_list_more("+1")
                        more_raw = more_resp.raw if hasattr(more_resp, 'raw') else str(more_resp)

                        if "QER" in more_raw.upper():
                            raise RuntimeError(f"LISTL failed: {more_raw}")
                        if self._is_qok_without_payload(more_raw):
                            break

                        payload = self._extract_list_payload(more_raw)
                        if payload:
                            line_no = self._extract_first_line_number(payload)
                            if line_no is not None:
                                if line_no == last_line_number or line_no in seen_line_numbers:
                                    break
                                seen_line_numbers.add(line_no)
                                last_line_number = line_no
                            lines.append(payload)
                            consecutive_empty = 0
                        else:
                            consecutive_empty += 1
                            if consecutive_empty >= 3:
                                break

            self.root.after(0, lambda p=program_name, data=lines: self._workspace_read_program_steps_done(p, data, None))
        except Exception as e:
            self.root.after(0, lambda p=program_name, err=e: self._workspace_read_program_steps_done(p, [], err))

    def _workspace_read_program_steps_done(self, program_name: str, lines, error):
        """UI-thread completion for workspace program step reads."""
        self.program_steps_refresh_in_progress = False
        if hasattr(self, 'workspace_read_steps_btn'):
            self.workspace_read_steps_btn.config(state=tk.NORMAL)

        if error is not None:
            self.log(f"✗ Failed to read program steps: {error}", "ERROR")
            return

        if hasattr(self, 'workspace_program_text'):
            self.workspace_program_text.delete("1.0", tk.END)
            if lines:
                self.workspace_program_text.insert(tk.END, "\n".join(lines))
            else:
                self.workspace_program_text.insert(tk.END, "(No program lines returned)")

        target = program_name if program_name else "currently open"
        self.log(f"✓ Loaded {len(lines)} program line(s) for {target}", "SUCCESS")

    def workspace_copy_viewer_to_editor(self):
        """Copy current viewer text into the built-in editor."""
        if not hasattr(self, 'workspace_program_text') or not hasattr(self, 'workspace_editor_text'):
            return

        source = self.workspace_program_text.get("1.0", tk.END).rstrip("\n")
        self.workspace_editor_text.delete("1.0", tk.END)
        if source:
            self.workspace_editor_text.insert(tk.END, source)

    def workspace_upload_editor_to_program_async(self):
        """Upload editor text to active program by replacing program contents."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return

        program_name = self.active_program_name or self._workspace_program_name()
        if not program_name:
            messagebox.showwarning("Program", "Load or open a program first.")
            return

        if not hasattr(self, 'workspace_editor_text'):
            return

        editor_text = self.workspace_editor_text.get("1.0", tk.END)
        if not editor_text.strip():
            messagebox.showwarning("Editor", "Editor is empty.")
            return

        if getattr(self, 'program_upload_in_progress', False):
            return

        confirm = messagebox.askyesno(
            "Upload Program",
            f"Replace all lines in {program_name} with the editor contents?"
        )
        if not confirm:
            return

        self.program_upload_in_progress = True
        if hasattr(self, 'workspace_upload_btn'):
            self.workspace_upload_btn.config(state=tk.DISABLED)
        self.log(f"Uploading editor to {program_name}...", "INFO")

        worker = threading.Thread(
            target=self._workspace_upload_editor_worker,
            args=(program_name, editor_text),
            daemon=True
        )
        worker.start()

    def _workspace_upload_editor_worker(self, program_name: str, editor_text: str):
        """Background upload worker: LOAD, ECLR, then EDATA/EDINS line writes."""
        try:
            lines_to_send = []
            next_auto_line = 10

            for raw_line in editor_text.splitlines():
                stripped = raw_line.strip()
                if not stripped:
                    continue

                parts = stripped.split(maxsplit=1)
                if len(parts) == 2 and parts[0].isdigit():
                    line_number = int(parts[0])
                    line_data = parts[1].strip()
                else:
                    line_number = next_auto_line
                    line_data = stripped
                if not line_data:
                    continue

                lines_to_send.append((line_number, line_data))
                next_auto_line = max(next_auto_line + 10, line_number + 10)

            if not lines_to_send:
                raise RuntimeError("No valid program lines to upload")

            open_resp = self.robot.open_program_for_edit(program_name)
            if self._response_has_error(open_resp):
                open_raw = open_resp.raw if hasattr(open_resp, 'raw') else str(open_resp)
                raise RuntimeError(f"LOAD failed: {open_raw}")

            clear_resp = self.robot.clear_program_contents()
            if self._response_has_error(clear_resp):
                clear_raw = clear_resp.raw if hasattr(clear_resp, 'raw') else str(clear_resp)
                raise RuntimeError(f"ECLR failed: {clear_raw}")

            for line_number, line_data in lines_to_send:
                line_candidates = [line_data]
                upper_line = line_data.upper().strip()
                if upper_line.startswith("MOV P"):
                    pos_num = upper_line[5:].strip()
                    if pos_num.isdigit():
                        line_candidates.append(f"MO {int(pos_num)}")

                wrote_ok = False
                last_edata_raw = ""
                last_edins_raw = ""
                last_error_code = None

                for candidate_line in line_candidates:
                    write_resp = self.robot.edit_program_line(line_number, candidate_line)
                    if not self._response_has_error(write_resp):
                        wrote_ok = True
                        break

                    last_edata_raw = write_resp.raw if hasattr(write_resp, 'raw') else str(write_resp)
                    last_error_code = getattr(write_resp, 'error_code', None)

                    # Fallback for controllers that prefer EDINS style at a given state
                    insert_resp = self.robot.insert_program_line(line_number, candidate_line)
                    if not self._response_has_error(insert_resp):
                        wrote_ok = True
                        break

                    last_edins_raw = insert_resp.raw if hasattr(insert_resp, 'raw') else str(insert_resp)

                if not wrote_ok:
                    hint = ""
                    edata_upper = last_edata_raw.upper()
                    edins_upper = last_edins_raw.upper()
                    if (
                        str(last_error_code) == "4220"
                        or str(last_error_code) == "6010"
                        or "QER4220" in edata_upper
                        or "QER6010" in edata_upper
                        or "QER4220" in edins_upper
                        or "QER6010" in edins_upper
                    ):
                        hint = " (syntax/state error: this controller may require MoveMaster style like '10 MO 1' instead of '10 MOV P1')"
                    raise RuntimeError(
                        f"Line {line_number} write failed (EDATA: {last_edata_raw}; EDINS: {last_edins_raw}){hint}"
                    )

            self.root.after(0, lambda p=program_name, lines=lines_to_send: self._workspace_upload_editor_done(p, lines, None))
        except Exception as e:
            self.root.after(0, lambda p=program_name, err=e: self._workspace_upload_editor_done(p, [], err))

    def _workspace_upload_editor_done(self, program_name: str, lines_to_send, error):
        """UI-thread completion for editor upload."""
        self.program_upload_in_progress = False
        if hasattr(self, 'workspace_upload_btn'):
            self.workspace_upload_btn.config(state=tk.NORMAL)

        if error is not None:
            self.log(f"✗ Upload failed: {error}", "ERROR")
            return

        self._set_active_program(program_name)
        self.log(f"✓ Uploaded {len(lines_to_send)} line(s) to {program_name}", "SUCCESS")

    def workspace_run_program(self, cycle_mode: bool):
        """Run currently selected/loaded program in repeat or cycle mode."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return

        mode_name = "Cycle" if cycle_mode else "Repeat"
        program_name = self.active_program_name or self._workspace_program_name()

        if program_name:
            self.execute_command(f"Run {program_name} ({mode_name})", self.robot.run, program_name, cycle_mode)
        else:
            self.execute_command(f"Run Selected Program ({mode_name})", self.robot.run, None, cycle_mode)

    def read_current_program_name(self):
        """Read current execution program name (PRGRD)."""
        if not self.connected:
            messagebox.showerror("Error", "Connect to robot first!")
            return

        try:
            response = self.robot.read_execution_program()
            raw = response.raw if hasattr(response, 'raw') else str(response)
            self.log("Current execution program:", "SUCCESS")
            self.log(f"  {raw}")
            name = self._extract_program_name_from_response(raw)
            if name:
                self._set_active_program(name)
        except Exception as e:
            self.log(f"✗ Failed to read current program: {e}", "ERROR")
    
    def run_demo(self):
        """Run pick and place demo."""
        if not self.connected or not self.initialized:
            messagebox.showerror("Error", "Robot must be connected and initialized!")
            return
        
        confirm = messagebox.askyesno("Run Demo", 
            "Run Pick & Place demo?\n\nThis will:\n" +
            "1. Move to home (P1)\n" +
            "2. Open gripper\n" +
            "3. Move to pick (P10)\n" +
            "4. Close gripper\n" +
            "5. Move to place (P20)\n" +
            "6. Open gripper\n" +
            "7. Return home\n\n" +
            "Ensure P1, P10, P20 are defined!")
        
        if not confirm:
            return
        
        def demo_thread():
            try:
                self.log("=== Starting Pick & Place Demo ===", "SUCCESS")
                
                self.log("→ Moving to home position...")
                self.robot.move_to_position(1)
                time.sleep(0.5)
                
                self.log("→ Opening gripper...")
                self.robot.grip_open()
                time.sleep(0.5)
                
                self.log("→ Moving to pick position...")
                self.robot.move_to_position(10)
                time.sleep(0.5)
                
                self.log("→ Closing gripper...")
                self.robot.grip_close()
                time.sleep(0.5)
                
                self.log("→ Lifting...")
                self.robot.move_joint(j3=-5.0)
                time.sleep(0.5)
                
                self.log("→ Moving to place position...")
                self.robot.move_to_position(20)
                time.sleep(0.5)
                
                self.log("→ Opening gripper...")
                self.robot.grip_open()
                time.sleep(0.5)
                
                self.log("→ Returning home...")
                self.robot.move_to_position(1)
                
                self.log("=== Demo Complete! ===", "SUCCESS")
                
            except Exception as e:
                self.log(f"✗ Demo failed: {e}", "ERROR")
        
        threading.Thread(target=demo_thread, daemon=True).start()
    
    def on_closing(self):
        """Handle window close event - safety stop jogging before exit."""
        # Stop any active jogging
        if hasattr(self, 'jog_active') and self.jog_active:
            try:
                # Stop the jog thread
                self.jog_stop_flag = True
                if self.jog_thread:
                    self.jog_thread.join(timeout=0.2)
                
                # Send stop command
                coord_system = self.jog_coord_system.get()
                command = f"JOG{coord_system};00;00;00;00"
                self.robot.serial.send_no_response(command, use_prefix=True, clear_buffer=False)
                self.log("▣ Stopped jogging on exit", "WARNING")
            except:
                pass
        
        # Close serial connection
        if self.connected and self.robot:
            try:
                self.robot.disconnect()
            except:
                pass
        
        # Destroy window
        self.root.destroy()
    
    def reset_alarm_clicked(self):
        """Reset alarm button handler."""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the robot first.")
            return
        
        self.execute_command("Reset Alarm", self.robot.reset_alarm)
    
    def emergency_stop(self):
        """Emergency stop."""
        if not self.connected:
            return
        
        self.log("!!! EMERGENCY STOP !!!", "ERROR")
        
        # Stop any active jogging first
        if hasattr(self, 'jog_active') and self.jog_active:
            try:
                # Stop the jog thread
                self.jog_stop_flag = True
                if self.jog_thread:
                    self.jog_thread.join(timeout=0.1)
                
                # Send stop command
                coord_system = self.jog_coord_system.get()
                command = f"JOG{coord_system};00;00;00;00"
                self.robot.serial.send_no_response(command, use_prefix=True, clear_buffer=False)
                time.sleep(0.05)
                self.robot.serial.clear_buffer()
                self.jog_active = False
            except:
                pass
        
        # Turn off servos
        try:
            self.robot.servo_off()
            self.initialized = False
            self.update_status()
            self.log("Servos turned OFF", "WARNING")
        except:
            pass


def main():
    """Main entry point."""
    root = tk.Tk()
    app = RobotControlGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
