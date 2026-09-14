"""Real child-process controls, without a camera, desktop capture, or FFmpeg dependency."""

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'skills/browser-workflow/scripts/recording_process.py'
spec = importlib.util.spec_from_file_location('recording_process', SOURCE)
recording = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recording)


class RecordingProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.children = []

    def tearDown(self):
        for child in self.children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=3)
            if child.stdin and not child.stdin.closed:
                child.stdin.close()
        self.temp.cleanup()

    def child(self, body):
        ready = Path(self.temp.name) / f'{len(self.children)}.ready'
        script = f'from pathlib import Path\nimport sys, os, time\n{body}'
        proc = subprocess.Popen([sys.executable, '-u', '-c', script, str(ready)],
                                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, bufsize=0,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        self.children.append(proc)
        return proc, ready

    def await_ready(self, proc, ready):
        deadline = time.monotonic() + 5
        while not ready.exists() and proc.poll() is None and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertTrue(ready.exists(), 'synthetic child failed to reach its test branch')

    def finish(self, proc, **options):
        result = recording.finish_recording(proc, timeout=.1, quit_grace=.5, kill_grace=3, **options)
        self.assertTrue(result['process_exited'])
        self.assertIsNotNone(proc.poll())
        self.assertTrue(proc.stdin.closed)
        self.assertLess(result['elapsed_seconds'], 5)
        return result

    def test_natural_success_failure_and_empty_output(self):
        for code in (0, 4):
            with self.subTest(code=code):
                proc, _ = self.child(f'sys.exit({code})')
                proc.wait(timeout=5)
                result = self.finish(proc)
                self.assertEqual(result['returncode'], code)
                self.assertEqual(result['shutdown'], 'natural')
                self.assertEqual(recording.recording_status(result, 10),
                                 'recorded-awaiting-qa' if code == 0 else 'failed')
                self.assertEqual(recording.recording_status(result, 0), 'failed')

    def test_deadline_graceful_quit_is_still_failure(self):
        proc, ready = self.child("Path(sys.argv[1]).touch()\nsys.exit(0 if sys.stdin.readline().strip() == 'q' else 7)")
        self.await_ready(proc, ready)
        result = self.finish(proc)
        self.assertEqual((result['stop_reason'], result['shutdown'], result['returncode']), ('deadline','quit',0))
        self.assertEqual(recording.recording_status(result, 100), 'failed')

    def test_requested_stop_is_distinct_from_deadline(self):
        proc, ready = self.child("Path(sys.argv[1]).touch()\nsys.exit(0 if sys.stdin.readline().strip() == 'q' else 7)")
        self.await_ready(proc, ready)
        result = self.finish(proc, stop_requested=lambda: True)
        self.assertEqual((result['stop_reason'], result['shutdown']), ('requested', 'quit'))
        self.assertEqual(recording.recording_status(result, 100), 'recorded-awaiting-qa')

    def test_ignored_quit_is_killed_and_reaped(self):
        proc, ready = self.child('Path(sys.argv[1]).touch()\ntime.sleep(60)')
        self.await_ready(proc, ready)
        result = self.finish(proc)
        self.assertEqual(result['shutdown'], 'kill')
        self.assertEqual(recording.recording_status(result, 100), 'failed')

    def test_closed_stdin_does_not_escape_receipt(self):
        proc, ready = self.child('os.close(0)\nPath(sys.argv[1]).touch()\ntime.sleep(60)')
        self.await_ready(proc, ready)
        result = self.finish(proc)
        self.assertEqual(result['shutdown'], 'kill')
        self.assertTrue(result['shutdown_errors'])
        self.assertEqual(recording.recording_status(result, 100), 'failed')

    def test_controller_error_still_reaps_owned_process(self):
        proc, ready = self.child('Path(sys.argv[1]).touch()\ntime.sleep(60)')
        self.await_ready(proc, ready)
        def fail():
            raise OSError('synthetic stop probe error')
        result = self.finish(proc, stop_requested=fail)
        self.assertEqual(result['stop_reason'], 'controller-error')
        self.assertEqual(recording.recording_status(result, 100), 'failed')

    def test_invalid_deadline_is_rejected_before_waiting(self):
        for value in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                recording.finish_recording(None, timeout=value)


if __name__ == '__main__':
    unittest.main()
