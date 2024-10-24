#!/usr/bin/env python3
import subprocess
import time
import datetime
import sys
import os
import re
import webbrowser
from urllib.request import urlopen
from typing import Tuple, List, Optional

# Configuration constants
WORKFLOW_START_WAIT = 10  # seconds to wait for workflow to start
WORKFLOW_TIMEOUT = 300    # seconds to wait for workflow to complete
CACHE_WAIT = 30          # seconds to wait for caches to sync
CANARY_RETRY_COUNT = 3   # number of times to retry canary verification
CANARY_RETRY_DELAY = 10  # seconds between canary verification attempts

class DeploymentVerifier:
    def __init__(self, repo_url: str, canary_path: str):
        self.repo_url = repo_url
        self.canary_path = canary_path
        self.timestamp = datetime.datetime.now().isoformat()
        self.first_changed_file = None

    def run_command(self, cmd: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
        """Run a command and return returncode, stdout, stderr"""
        print(f"\n📋 Running command: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=capture_output, text=True)
            if result.returncode != 0:
                print(f"⚠️  Command returned error code {result.returncode}")
                if result.stderr:
                    print(f"Error output:\n{result.stderr}")
            return result.returncode, result.stdout, result.stderr
        except subprocess.SubprocessError as e:
            print(f"❌ Error running command {' '.join(cmd)}: {e}")
            sys.exit(1)

    def get_git_status(self) -> Tuple[List[str], List[str], List[str]]:
        """Returns lists of added, modified, and deleted files"""
        print("\n🔍 Checking git status...")
        status_code, status_output, _ = self.run_command(['git', 'status', '--porcelain'])
        if status_code != 0:
            print("❌ Failed to get git status")
            sys.exit(1)

        added = []
        modified = []
        deleted = []

        for line in status_output.splitlines():
            if not line.strip():
                continue
            status = line[:2]
            filename = line[3:].strip()
            
            if status.startswith('??'):
                added.append(filename)
                if not self.first_changed_file:
                    self.first_changed_file = filename
            elif status.startswith(' M') or status.startswith('M '):
                modified.append(filename)
                if not self.first_changed_file:
                    self.first_changed_file = filename
            elif status.startswith(' D') or status.startswith('D '):
                deleted.append(filename)
                if not self.first_changed_file:
                    self.first_changed_file = filename

        print(f"📊 Status summary:")
        if added: print(f"  Added: {added}")
        if modified: print(f"  Modified: {modified}")
        if deleted: print(f"  Deleted: {deleted}")
        if not (added or modified or deleted):
            print("  No changes detected")

        return added, modified, deleted

    def create_commit_message(self, added: List[str], modified: List[str], deleted: List[str]) -> str:
        """Create a descriptive commit message"""
        print("\n📝 Creating commit message...")
        parts = []
        if added:
            files_str = ', '.join(added[:3])
            if len(added) > 3:
                files_str += f' and {len(added)-3} more'
            parts.append(f"Added {files_str}")
        
        if modified:
            files_str = ', '.join(modified[:3])
            if len(modified) > 3:
                files_str += f' and {len(modified)-3} more'
            parts.append(f"Modified {files_str}")
            
        if deleted:
            files_str = ', '.join(deleted[:3])
            if len(deleted) > 3:
                files_str += f' and {len(deleted)-3} more'
            parts.append(f"Deleted {files_str}")

        msg = '; '.join(parts) if parts else "No changes"
        print(f"✍️  Commit message: {msg}")
        return msg

    def update_canary_file(self) -> None:
        """Update the canary file with current timestamp"""
        print(f"\n🐦 Updating canary file at {self.canary_path}")
        os.makedirs(os.path.dirname(self.canary_path), exist_ok=True)
        with open(self.canary_path, 'w') as f:
            f.write(self.timestamp)
        print(f"✅ Canary updated with timestamp: {self.timestamp}")

    def wait_for_workflow(self, timeout: int = WORKFLOW_TIMEOUT) -> bool:
        """Wait for the most recent workflow run to complete"""
        print(f"\n⏳ Waiting {WORKFLOW_START_WAIT} seconds for workflow to start...")
        time.sleep(WORKFLOW_START_WAIT)
        
        print("🔄 Monitoring workflow status...")
        start_time = time.time()
        last_status = None

        while time.time() - start_time < timeout:
            code, output, _ = self.run_command(['gh', 'run', 'list', '--limit', '1'])
            if code != 0:
                print("❌ Failed to get workflow runs")
                return False

            if not output.strip():
                print("⚠️  No workflow runs found")
                return False

            run_info = output.strip().split()
            if len(run_info) < 3:
                print("⚠️  Unexpected workflow run output format")
                return False

            status = run_info[2]
            
            if status != last_status:
                print(f"📊 Workflow status: {status}")
                last_status = status

            if status == 'completed':
                print("✅ Workflow completed successfully!")
                return True
            elif status in ['failed', 'cancelled']:
                print(f"❌ Workflow {status}!")
                return False
                
            time.sleep(10)

        print(f"⚠️  Timeout after {timeout} seconds")
        return False

    def verify_canary(self, url: str, retry_count: int = CANARY_RETRY_COUNT, 
                     retry_delay: int = CANARY_RETRY_DELAY) -> bool:
        """Verify the canary file contains the expected timestamp"""
        print(f"\n🔍 Verifying canary file at {url}")
        
        for attempt in range(retry_count):
            print(f"\n📡 Verification attempt {attempt + 1} of {retry_count}")
            try:
                with urlopen(url) as response:
                    content = response.read().decode('utf-8')
                    
                    if self.timestamp in content:
                        print("✅ Canary verification successful!")
                        return True
                    
                    print("❌ Canary content doesn't match")
                    print(f"Expected: {self.timestamp}")
                    print(f"Found: {content[:200]}...")
                    
            except Exception as e:
                print(f"❌ Error fetching canary: {e}")
            
            if attempt < retry_count - 1:
                print(f"⏳ Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

        return False

    def open_changed_file(self) -> None:
        """Open the first changed file in web browser"""
        if self.first_changed_file and self.first_changed_file != self.canary_path:
            print(f"\n🌐 Opening first changed file in browser: {self.first_changed_file}")
            # Convert file path to URL
            file_url = f"{self.repo_url}/{self.first_changed_file}"
            if file_url.endswith('.md'):
                file_url = file_url[:-3] + '.html'
            print(f"🔗 URL: {file_url}")
            webbrowser.open(file_url)
        else:
            print("\n📝 No non-canary files were changed")

    def run(self) -> bool:
        """Run the complete verification process"""
        print("\n🚀 Starting deployment verification process...")
        # 0. TODO do a preview build 
        # 1. Check for changes and add new files
        added, modified, deleted = self.get_git_status()
        if added:
            print(f"\n📥 Adding new files to git...")
            self.run_command(['git', 'add'] + added)

        # 2. Create commit message
        commit_message = self.create_commit_message(added, modified, deleted)

        # 3. Update canary file
        self.update_canary_file()

        # 4. Commit and push
        print("\n📤 Committing and pushing changes...")
        self.run_command(['git', 'add', self.canary_path])
        self.run_command(['git', 'commit', '-m', commit_message])
        push_code, _, _ = self.run_command(['git', 'push', 'origin', 'main'])
        if push_code != 0:
            print("❌ Failed to push changes")
            return False

        # 5. Wait for workflow
        if not self.wait_for_workflow():
            return False

        # 6. Wait for caches
        print(f"\n⏳ Waiting {CACHE_WAIT} seconds for caches to sync...")
        time.sleep(CACHE_WAIT)

        # 7. Verify canary
        canary_url = f"{self.repo_url}/{self.canary_path}"
        success = self.verify_canary(canary_url)

        # 8. Open changed file in browser
        if success:
            self.open_changed_file()

        return success

def main():
    # These should be configured for your repository
    REPO_URL = "https://dfeldman.github.io/dfeldman"
    CANARY_PATH = "content/canary.txt"  # Adjust based on your Hugo structure

    print("🔧 Deploy Verification Script")
    print(f"📍 Repository URL: {REPO_URL}")
    print(f"🐦 Canary Path: {CANARY_PATH}")

    verifier = DeploymentVerifier(REPO_URL, CANARY_PATH)
    success = verifier.run()
    
    if success:
        print("\n✨ Deployment verification completed successfully! ✨")
        sys.exit(0)
    else:
        print("\n❌ Deployment verification failed! ❌")
        sys.exit(1)

if __name__ == "__main__":
    main()

