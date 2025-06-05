#!/usr/bin/env python3
"""
Continuous Integration Monitor for PolyhedronEmu
Monitors git commits and runs CI pipeline: flake8 -> pytest -> build -> archive
"""

import os
import sys
import time
import subprocess
import datetime
import zipfile
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

try:
    import psutil
except ImportError:
    psutil = None


class CIMonitor:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.build_history_dir = self.repo_path / ".build_history"
        self.builds_dir = self.repo_path / ".builds"
        godot_path = "D:/Games/Godot/Godot_v4.4.1-stable_win64.exe"
        self.godot_exe = Path(godot_path)
        self.last_commit_hash = None
        self.poll_interval = 30  # seconds

        # Find git executable
        try:
            self.git_exe = self._find_git_executable()
        except FileNotFoundError:
            sys.exit(1)

        # Ensure directories exist
        self.build_history_dir.mkdir(exist_ok=True)

        # Load last processed commit
        self.load_state()

    def _find_git_executable(self) -> str:
        """Find git executable in common locations"""
        common_paths = [
            "git",  # Try PATH first
            "C:/Program Files/Git/bin/git.exe",
            "C:/Program Files (x86)/Git/bin/git.exe",
            "/usr/bin/git",
            "/usr/local/bin/git",
        ]

        for git_path in common_paths:
            try:
                result = subprocess.run(
                    [git_path, "--version"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return git_path
            except (
                subprocess.CalledProcessError,
                FileNotFoundError,
                subprocess.TimeoutExpired,
            ):
                continue

        raise FileNotFoundError(
            "Git executable not found. Please install Git or add it to PATH."
        )

    def get_cpu_utilization(self) -> float:
        """Get current CPU utilization percentage"""
        if psutil is None:
            return 0.0

        try:
            # Get CPU usage over a 1 second interval for accuracy
            cpu_percent = psutil.cpu_percent(interval=1)
            return cpu_percent
        except Exception:
            return 0.0

    def get_gpu_utilization(self) -> float:
        """Get current GPU utilization percentage"""
        try:
            # Try NVIDIA GPU first using nvidia-smi
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                gpu_usage = float(result.stdout.strip().split("\n")[0])
                return gpu_usage
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            ValueError,
            subprocess.TimeoutExpired,
        ):
            pass

        try:
            # Fallback to PowerShell WMI query for integrated/other GPUs
            powershell_cmd = (
                "Get-Counter '\\GPU Engine(*)\\Utilization Percentage' | "
                "Select-Object -ExpandProperty CounterSamples | "
                "Measure-Object -Property CookedValue -Maximum | "
                "Select-Object -ExpandProperty Maximum"
            )
            result = subprocess.run(
                ["powershell", "-Command", powershell_cmd],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                gpu_usage = float(result.stdout.strip())
                return gpu_usage
        except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired):
            pass

        # If all methods fail, assume 0% usage
        return 0.0

    def check_system_load(self) -> Tuple[bool, str]:
        """Check if system load is acceptable for running CI pipeline"""
        cpu_usage = self.get_cpu_utilization()
        gpu_usage = self.get_gpu_utilization()

        cpu_threshold = 10.0
        gpu_threshold = 10.0

        if cpu_usage > cpu_threshold:
            return (
                False,
                f"CPU usage too high: {cpu_usage:.1f}% (threshold: {cpu_threshold}%)",
            )

        if gpu_usage > gpu_threshold:
            return (
                False,
                f"GPU usage too high: {gpu_usage:.1f}% (threshold: {gpu_threshold}%)",
            )

        return (
            True,
            f"System load acceptable (CPU: {cpu_usage:.1f}%, GPU: {gpu_usage:.1f}%)",
        )

    def load_state(self):
        """Load the last processed commit hash"""
        state_file = self.build_history_dir / "ci_state.json"
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                    self.last_commit_hash = state.get("last_commit_hash")
            except Exception:
                pass

    def save_state(self):
        """Save the current state"""
        state_file = self.build_history_dir / "ci_state.json"
        state = {"last_commit_hash": self.last_commit_hash}
        try:
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass

    def get_latest_commit_hash(self) -> Optional[str]:
        """Get the latest commit hash from git"""
        try:
            result = subprocess.run(
                [self.git_exe, "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def get_commit_info(self, commit_hash: str) -> Dict[str, Any]:
        """Get commit information"""
        try:
            # Get commit message
            result = subprocess.run(
                [self.git_exe, "log", "-1", "--pretty=format:%s", commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            message = result.stdout.strip()

            # Get commit author and date
            cmd = [
                self.git_exe,
                "log",
                "-1",
                "--pretty=format:%an|%ad",
                "--date=iso",
                commit_hash,
            ]
            result = subprocess.run(
                cmd, cwd=self.repo_path, capture_output=True, text=True, check=True
            )
            author, date = result.stdout.strip().split("|")

            return {
                "hash": commit_hash,
                "message": message,
                "author": author,
                "date": date,
            }
        except subprocess.CalledProcessError:
            return {
                "hash": commit_hash,
                "message": "Unknown",
                "author": "Unknown",
                "date": "Unknown",
            }

    def run_flake8(self) -> Tuple[bool, str]:
        """Run flake8 linting, excluding addons folder"""
        print("Running flake8...")
        try:
            cmd = [
                "python",
                "-m",
                "flake8",
                ".",
                "--exclude=addons",
                "--max-line-length=100",
            ]
            result = subprocess.run(
                cmd, cwd=self.repo_path, capture_output=True, text=True
            )

            if result.returncode == 0:
                print("✅ flake8 passed")
                return True, "flake8 passed with no issues"
            else:
                print("❌ flake8 failed")
                error_return = f"flake8 errors:\n{result.stdout}\n{result.stderr}"
                return False, error_return

        except Exception as e:
            print(f"❌ Failed to run flake8: {e}")
            return False, f"Failed to run flake8: {e}"

    def run_pytest(self) -> Tuple[bool, str]:
        """Run pytest test suite"""
        print("Running pytest...")
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v", "--tb=no"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ pytest passed")
                return True, f"pytest passed:\n{result.stdout}"
            else:
                print("❌ pytest failed")
                error_return = f"pytest failed:\n{result.stdout}\n{result.stderr}"
                return False, error_return

        except Exception as e:
            print(f"❌ Failed to run pytest: {e}")
            return False, f"Failed to run pytest: {e}"

    def run_godot_build(self) -> Tuple[bool, str]:
        """Run headless Godot build using build_local.ps1"""
        print("Running Godot build...")
        build_script = self.repo_path / "build_local.ps1"
        if not build_script.exists():
            error_msg = f"Build script not found at {build_script}"
            print(f"❌ {error_msg}")
            return False, error_msg

        try:
            # Run the PowerShell build script with -Build argument
            result = subprocess.run(
                [
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(build_script),
                    "-Build",
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ Godot build succeeded")
                return True, "Godot build completed successfully"
            else:
                print("❌ Godot build failed")
                error_return = f"Godot build failed:\n{result.stdout}\n{result.stderr}"
                return False, error_return

        except Exception as e:
            print(f"❌ Failed to run Godot build: {e}")
            return False, f"Failed to run Godot build: {e}"

    def create_build_archive(self, commit_info: Dict[str, Any]) -> Optional[str]:
        """Create archive of build output"""
        if not self.builds_dir.exists():
            return None

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        commit_short = commit_info["hash"][:8]
        archive_name = f"build_{timestamp}_{commit_short}.zip"
        archive_path = self.build_history_dir / archive_name

        try:
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.builds_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arc_path = file_path.relative_to(self.builds_dir)
                        zipf.write(file_path, arc_path)

                # Add commit info
                commit_info_str = json.dumps(commit_info, indent=2)
                zipf.writestr("commit_info.json", commit_info_str)

            # Create build report
            self.create_build_report(archive_name, commit_info, True)

            return str(archive_path)

        except Exception:
            return None

    def create_build_report(
        self, archive_name: str, commit_info: Dict[str, Any], success: bool
    ):
        """Create a build report"""
        report_file = self.build_history_dir / "build_report.json"

        # Load existing reports
        reports = []
        if report_file.exists():
            try:
                with open(report_file, "r") as f:
                    reports = json.load(f)
            except Exception:
                pass

        # Add new report
        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "commit": commit_info,
            "success": success,
            "archive": archive_name if success else None,
        }

        reports.append(report)

        # Keep only last 50 reports
        reports = reports[-50:]

        # Save reports
        try:
            with open(report_file, "w") as f:
                json.dump(reports, f, indent=2)
        except Exception:
            pass

    def process_commit(self, commit_hash: str) -> bool:
        """Process a new commit through the CI pipeline"""
        commit_info = self.get_commit_info(commit_hash)
        commit_short = commit_hash[:8]
        commit_msg = commit_info["message"]
        print(f"Processing commit {commit_short}: {commit_msg}")

        # Run flake8
        flake8_success, flake8_output = self.run_flake8()
        if not flake8_success:
            print("❌ CI pipeline failed at flake8 stage")
            self.create_build_report("", commit_info, False)
            return False

        # Run pytest
        pytest_success, pytest_output = self.run_pytest()
        if not pytest_success:
            print("❌ CI pipeline failed at pytest stage")
            self.create_build_report("", commit_info, False)
            return False

        # Run Godot build
        build_success, build_output = self.run_godot_build()
        if not build_success:
            print("❌ CI pipeline failed at build stage")
            self.create_build_report("", commit_info, False)
            return False

        # Create archive
        archive_path = self.create_build_archive(commit_info)
        if archive_path:
            print(f"✅ CI pipeline completed successfully for commit {commit_short}")
            return True
        else:
            print("❌ CI pipeline failed at archiving stage")
            self.create_build_report("", commit_info, False)
            return False

    def check_for_new_commits(self) -> bool:
        """Check if there are new commits to process"""
        current_commit = self.get_latest_commit_hash()
        if not current_commit:
            return False

        if current_commit != self.last_commit_hash:
            print(f"New commit detected: {current_commit}")

            # Check system load before processing
            load_ok, load_msg = self.check_system_load()
            if not load_ok:
                print(f"⏸️ Skipping CI: {load_msg}")
                return False

            print(f"✅ {load_msg}")

            # Process the commit
            if self.process_commit(current_commit):
                self.last_commit_hash = current_commit
                self.save_state()
                return True
            else:
                return False

        return False

    def run(self):
        """Main monitoring loop"""
        print("Starting CI monitor...")
        print(f"Monitoring repository: {self.repo_path}")
        print(f"Poll interval: {self.poll_interval} seconds")

        # Check if we're in a git repository
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            print("❌ Not a git repository!")
            sys.exit(1)

        # Initial check
        if self.last_commit_hash is None:
            current_commit = self.get_latest_commit_hash()
            if current_commit:
                self.last_commit_hash = current_commit
                self.save_state()
                print(f"Initialized with current commit: {current_commit}")
        else:
            print(f"Last processed commit: {self.last_commit_hash}")

        try:
            while True:
                self.check_for_new_commits()
                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            print("\nCI monitor stopped by user")
        except Exception as e:
            print(f"❌ CI monitor crashed: {e}")
            sys.exit(1)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="PolyhedronEmu CI Monitor")
    parser.add_argument(
        "--repo-path",
        default=".",
        help="Path to repository (default: current directory)",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=30,
        help="Poll interval in seconds (default: 30)",
    )
    parser.add_argument("--godot-exe", help="Path to Godot executable")

    args = parser.parse_args()

    monitor = CIMonitor(args.repo_path)

    if args.poll_interval:
        monitor.poll_interval = args.poll_interval

    if args.godot_exe:
        monitor.godot_exe = Path(args.godot_exe)

    monitor.run()


if __name__ == "__main__":
    main()
