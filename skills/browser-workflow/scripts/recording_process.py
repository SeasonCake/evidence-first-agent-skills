"""Bounded shutdown for one caller-owned FFmpeg process; never drives a UI."""

from __future__ import annotations

import math
import subprocess
import time
from typing import Callable


def finish_recording(
    proc: subprocess.Popen,
    *,
    timeout: float,
    stop_requested: Callable[[], bool] | None = None,
    quit_grace: float = 5,
    kill_grace: float = 3,
) -> dict:
    """Wait, send q at most once, then kill/reap only this process if necessary.

    The caller spawns FFmpeg directly (no shell), owns stdin exclusively, redirects
    stdout/stderr to files or DEVNULL, and records PID/command before this call.
    Do not pass a process with undrained stdout/stderr PIPEs or reuse communicate(input).
    A deadline remains a failure even if q seals a playable file with exit code zero.
    """
    for value in (timeout, quit_grace, kill_grace):
        if not math.isfinite(value) or value <= 0:
            raise ValueError('Timeout and grace periods must be positive and finite')
    started = time.monotonic()
    deadline = started + timeout
    reason = 'duration'
    shutdown = 'natural'
    errors = []
    try:
        while proc.poll() is None:
            if stop_requested is not None and stop_requested():
                reason = 'requested'
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                reason = 'deadline'
                break
            try:
                proc.wait(timeout=min(0.1, remaining))
            except subprocess.TimeoutExpired:
                pass
        if proc.poll() is None:
            shutdown = 'quit'
            try:
                if proc.stdin is None:
                    raise OSError('No owned stdin for graceful shutdown')
                proc.stdin.write(b'q\n')
                proc.stdin.flush()
            except (BrokenPipeError, OSError, ValueError) as error:
                errors.append(f'quit: {type(error).__name__}')
            try:
                proc.wait(timeout=quit_grace)
            except subprocess.TimeoutExpired:
                shutdown = 'kill'
                try:
                    proc.kill()
                except OSError as error:
                    errors.append(f'kill: {type(error).__name__}')
                try:
                    proc.wait(timeout=kill_grace)
                except subprocess.TimeoutExpired:
                    shutdown = 'kill-unconfirmed'
        code = proc.poll()
    except BaseException as error:
        reason = 'controller-error'
        shutdown = 'kill'
        errors.append(f'controller: {type(error).__name__}')
        try:
            if proc.poll() is None:
                proc.kill()
            proc.wait(timeout=kill_grace)
        except (OSError, subprocess.TimeoutExpired) as cleanup_error:
            shutdown = 'kill-unconfirmed'
            errors.append(f'cleanup: {type(cleanup_error).__name__}')
        code = proc.poll()
    finally:
        if proc.stdin is not None:
            try:
                proc.stdin.close()
            except (BrokenPipeError, OSError, ValueError):
                pass
    return {
        'returncode': code, 'process_exited': code is not None,
        'stop_reason': reason, 'shutdown': shutdown,
        'deadline_expired': reason == 'deadline',
        'elapsed_seconds': time.monotonic() - started, 'shutdown_errors': errors,
    }


def recording_status(result: dict, output_bytes: int) -> str:
    """This lifecycle state does not prove duration, decode or visual correctness."""
    ready = (result['process_exited'] and result['returncode'] == 0 and output_bytes > 0
             and result['stop_reason'] in {'duration', 'requested'}
             and result['shutdown'] in {'natural', 'quit'})
    return 'recorded-awaiting-qa' if ready else 'failed'
