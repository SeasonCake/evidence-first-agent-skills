"""Optional synthetic FFmpeg smoke. No screen/camera input or binary installation."""

import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time

SOURCE = Path(__file__).resolve().parents[1] / 'skills/browser-workflow/scripts/recording_process.py'
spec = importlib.util.spec_from_file_location('recording_process', SOURCE)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', type=Path, required=True)
    parser.add_argument('--ffprobe', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True, help='A new directory; existing results are never overwritten')
    args = parser.parse_args()
    ffmpeg, ffprobe = args.ffmpeg.resolve(), args.ffprobe.resolve()
    if not ffmpeg.is_file() or not ffprobe.is_file():
        parser.error('Provide existing, selected FFmpeg and ffprobe executables')
    root = args.output_dir.resolve()
    root.mkdir(parents=True, exist_ok=False)
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    receipt = {'recorded_at': datetime.datetime.now().astimezone().isoformat(), 'synthetic': True,
               'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'cases': []}
    def save():
        (root/'results.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    failures = []
    for case in ['natural', 'requested', 'deadline']:
        output = root / f'{case}.mp4'
        command = [str(ffmpeg), '-n', '-hide_banner', '-loglevel', 'error', '-re',
                   '-f', 'lavfi', '-i', 'testsrc2=size=160x90:rate=12',
                   '-t', '1' if case == 'natural' else '8', '-an', '-c:v', 'libx264',
                   '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', str(output)]
        row = {'case': case, 'command': command, 'status': 'starting'}
        receipt['cases'].append(row)
        save()
        try:
            started = time.monotonic()
            with (root/f'{case}.stderr.txt').open('wb') as log:
                proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                        stderr=log, bufsize=0, creationflags=flags)
                row.update(pid=proc.pid, status='recording')
                save()
                result = helper.finish_recording(proc, timeout=.65 if case == 'deadline' else 5,
                    stop_requested=(lambda: time.monotonic()-started > .65) if case == 'requested' else None)
            size = output.stat().st_size if output.exists() else 0
            row.update(result, status=helper.recording_status(result, size), bytes=size)
            save()
            probe = subprocess.run([str(ffprobe), '-v', 'error', '-count_frames', '-show_entries',
                'format=duration:stream=codec_name,width,height,nb_read_frames', '-of', 'json', str(output)],
                capture_output=True, text=True, timeout=20, creationflags=flags)
            decode = subprocess.run([str(ffmpeg), '-v', 'error', '-i', str(output), '-f', 'null', '-'],
                capture_output=True, text=True, timeout=20, creationflags=flags)
            row.update(probe_returncode=probe.returncode, decode_returncode=decode.returncode,
                       probe=json.loads(probe.stdout) if probe.returncode == 0 else None)
            save()
            good = (result['process_exited'] and result['returncode'] == 0 and
                    probe.returncode == decode.returncode == 0 and
                    row['status'] == ('failed' if case == 'deadline' else 'recorded-awaiting-qa') and
                    result['stop_reason'] == ('duration' if case == 'natural' else case))
            if not good:
                failures.append(case)
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            row['test_error'] = f'{type(error).__name__}: {error}'
            failures.append(case)
            save()
    receipt['test_result'] = 'FAIL' if failures else 'PASS'
    receipt['failed_cases'] = failures
    save()
    print(json.dumps({'result': receipt['test_result'], 'cases': len(receipt['cases']), 'receipt': str(root/'results.json')}))
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
