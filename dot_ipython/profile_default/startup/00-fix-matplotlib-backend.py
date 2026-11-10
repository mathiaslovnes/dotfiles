import os
import glob

venv = os.environ.get('VIRTUAL_ENV') or os.environ.get('CONDA_PREFIX')
if venv:
    pattern = f"{venv}/lib/python*/site-packages/matplotlib-backend-kitty/__init__.py"
    files = glob.glob(pattern)
    
    for f in files:
        try:
            with open(f, 'r') as file:
                original = file.read()

            # Apply fixes: no gray background, centered plots
            content = original.replace(", facecolor='#888888'", "")
            content = content.replace("'--align', 'left'", "'--align', 'center'")

            # Write and report only when something changed
            if content != original:
                with open(f, 'w') as file:
                    file.write(content)
                print("✓ matplotlib-backend-kitty auto-patched")
        except OSError as e:
            print(f"matplotlib-backend-kitty patch failed: {e}")
        break
