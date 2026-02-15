import os
import glob

venv = os.environ.get('VIRTUAL_ENV') or os.environ.get('CONDA_PREFIX')
if venv:
    pattern = f"{venv}/lib/python*/site-packages/matplotlib-backend-kitty/__init__.py"
    files = glob.glob(pattern)
    
    for f in files:
        try:
            with open(f, 'r') as file:
                content = file.read()
            
            # Apply fixes
            content = content.replace(", facecolor='#888888'", "")
            content = content.replace("'--align', 'left'", "'--align', 'center'")
            
            with open(f, 'w') as file:
                file.write(content)
            
            print("✓ matplotlib-backend-kitty auto-patched")
            break
        except:
            pass
