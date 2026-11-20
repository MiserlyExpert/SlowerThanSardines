# Slower Than Sardines

*A roguelike naval tactics game about fish, freedom and taxes.*

By Royal Decree, every fish in the sea is Property of His Majesty. Sardines need a licence. Small
sardines need a smaller, more expensive licence. You are the **Free Fishers**: fishermen turned
freedom fighters. Your crew has stolen the plans to **HMS Insufferable**, the Crown's gigantic
flagship and floating tax office. Sail five seas, survive the pirates who infest every one of them,
stay ahead of the pompous **Royal Armada** chasing you (with a brass band), and sink the Insufferable.

It plays like FTL: real-time-with-pause battles, managing power, sending crew around the ship, and
aiming cannons at enemy rooms. Ships are shown **side-on as cutaways**, with decks, ladders and stairs.

![Combat](docs/combat_brig.png)
![Shipyard](docs/hangar_sardine.png)

## Download & play

Grab the latest build from the **[Releases page](https://github.com/MiserlyExpert/SlowerThanSardines/releases/latest)**:

- **Windows:** download `SlowerThanSardines-Windows.exe` and double-click it. No install, no Python.
  Windows may show "Windows protected your PC" because the game isn't code-signed; click
  **More info → Run anyway**.
- **macOS:** download the macOS zip, unzip, then right-click the app and choose **Open**.
- **Linux:** download the tarball, extract, and run `./SlowerThanSardines`.

## Features

- **Side-view cutaway ships.** Crow's nest, open top deck, gun deck, captain's quarters, galley,
  mess hall, sick bay, carpenter's shop, cargo hold and powder magazine. Crew walk the decks, climb
  ladders, take the stairs, and go up the rigging to the crow's nest, with animations for each.
- **Broadside battles.** Your ship in the foreground, the enemy alongside in the background, with
  cannonballs arcing between them. Cannons fire with muzzle flash, recoil and smoke. A sunk enemy
  **cracks in half** and slides under the waves.
- **Flooding.** Leaks below the waterline flood fast. Water pours down hatches into the lower decks,
  drowns crew, shorts out systems, and makes the ship sit lower and handle worse. Crew patch leaks.
- **Fire.** Fire spreads room to room. If the powder magazine burns for too long, it explodes.
- **Fog of war.** You can't see inside an enemy ship unless your Crow's Nest (telescope) is working,
  or your boarders are aboard it.
- **Boarding.** Buy Grappling Hooks in port, then swing crew from your top deck onto the enemy's and
  fight your way down through the decks.
- **Six unlockable ships**, each with its own layout and crew: The Plucky Sardine (rebels),
  The Rusty Cutlass (pirates), HMS Turncoat (Royal deserters), The Floating Tavern (three drunks and
  a cook), The Rum Runner (smugglers) and The Damp Mary (ghosts). Pick your starting crew.
- **A crew with opinions.** Captains are the best at the helm. The **Drunkard is the best gunner and
  the best brawler**, and walks like the deck is always moving. Many classes unlock special event options.
- **15 cannons**, tagged by what they're good at: MULTI-shot, FAST reload, FIRE, HULL damage,
  LOB (ignores bulwarks), CREW damage and RIGGING damage.
- **Fog banks** take two days to cross, so the Armada gains twice as fast.
- **About 35 hand-written events**, a custom pixel font, all art drawn in code, and synthesized audio
  (including a chiptune *Drunken Sailor*).

## Running from source

**Windows, easiest:** install Python from https://www.python.org/downloads/ (tick **"Add python.exe
to PATH"**), then double-click **`Play.bat`** in this folder. The first run takes about a minute to
set things up; after that it starts straight away.

**Any OS, by hand:** requires Python 3.10+.

```bash
pip install -r requirements.txt
python main.py                 # or: python -m sardines
python main.py --unlock-all    # try every ship without earning it
```

Unlocks and lifetime stats are saved to `~/.slower_than_sardines/profile.json`.

## Controls

| Action | Input |
|---|---|
| Pause / resume | **Space** |
| Select cannon, then aim | **1–4** or click a cannon card, then click an enemy room |
| Power / unpower a cannon | Click card / right-click card |
| Add / remove system power | Left / right-click a system column |
| Select crew | Click crew (Shift to add, **A** for all) |
| Move crew | Right-click a room |
| Board (needs Grappling Hooks) | Select crew on your top deck, press **B** |
| Make Sail (escape) | Button, once the escape bar is full (needs a manned helm) |
| Shipwright (upgrades) | **S** on the sea chart |
| Fullscreen / music | **F11** / **M** |

## Building a standalone app

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name SlowerThanSardines --exclude-module pkg_resources main.py
```

The executable ends up in `dist/`. The GitHub Actions workflow in `.github/workflows/build.yml`
builds it for **Windows, macOS and Linux** on every push to `main`, and attaches the builds to a
GitHub Release when you push a tag like `v0.1.0`.

## Tests

```bash
pip install pytest
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m pytest -q
```

The tests simulate battles against every enemy type, test boarding and flooding, generate sea
charts, apply every event outcome, sail a full five-sea run, and render every screen headlessly.

See [DESIGN.md](DESIGN.md) for the full design and code map.
