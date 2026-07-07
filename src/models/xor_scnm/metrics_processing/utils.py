# utils.py

from pathlib import Path

def get_latest_acquisition(base_output_dir, specific=None):
    output_path = Path(base_output_dir)
    
    if specific:
        target = output_path / specific
        if not target.exists():
            raise FileNotFoundError(f"Specified acquisition not found: {specific}")
        return target
    
    acquisition_folders = [
        f for f in output_path.iterdir()
        if f.is_dir() and f.name.endswith('-acquisition')
    ]
    
    if not acquisition_folders:
        raise FileNotFoundError(f"No acquisition folders found in {base_output_dir}")
    
    latest = sorted(acquisition_folders, key=lambda f: f.name)[-1]
    print(f"Using acquisition folder: {latest.name}")
    return latest