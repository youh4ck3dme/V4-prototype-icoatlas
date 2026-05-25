import os
import re

def fix_mobile_h_screen(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.jsx'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()

                # Surgical replacements for mobile-safe heights
                new_content = re.sub(r'\bmin-h-screen\b', 'min-h-[100dvh]', content)
                new_content = re.sub(r'\bh-screen\b', 'h-[100dvh]', new_content)

                if new_content != content:
                    with open(filepath, 'w') as f:
                        f.write(new_content)
                    print(f"Fixed heights in: {filepath}")

if __name__ == '__main__':
    fix_mobile_h_screen('/Users/erikbabcan/Documents/Dokumenty – Mac mini užívateľa youh4ck3dme - 1/V4/V4-prototype-icoatlas/frontend/src')
