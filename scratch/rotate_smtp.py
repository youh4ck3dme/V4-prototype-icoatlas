import subprocess
import os

PASS_FILE = "/Users/erikbabcan/.gemini/antigravity-ide/brain/f903585d-628e-46ae-b38e-6020b3958f0b/pass.md"

def read_new_password():
    with open(PASS_FILE, "r") as f:
        content = f.read().strip()
    # If the file has metadata header, get the last line or parse it.
    # The file contains:
    # Created At: ...
    # Completed At: ...
    # File Path: ...
    # Total Lines: ...
    # Showing lines 1 to 2
    # 1: 23513900zZz###
    # Or it might just contain the password.
    # Let's handle both.
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    if not lines:
        raise ValueError("Password file is empty")
    
    # If it is just a single line, return it.
    if len(lines) == 1:
        return lines[0]
    
    # If it contains line numbers or metadata, look for the password.
    for line in lines:
        if ":" in line and not line.startswith("http") and not line.startswith("Created") and not line.startswith("Completed") and not line.startswith("File"):
            # Check if it looks like a line: "1: password"
            parts = line.split(":", 1)
            if parts[0].strip().isdigit():
                return parts[1].strip()
    
    # Otherwise, return the last line.
    return lines[-1]

def get_remote_env():
    cmd = ["ssh", "fantastic4-vps", "cat /opt/icoatlas-admin/.env"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to read remote .env: {res.stderr}")
    return res.stdout

def write_remote_env(content):
    # Pass content via stdin to avoid exposing it in the command line
    cmd = ["ssh", "fantastic4-vps", "cat > /opt/icoatlas-admin/.env"]
    res = subprocess.run(cmd, input=content, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to write remote .env: {res.stderr}")

print("Starting secure SMTP password rotation...")

# 1. Read the password from local file
password = read_new_password()
print(f"Successfully read password from pass.md (length: {len(password)})")

# 2. Read remote env
env_content = get_remote_env()
print("Successfully read remote .env file")

# 3. Filter out any existing SMTP_PASSWORD lines
lines = env_content.splitlines()
cleaned_lines = []
for line in lines:
    if not line.strip().startswith("SMTP_PASSWORD="):
        cleaned_lines.append(line)

# 4. Append the new SMTP_PASSWORD
cleaned_lines.append(f"SMTP_PASSWORD={password}")
new_env_content = "\n".join(cleaned_lines) + "\n"

# 5. Write back to VPS
write_remote_env(new_env_content)
print("Successfully updated remote .env file with no duplicates and no history trace.")

# 6. Recreate only the WordPress container
print("Recreating WordPress container...")
recreate_cmd = ["ssh", "fantastic4-vps", "docker compose -f /opt/icoatlas-admin/docker-compose.yml up -d --force-recreate wordpress"]
res = subprocess.run(recreate_cmd, capture_output=True, text=True)
print(f"Container recreation output: {res.stdout.strip()}")
if res.returncode != 0:
    print(f"Error: {res.stderr}")

# 7. Run wp_mail test
print("Running wp_mail smoke test...")
test_code = "require_once 'wp-load.php'; $to = 'support@icoatlas.sk'; $subject = 'ICO Atlas SMTP Test - Rotated'; $body = 'SMTP test from admin.icoatlas.sk passed after password rotation.'; $result = wp_mail($to, $subject, $body); var_dump($result);"
test_cmd = [
    "ssh", "fantastic4-vps",
    f"docker exec icoatlas-admin-wordpress php -r \"{test_code}\""
]
res = subprocess.run(test_cmd, capture_output=True, text=True)
print(f"wp_mail test output: {res.stdout.strip()}")
if "bool(true)" in res.stdout:
    print("SMTP ROTATION SUCCESSFUL: wp_mail returned true.")
else:
    print("SMTP ROTATION FAILED: wp_mail did not return true.")
