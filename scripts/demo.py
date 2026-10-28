"""Run the two local services with a shared ephemeral service credential."""

import argparse
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--web-port", type=int, default=3000)
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--production", action="store_true", help="Use a previously built Next.js bundle.")
    parser.add_argument("--live", action="store_true", help="Explicitly enable configured OpenAI chat; case data stays synthetic.")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.web_port == args.api_port:
        parser.error("Web and API ports must differ.")
    for port in (args.web_port, args.api_port):
        if not 1024 <= port <= 65535:
            parser.error("Ports must be between 1024 and 65535.")
        with socket.socket() as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                parser.error(f"Port {port} is already in use; choose a different port.")
    if args.live and not all(os.environ.get(k) for k in ("OPENAI_API_KEY", "OPENAI_MODEL")):
        parser.error("--live requires OPENAI_API_KEY and OPENAI_MODEL. No fixture will impersonate a live connection.")
    env = {**os.environ,
           "BENEFITS_SERVICE_SECRET": secrets.token_urlsafe(48),
           "BENEFITS_SERVICE_URL": f"http://127.0.0.1:{args.api_port}",
           "BENEFITS_APP_ORIGIN": f"http://127.0.0.1:{args.web_port}",
           "BENEFITS_MODE": "live" if args.live else "synthetic",
           "NEXT_TELEMETRY_DISABLED": "1",
           "DO_NOT_TRACK": "1",
           "COPILOTKIT_TELEMETRY_DISABLED": "true",
           "SCARF_ANALYTICS": "false",
           "OTEL_SDK_DISABLED": "true"}
    processes = []
    try:
        processes.append(subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "service.app:app", "--host", "127.0.0.1",
             "--port", str(args.api_port), "--no-access-log"], cwd=root, env=env))
        processes.append(subprocess.Popen(
            ["node", str(root / "node_modules" / "next" / "dist" / "bin" / "next"),
             "start" if args.production else "dev", "--hostname", "127.0.0.1", "--port", str(args.web_port)],
            cwd=root, env=env))
        for port, endpoint in ((args.api_port, "/health"), (args.web_port, "/")):
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                if any(p.poll() is not None for p in processes):
                    raise RuntimeError("A service exited during startup; inspect its error above.")
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}{endpoint}", timeout=3) as response:
                        if response.status == 200:
                            break
                except (OSError, TimeoutError):
                    time.sleep(.5)
            else:
                raise RuntimeError(f"Service on port {port} did not become ready.")
        print(f"Benefits IQ ready: http://127.0.0.1:{args.web_port} | "
              f"{'CONFIGURED MODEL CHAT' if args.live else 'SYNTHETIC DETERMINISTIC MODE'}", flush=True)
        while all(p.poll() is None for p in processes):
            time.sleep(1)
        raise RuntimeError("A service stopped unexpectedly.")
    except KeyboardInterrupt:
        print("Stopping Benefits IQ.", flush=True)
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == "__main__":
    main()
