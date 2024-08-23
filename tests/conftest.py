import os
import sys

# Get the current directory (tests/)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory (project root)
parent_dir = os.path.dirname(current_dir)

# Add the parent directory to sys.path
sys.path.insert(0, parent_dir)

# Add the 'src' directory to sys.path
src_dir = os.path.join(parent_dir, "sqlmodel_controller")
sys.path.insert(0, src_dir)
