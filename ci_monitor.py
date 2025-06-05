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
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any


class CIMonitor:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.build_history_dir = self.repo_path / ".build_history"
        self.builds_dir = self.repo_path / ".builds"
        godot_path = "D:/Games/Godot/Godot_v4.4.1-stable_win64.exe"
        self.godot_exe = Path(godot_path)
        self.last_commit_hash = None
        self.poll_interval = 30  # seconds

        # Setup logging first so we can log errors
        self.setup_logging()

        # Find git executable
        try:
            self.git_exe = self._find_git_executable()
            self.logger.info(f"Found git at: {self.git_exe}")
        except FileNotFoundError as e:
            self.logger.error(str(e))
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

    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = self.repo_path / "logs"
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / "ci_monitor.log"

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def load_state(self):
        """Load the last processed commit hash"""
        state_file = self.build_history_dir / "ci_state.json"
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                    self.last_commit_hash = state.get("last_commit_hash")
                    msg = f"Loaded last processed commit: {self.last_commit_hash}"
                    self.logger.info(msg)
            except Exception as e:
                self.logger.warning(f"Failed to load state: {e}")

    def save_state(self):
        """Save the current state"""
        state_file = self.build_history_dir / "ci_state.json"
        state = {"last_commit_hash": self.last_commit_hash}
        try:
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

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
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get commit hash: {e}")
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
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get commit info: {e}")
            return {
                "hash": commit_hash,
                "message": "Unknown",
                "author": "Unknown",
                "date": "Unknown",
            }

    def run_flake8(self) -> Tuple[bool, str]:
        """Run flake8 linting, excluding addons folder"""
        self.logger.info("Running flake8...")
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
                self.logger.info("✅ flake8 passed")
                return True, "flake8 passed with no issues"
            else:
                error_msg = f"❌ flake8 failed:\n{result.stdout}\n{result.stderr}"
                self.logger.error(error_msg)
                error_return = f"flake8 errors:\n{result.stdout}\n{result.stderr}"
                return False, error_return

        except Exception as e:
            self.logger.error(f"Failed to run flake8: {e}")
            return False, f"Failed to run flake8: {e}"

    def run_pytest(self) -> Tuple[bool, str]:
        """Run pytest test suite"""
        self.logger.info("Running pytest...")
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v", "--tb=no"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                self.logger.info("✅ pytest passed")
                return True, f"pytest passed:\n{result.stdout}"
            else:
                error_msg = f"❌ pytest failed:\n{result.stdout}\n{result.stderr}"
                self.logger.error(error_msg)
                error_return = f"pytest failed:\n{result.stdout}\n{result.stderr}"
                return False, error_return

        except Exception as e:
            self.logger.error(f"Failed to run pytest: {e}")
            return False, f"Failed to run pytest: {e}"

    def run_godot_build(self) -> Tuple[bool, str]:
        """Run headless Godot build using build_local.ps1"""
        self.logger.info("Running Godot build using build_local.ps1...")

        build_script = self.repo_path / "build_local.ps1"
        if not build_script.exists():
            error_msg = f"Build script not found at {build_script}"
            self.logger.error(error_msg)
            return False, error_msg

        try:
            # Run the PowerShell build script with -Build argument
            self.logger.info("Executing build_local.ps1 -Build...")
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
                self.logger.info("✅ Godot build succeeded")
                return True, "Godot build completed successfully"
            else:
                error_msg = f"❌ Godot build failed:\n{result.stdout}\n{result.stderr}"
                self.logger.error(error_msg)
                error_return = f"Godot build failed:\n{result.stdout}\n{result.stderr}"
                return False, error_return

        except Exception as e:
            self.logger.error(f"Failed to run Godot build: {e}")
            return False, f"Failed to run Godot build: {e}"

    def create_build_archive(self, commit_info: Dict[str, Any]) -> Optional[str]:
        """Create archive of build output"""
        if not self.builds_dir.exists():
            error_msg = "Build directory doesn't exist, cannot create archive"
            self.logger.error(error_msg)
            return None

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        commit_short = commit_info["hash"][:8]
        archive_name = f"build_{timestamp}_{commit_short}.zip"
        archive_path = self.build_history_dir / archive_name

        try:
            self.logger.info(f"Creating build archive: {archive_name}")

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

            self.logger.info(f"✅ Build archived: {archive_name}")
            return str(archive_path)

        except Exception as e:
            self.logger.error(f"Failed to create archive: {e}")
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
        except Exception as e:
            self.logger.error(f"Failed to save build report: {e}")

    def process_commit(self, commit_hash: str) -> bool:
        """Process a new commit through the CI pipeline"""
        commit_info = self.get_commit_info(commit_hash)
        commit_short = commit_hash[:8]
        commit_msg = commit_info["message"]
        msg = f"Processing commit {commit_short}: {commit_msg}"
        self.logger.info(msg)

        # Run flake8
        flake8_success, flake8_output = self.run_flake8()
        if not flake8_success:
            self.logger.error("CI pipeline failed at flake8 stage")
            self.create_build_report("", commit_info, False)
            return False

        # Run pytest
        pytest_success, pytest_output = self.run_pytest()
        if not pytest_success:
            self.logger.error("CI pipeline failed at pytest stage")
            self.create_build_report("", commit_info, False)
            return False

        # Run Godot build
        build_success, build_output = self.run_godot_build()
        if not build_success:
            self.logger.error("CI pipeline failed at build stage")
            self.create_build_report("", commit_info, False)
            return False

        # Create archive
        archive_path = self.create_build_archive(commit_info)
        if archive_path:
            success_msg = (
                f"✅ CI pipeline completed successfully for commit "
                f"{commit_hash[:8]}"
            )
            self.logger.info(success_msg)
            return True
        else:
            self.logger.error("CI pipeline failed at archiving stage")
            self.create_build_report("", commit_info, False)
            return False

    def check_for_new_commits(self) -> bool:
        """Check if there are new commits to process"""
        current_commit = self.get_latest_commit_hash()
        if not current_commit:
            return False

        if current_commit != self.last_commit_hash:
            self.logger.info(f"New commit detected: {current_commit}")

            # Process the commit
            if self.process_commit(current_commit):
                self.last_commit_hash = current_commit
                self.save_state()
                return True
            else:
                error_msg = (
                    "Failed to process commit, not updating last processed " "commit"
                )
                self.logger.error(error_msg)
                return False

        return False

    def run(self):
        """Main monitoring loop"""
        self.logger.info("Starting CI monitor...")
        self.logger.info(f"Monitoring repository: {self.repo_path}")
        self.logger.info(f"Build history directory: {self.build_history_dir}")
        self.logger.info(f"Poll interval: {self.poll_interval} seconds")
        self.logger.info(f"Git executable: {self.git_exe}")

        # Check if we're in a git repository
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            self.logger.error("Not a git repository!")
            sys.exit(1)

        # Initial check
        if self.last_commit_hash is None:
            current_commit = self.get_latest_commit_hash()
            if current_commit:
                self.last_commit_hash = current_commit
                self.save_state()
                init_msg = f"Initialized with current commit: {current_commit}"
                self.logger.info(init_msg)

        try:
            while True:
                self.check_for_new_commits()
                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            self.logger.info("CI monitor stopped by user")
        except Exception as e:
            self.logger.error(f"CI monitor crashed: {e}")
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
