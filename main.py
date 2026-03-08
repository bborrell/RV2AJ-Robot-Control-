"""Command-line interface for the Mitsubishi RV-2AJ robot control application.

Usage examples::

    # Connect via serial and move to home
    python main.py --serial /dev/ttyUSB0 home

    # Connect via Ethernet and enable the servo
    python main.py --host 192.168.0.10 servo-on

    # Move to a joint position
    python main.py --serial COM3 move-joint --j1 45 --j2 -30

    # Move to a Cartesian position (straight-line)
    python main.py --host 192.168.0.10 move-cartesian --x 300 --y 0 --z 400 --linear

    # Open/close the gripper
    python main.py --serial /dev/ttyUSB0 hand-open
    python main.py --serial /dev/ttyUSB0 hand-close

    # Reset alarms
    python main.py --serial /dev/ttyUSB0 reset-alarm
"""

from __future__ import annotations

import argparse
import logging
import sys

from robot_control.communication import EthernetCommunication, SerialCommunication
from robot_control.controller import RobotController
from robot_control.exceptions import RobotError
from robot_control.positions import CartesianPosition, JointPosition


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="rv2aj-control",
        description="Control application for the Mitsubishi RV-2AJ robot arm.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # ------------------------------------------------------------------ #
    # Global options
    # ------------------------------------------------------------------ #
    transport = parser.add_mutually_exclusive_group(required=True)
    transport.add_argument(
        "--serial",
        metavar="PORT",
        help="Serial port to connect to (e.g. /dev/ttyUSB0 or COM3).",
    )
    transport.add_argument(
        "--host",
        metavar="HOST",
        help="IP address or hostname of the robot controller.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=10001,
        help="TCP port when using --host (default: 10001).",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=9600,
        help="Baud rate when using --serial (default: 9600).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Communication timeout in seconds (default: 5.0).",
    )
    parser.add_argument(
        "--speed",
        type=int,
        default=10,
        metavar="PERCENT",
        help="Speed override percentage 1-100 applied before any motion command (default: 10).",
    )
    parser.add_argument(
        "--no-servo",
        action="store_true",
        help="Do NOT automatically enable the servo before a motion command.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging output.",
    )

    # ------------------------------------------------------------------ #
    # Sub-commands
    # ------------------------------------------------------------------ #
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    # servo-on / servo-off / home / stop / reset-alarm
    sub.add_parser("servo-on",    help="Enable the servo motors.")
    sub.add_parser("servo-off",   help="Disable the servo motors.")
    sub.add_parser("home",        help="Move the robot to the home position.")
    sub.add_parser("stop",        help="Immediately stop all robot motion.")
    sub.add_parser("reset-alarm", help="Reset any active alarms on the controller.")
    sub.add_parser("get-pos",     help="Print the current Cartesian position.")
    sub.add_parser("get-joint",   help="Print the current joint position.")

    # hand-open / hand-close
    for name in ("hand-open", "hand-close"):
        p = sub.add_parser(name, help=f"{'Open' if name == 'hand-open' else 'Close'} the gripper.")
        p.add_argument("--hand", type=int, default=1, choices=[1, 2],
                       help="Gripper number (default: 1).")

    # move-joint
    mj = sub.add_parser("move-joint", help="Move to a joint-space position.")
    mj.add_argument("--j1", type=float, default=0.0, help="Joint 1 angle (degrees).")
    mj.add_argument("--j2", type=float, default=0.0, help="Joint 2 angle (degrees).")
    mj.add_argument("--j3", type=float, default=0.0, help="Joint 3 angle (degrees).")
    mj.add_argument("--j4", type=float, default=0.0, help="Joint 4 angle (degrees).")
    mj.add_argument("--j5", type=float, default=0.0, help="Joint 5 angle (degrees).")
    mj.add_argument("--j6", type=float, default=0.0, help="Joint 6 angle (degrees).")

    # move-cartesian
    mc = sub.add_parser("move-cartesian", help="Move to a Cartesian position.")
    mc.add_argument("--x",  type=float, default=0.0, help="X coordinate (mm).")
    mc.add_argument("--y",  type=float, default=0.0, help="Y coordinate (mm).")
    mc.add_argument("--z",  type=float, default=0.0, help="Z coordinate (mm).")
    mc.add_argument("--rx", type=float, default=0.0, help="Roll angle (degrees).")
    mc.add_argument("--ry", type=float, default=0.0, help="Pitch angle (degrees).")
    mc.add_argument("--rz", type=float, default=0.0, help="Yaw angle (degrees).")
    mc.add_argument("--linear", action="store_true",
                    help="Use straight-line (MVS) interpolation.")

    return parser


def run(args: argparse.Namespace) -> int:
    """Execute the requested command and return an exit code.

    Args:
        args: Parsed command-line arguments.

    Returns:
        ``0`` on success, ``1`` on error.
    """
    # Build the communication back-end
    if args.serial:
        comm = SerialCommunication(
            port=args.serial,
            baud_rate=args.baud,
            timeout=args.timeout,
        )
    else:
        comm = EthernetCommunication(
            host=args.host,
            port=args.port,
            timeout=args.timeout,
        )

    robot = RobotController(comm)

    try:
        robot.connect()

        # Convenience: enable servo + set speed before motion commands
        motion_commands = {"move-joint", "move-cartesian", "home"}
        if args.command in motion_commands and not args.no_servo:
            robot.servo_on()
            robot.set_speed(args.speed)

        # ---------------------------------------------------------------- #
        # Dispatch
        # ---------------------------------------------------------------- #
        if args.command == "servo-on":
            robot.servo_on()

        elif args.command == "servo-off":
            robot.servo_off()

        elif args.command == "home":
            robot.go_home()
            print("Robot moved to home position.")

        elif args.command == "stop":
            robot.stop()
            print("Stop command sent.")

        elif args.command == "reset-alarm":
            robot.reset_alarm()
            print("Alarms reset.")

        elif args.command == "get-pos":
            pos = robot.get_current_position()
            print(f"Current position: {pos}")

        elif args.command == "get-joint":
            jnt = robot.get_current_joint()
            print(f"Current joints: {jnt}")

        elif args.command == "hand-open":
            robot.hand_open(args.hand)
            print(f"Hand {args.hand} opened.")

        elif args.command == "hand-close":
            robot.hand_close(args.hand)
            print(f"Hand {args.hand} closed.")

        elif args.command == "move-joint":
            pos = JointPosition(
                j1=args.j1, j2=args.j2, j3=args.j3,
                j4=args.j4, j5=args.j5, j6=args.j6,
            )
            robot.move_joint(pos)
            print(f"Moved to joint position: {pos}")

        elif args.command == "move-cartesian":
            pos = CartesianPosition(
                x=args.x, y=args.y, z=args.z,
                rx=args.rx, ry=args.ry, rz=args.rz,
            )
            robot.move_cartesian(pos, linear=args.linear)
            print(f"Moved to Cartesian position: {pos}")

        return 0

    except RobotError as exc:
        print(f"Robot error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        return 1
    finally:
        if robot.servo_enabled:
            try:
                robot.servo_off()
            except RobotError:
                pass
        robot.disconnect()


def main() -> None:
    """Entry point for the rv2aj-control command-line tool."""
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    sys.exit(run(args))


if __name__ == "__main__":
    main()
