import os
import subprocess
import sys
import click
from tqdm import tqdm

def install_package(package):
    """Install a package using pip."""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package}. Please install it manually.")
        sys.exit(1)
    except FileNotFoundError:
        print("pip not found. Please install pip manually.")
        sys.exit(1)

def check_and_install_package(package):
    """Check if a package is installed; if not, install it."""
    try:
        __import__(package)
    except ImportError:
        print(f"{package} not found. Installing...")
        install_package(package)

# Check for tqdm
check_and_install_package('tqdm')

from tqdm import tqdm

def find_extensions(directory):
    """Find all unique file extensions in a directory."""
    extensions = set()
    for root, _, files in os.walk(directory):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext:
                extensions.add(ext.lower())
    return extensions

def is_binary(file_path):
    """Check if the file is binary based on MIME type."""
    try:
        result = subprocess.run(['file', '--mime-type', '-b', file_path],
                                capture_output=True, text=True)
        mime_type = result.stdout.strip()
        # If MIME type starts with 'text/', classify as text; otherwise, binary
        return not mime_type.startswith('text/')
    except Exception as e:
        print(f"Error checking file {file_path}: {e}")
        return True

def process_extensions(directory, extensions, git_attributes_file):
    """Process each extension to determine if it's binary and update .gitattributes."""
    report = {'text': [], 'binary': [], 'no_files': []}
    
    with open(git_attributes_file, 'a') as attr_file:
        for ext in tqdm(extensions, desc="Processing extensions", unit="ext", ncols=100, ascii=True, dynamic_ncols=True):
            ext = ext.lstrip('.')
            found_file = None
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith(ext):
                        found_file = os.path.join(root, file)
                        break
                if found_file:
                    break

            if found_file:
                if is_binary(found_file):
                    entry = f"*{ext} filter=lfs diff=lfs merge=lfs -text\n"
                    with open(git_attributes_file, 'r') as attr_file_check:
                        if entry not in attr_file_check.read():
                            attr_file.write(entry)
                            print(f"Added *{ext} to {git_attributes_file} for LFS.")
                    report['binary'].append(ext)
                else:
                    report['text'].append(ext)
            else:
                report['no_files'].append(ext)

    return report

@click.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
def main(directory):
    """Find and process file extensions in DIRECTORY to update .gitattributes for LFS and generate a report."""
    print("Finding unique extensions...")
    extensions = find_extensions(directory)
    
    if not extensions:
        print("No extensions found.")
        return

    git_attributes_file = '.gitattributes'
    
    report = process_extensions(directory, extensions, git_attributes_file)
    
    print("\nReport:")
    print("\nBinary extensions:")
    for ext in report['binary']:
        print(f".{ext}")

    print("\nText extensions:")
    for ext in report['text']:
        print(f".{ext}")

    print("\nExtensions with no files found:")
    for ext in report['no_files']:
        print(f".{ext}")

if __name__ == "__main__":
    main()
