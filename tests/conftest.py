import sys
from pathlib import Path

# Let tests import harness/stacks/known_bugs as plain modules.
sys.path.insert(0, str(Path(__file__).parent))

# Fixture repos carry their own tests; they run inside the fixture, not here.
collect_ignore_glob = ["fixtures/*"]
