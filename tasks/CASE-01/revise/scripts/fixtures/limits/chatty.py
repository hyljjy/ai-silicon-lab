"""Output fixture for test_limits. Self-limited: exits on its own after at most 10 s and never writes more than 64 KB in
total (stdout plus stderr), whatever the wrapper under test does.

  chatty.py [--stdout N] [--stderr N] [--flood] [--first-line TEXT] [--wait-file F] [--sleep] [--marker M]

  --stdout N / --stderr N  write N bytes (lines of "x") to stdout / stderr, flushed, then exit 0 (or sleep, --sleep)
  --flood                  write stdout as fast as possible up to the 64 KB cap, then sleep until the 10 s cap
  --first-line TEXT        write TEXT and a newline first, flushed
  --wait-file F            after the output, wait until F exists, then exit 0
  --sleep                  after the output, sleep until the 10 s cap
"""
import os
import sys
import time

MAX_SECONDS = 10
MAX_BYTES = 64 * 1024
START = time.monotonic()
written = 0


def emit(stream, data):
    global written
    data = data[:max(0, MAX_BYTES - written)]
    if data:
        stream.write(data)
        stream.flush()
        written += len(data)


def block(n):
    line = b"x" * 63 + b"\n"
    return (line * (n // 64 + 1))[:n]


def arg(argv, name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


def sleep_out(code=3):
    while time.monotonic() - START < MAX_SECONDS:
        time.sleep(0.05)
    sys.exit(code)


def main(argv):
    out, err = sys.stdout.buffer, sys.stderr.buffer
    if "--marker" in argv:
        with open(arg(argv, "--marker"), "w", encoding="ascii") as f:
            f.write("started\n")
    if "--first-line" in argv:
        emit(out, arg(argv, "--first-line").encode() + b"\n")
    if "--stdout" in argv:
        emit(out, block(int(arg(argv, "--stdout"))))
    if "--stderr" in argv:
        emit(err, block(int(arg(argv, "--stderr"))))
    if "--flood" in argv:
        while written < MAX_BYTES and time.monotonic() - START < MAX_SECONDS:
            emit(out, block(1024))
        sleep_out()
    if "--wait-file" in argv:
        f = arg(argv, "--wait-file")
        while time.monotonic() - START < MAX_SECONDS:
            if os.path.exists(f):
                sys.exit(0)
            time.sleep(0.02)
        sys.exit(4)
    if "--sleep" in argv:
        sleep_out()
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])
