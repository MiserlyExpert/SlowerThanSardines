"""Global constants."""

TITLE = "Slower Than Sardines"
VERSION = "0.1.1"

# Logical resolution. The window is integer-scaled up from this, so every
# pixel stays a crisp, chunky pixel.
W, H = 640, 360
FPS = 60

# Side-view ship grid: one tile is TW pixels wide, one deck (row) is RH pixels tall.
TW = 16
RH = 24
T = TW
TOP_ROW = 1        # row 0 is the crow's nest, row 1 the open top deck, rows 2+ are below decks

MAX_CREW = 8
MAX_WEAPONS = 4
