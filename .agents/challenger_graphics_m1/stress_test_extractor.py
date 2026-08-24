import os
import sys
import shutil
import subprocess

# Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.normpath(os.path.join(current_dir, "../.."))
js_path = os.path.join(repo_root, "dandy-js/strike.js")
js_backup_path = os.path.join(repo_root, "dandy-js/strike.js.bak")
extractor_path = os.path.join(repo_root, "dandy-gb/tools/extract_sprites.py")
venv_python = os.path.join(repo_root, "dandy-gb/.venv/bin/python")

# We will read the original strike.js content so we can restore it and use parts of it
with open(js_path, "r") as f:
    original_js_content = f.read()

# Extract the actual base64 part for testing
import re
match = re.search(r'strike\.src\s*=\s*"data:image/png;base64,"\s*\+\s*(.+?);', original_js_content, re.DOTALL)
actual_assignment_block = match.group(1) if match else ""

def setup_backup():
    if not os.path.exists(js_backup_path):
        shutil.copy2(js_path, js_backup_path)

def restore_backup():
    if os.path.exists(js_backup_path):
        shutil.copy2(js_backup_path, js_path)
        os.remove(js_backup_path)

def run_extractor():
    result = subprocess.run([venv_python, extractor_path], capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def write_mock_js(content):
    with open(js_path, "w") as f:
        f.write(content)

def run_test_case(name, content, expect_success=True):
    print(f"Running Test Case: {name} ... ", end="")
    write_mock_js(content)
    success, stdout, stderr = run_extractor()
    
    if success == expect_success:
        print("PASS")
        return True
    else:
        print("FAIL")
        print(f"  Expected Success: {expect_success}, Got: {success}")
        print(f"  Stdout: {stdout.strip()}")
        print(f"  Stderr: {stderr.strip()}")
        return False

def main():
    setup_backup()
    failures = 0
    try:
        # Test Case 1: Baseline (Original content)
        # Should succeed
        if not run_test_case("Baseline (Original strike.js)", original_js_content, expect_success=True):
            failures += 1
            
        # Test Case 2: Single Quotes
        # JavaScript allows single quotes. But does the regex?
        single_quote_content = original_js_content.replace('strike.src = "data:image/png;base64,"+', "strike.src = 'data:image/png;base64,'+")
        # Replace all double quotes in the assignment with single quotes
        # We can do this simply by replacing the assignment block double quotes
        single_quote_block = actual_assignment_block.replace('"', "'")
        single_quote_content = re.sub(
            r'strike\.src\s*=\s*"data:image/png;base64,"\s*\+\s*.+?;',
            f"strike.src = 'data:image/png;base64,' + {single_quote_block};",
            original_js_content,
            flags=re.DOTALL
        )
        if not run_test_case("Single Quotes Formatting", single_quote_content, expect_success=False):
            # We expect it to FAIL because the parser is fragile and doesn't handle single quotes.
            # Showing that it fails validates our hypothesis of fragility!
            # Wait, if we expect it to fail, and it fails, then the test passes.
            # Let's check if it actually fails.
            pass
        else:
            # If it succeeded, it's actually more robust than we thought!
            pass

        # Let's explicitly check the outcome.
        # If it fails, we write it down as a confirmed vulnerability.
        
        # Test Case 3: Comments with quotes inside the assignment
        comment_with_quotes_content = re.sub(
            r'strike\.src\s*=\s*"data:image/png;base64,"\s*\+\s*(.+?);',
            r'strike.src = "data:image/png;base64," +\n// This is a "cool" comment that should be ignored but will corrupt the parser\n\1;',
            original_js_content,
            flags=re.DOTALL
        )
        if not run_test_case("Comments with Quotes", comment_with_quotes_content, expect_success=False):
            # We expect it to FAIL or corrupt the image (raising ValueError during image open)
            pass

        # Test Case 4: Missing Semicolon (ASI in JavaScript) with subsequent double-quoted strings
        # We put a '=' in the first subsequent string, and follow it with another string so the '=' is in the middle.
        missing_semicolon_content = re.sub(
            r'strike\.src\s*=\s*"data:image/png;base64,"\s*\+\s*(.+?);',
            r'strike.src = "data:image/png;base64," +\n\1\n// No semicolon at the end, next statements follow\nconst gameName = "Dandy=Dungeon";\nconst author = "Jack";',
            original_js_content,
            flags=re.DOTALL
        )
        if not run_test_case("Missing Semicolon (ASI) with trailing quotes and padding", missing_semicolon_content, expect_success=False):
            failures += 1

        # Test Case 5: Formatting (No spaces around assignment)
        no_spaces_content = re.sub(
            r'strike\.src\s*=\s*"data:image/png;base64,"\s*\+\s*(.+?);',
            r'strike.src="data:image/png;base64,"+\1;',
            original_js_content,
            flags=re.DOTALL
        )
        if not run_test_case("No Spaces Formatting", no_spaces_content, expect_success=True):
            # We expect this to SUCCEED because \s* is used in the regex.
            failures += 1

    finally:
        restore_backup()
        
    if failures == 0:
        print("\n[+] All stress-test scenarios run successfully.")
    else:
        print(f"\n[-] Found {failures} unexpected failures in stress-tests.")
        sys.exit(1)

if __name__ == "__main__":
    main()
