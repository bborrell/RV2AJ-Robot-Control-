import json
import serial
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class SerialConfig:
    port: str = "COM3"
    baudrate: int = 9600
    parity: str = serial.PARITY_EVEN
    stopbits: int = serial.STOPBITS_TWO
    bytesize: int = serial.EIGHTBITS
    timeout: float = 1.0


def load_config(path: str = "../RV2AJ_Reference_JSONs/rv2aj_config.json") -> SerialConfig:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        parity = data.get("parity", "EVEN").upper()
        parity_val = {
            "EVEN": serial.PARITY_EVEN,
            "NONE": serial.PARITY_NONE,
            "ODD": serial.PARITY_ODD,
            "MARK": serial.PARITY_MARK,
            "SPACE": serial.PARITY_SPACE,
        }.get(parity, serial.PARITY_EVEN)
        return SerialConfig(
            port=data.get("port", "COM3"),
            baudrate=int(data.get("baudrate", 9600)),
            parity=parity_val,
            stopbits=int(data.get("stopbits", 2)),
            bytesize=int(data.get("bytesize", 8)),
            timeout=float(data.get("timeout", 1.0)),
        )
    except Exception:
        return SerialConfig()


def decode_escapes(text: str) -> bytes:
    # Supports \r, \n, \t, \xNN, \\ and standard Python escapes
    return bytes(text.encode("utf-8").decode("unicode_escape"), "utf-8")


def read_all(ser: serial.Serial, wait: float = 0.2) -> bytes:
    time.sleep(wait)
    data = b""
    while True:
        chunk = ser.read(ser.in_waiting or 1)
        if not chunk:
            break
        data += chunk
        if ser.in_waiting == 0:
            break
    return data


def print_help() -> None:
    print(
        """
Raw serial test
Commands:
  /exit            - quit
  /cr              - append CR to each send
  /crlf            - append CRLF to each send
  /none            - send exactly what you type
  /read            - read any pending response

Input:
  Type raw command text. You may use escapes like \r, \n, \x0D.
"""
    )


def main() -> None:
    config = load_config()
    ser = serial.Serial(
        port=config.port,
        baudrate=config.baudrate,
        parity=config.parity,
        stopbits=config.stopbits,
        bytesize=config.bytesize,
        timeout=config.timeout,
    )
    print("Serial opened:")
    print(f"  Port: {config.port}")
    print(f"  Baudrate: {config.baudrate}")
    print(f"  Parity: {config.parity}")
    print(f"  Stop bits: {config.stopbits}")
    print(f"  Bytesize: {config.bytesize}")

    terminator: Optional[bytes] = b"\r"
    print_help()

    while True:
        line = input("raw>> ").strip()
        if not line:
            continue
        if line.lower() == "/exit":
            break
        if line.lower() == "/cr":
            terminator = b"\r"
            print("Terminator: CR")
            continue
        if line.lower() == "/crlf":
            terminator = b"\r\n"
            print("Terminator: CRLF")
            continue
        if line.lower() == "/none":
            terminator = None
            print("Terminator: none")
            continue
        if line.lower() == "/read":
            data = read_all(ser)
            print(f"RX: {data!r}")
            continue

        payload = decode_escapes(line)
        if terminator:
            payload += terminator
        ser.reset_input_buffer()
        ser.write(payload)
        rx = read_all(ser)
        print(f"TX: {payload!r}")
        print(f"RX: {rx!r}")

    ser.close()


if __name__ == "__main__":
    main()
