# Slower Than Sardines — Game Design

> *A roguelike naval tactics game about delivering a very important napkin.*

## Pitch

An FTL-style real-time-with-pause roguelike set on the high seas, in chunky pixel art.
You captain the **HMS Questionable Decisions**, a royal courier sloop. A drunk Royal spy
scribbled the location of the pirates' secret base on a bar napkin. Your crew
(mostly your drunk) found it. Get the **Napkin of Destiny** to the **Royal Armada** in
Royal Waters before the **Black Tide** pirate fleet runs you down.

Tone: dry, silly, affectionate. Every event is a small joke; every crew member has opinions.

## Core loop (mirrors FTL)

1. **Sea chart.** Each sea (sector) is a map of ~20 waypoints. Sail to a connected waypoint.
   Every leg costs **1 Rum** (the crew won't sail sober).
2. **Something happens.** A text event with choices, a port tavern (shop), or a pirate attack.
3. **Battle.** Real-time with pause. Power systems, aim cannons at enemy rooms, move crew to
   man stations, put out fires, patch leaks, repel boarders.
4. **Loot.** Doubloons, rum, cannonballs, new cannons, new crew.
5. **Upgrade** at the Shipwright between legs.
6. Reach the sea's exit before the **Black Tide** (the pursuing fleet) catches you.
   5 seas total. In the last, the Armada waits — and so does the pirate flagship.

## Resources

| FTL | Here | Notes |
|---|---|---|
| Fuel | **Rum** | 1 per leg. At 0 you can "sail sober": every crew member takes withdrawal damage. |
| Scrap | **Doubloons** | Currency for shops and upgrades. |
| Missiles | **Cannonballs** | Ammo for the Bomb Mortar and Rum Firebomb. |
| Reactor | **Gusto** | Bars of crew effort you assign to powered systems. |
| Federation | **Royal Armada** | Your destination. |
| Rebel fleet | **The Black Tide** | Advances every day. Waypoints it swallows hold elite pirate warships. |

## Fog

Fog banks drift across every chart, thickest in **The Murk**.
- Sailing into or out of fog takes **two days**, so the Black Tide gains twice as fast.
- Battles in fog: every ship's **evasion is halved**, and **making sail (escape) charges at half speed**.
- Fog has its own events (voices in the rum barrel, things beneath the hull).

## Ship systems

| System | Powered? | Effect |
|---|---|---|
| **Helm** | subsystem | Must be manned for any evasion or escape. Captains give a huge bonus. |
| **Sails** | yes | +5% evasion per bar; speeds escape. |
| **Gun Deck** | yes | Each cannon needs bars. Manning speeds reloads (drunks best). |
| **Bulwarks** | yes | Every 2 bars = 1 layer of oak plating that blocks 1 shot, then regrows. |
| **Sick Bay** | yes | Heals crew inside. |
| **Crow's Nest** | subsystem | L1 see enemy crew, L2 see enemy reload bars, L3 +10% accuracy. |

Damage: hits damage the hull **and** the system in the struck room (bars go red; power is lost).
Crew standing in a room repair it.

### Hazards
- **Fire** spreads between rooms, burns systems and crew. Crew beat it out.
- **Leaks** (hull breaches) flood the room. Water spreads to neighbouring rooms, drowns crew
  in deep water, **puts out fires**, and makes the ship sluggish (evasion penalty). Crew patch leaks.

## Crew

| Class | Speciality |
|---|---|
| **Captain** | Best at the Helm by a mile. Unlocks *[Captain]* event options. |
| **Drunkard** | **Best gunner and best brawler on the ship.** Wobbly, slow walker, bad repairer. *[Drunkard]* options. |
| Deckhand | Good on Sails. Reliable. |
| Powder Monkey | Fastest walker, good reloader, fragile. |
| Carpenter | Repairs at 2.2× speed. |
| Surgeon | Heals crew in the same room. |
| Cook | Heals the whole crew after every leg. Tough. |

Crew bark one-liners during battle. Enemies: Pirates, Pirate Brutes, Ghosts, the Dread Captain.

## Cannons

Long Nine, Twin Nines, Carronade, Chain Shot (system damage), Grapeshot (crew damage),
Heated Shot (fire), Swivel Battery (3 shots), Bomb Mortar (ignores bulwarks, uses ammo),
Rum Firebomb (ignores bulwarks, starts fires), Royal 32-Pounder (rare).

## Enemies

Pirate Sloop, Smuggler Cutter (evasive), Pirate Brigantine, Rogue Privateer, Ghost Ship,
Pirate Galleon, Black Tide Man-o-War (elite), and the boss: **The Leviathan's Grin**,
which gets angrier (faster reloads) at half hull. Pirates with grappling hooks **board** you.

Win by sinking the hull (standard loot) or killing every crew member (+50% loot, chance of
a prisoner joining). Enemies may try to flee when beaten up.

## The five seas

1. **The Shallows** — amateur pirates, many crabs.
2. **Smuggler's Reach** — every crate says NOT RUM.
3. **The Murk** — fog so thick you could spread it on toast. Ghost ships.
4. **Kraken Deeps** — galleons and large locals.
5. **Royal Waters** — the Armada rendezvous and the final battle.

## Controls

- **Space** pause. **1–4** select cannon, then click an enemy room to target (auto-fires when loaded).
- Left-click crew to select (Shift = add), **right-click** a room to send them there.
- Systems bar: left-click add power, right-click remove. Cannon card: right-click to unpower.
- **F11** fullscreen, **M** music.

## Tech

- Python 3.10+, pygame 2. Native desktop window (640×360 logical, integer-scaled).
- All art is pixel art defined in code (string sprite maps) — no asset files.
- All sound is synthesized at startup (including a chiptune *Drunken Sailor*).
- GitHub Actions builds standalone executables for Windows, macOS and Linux with PyInstaller.

## Code layout

```
sardines/
  config.py     constants
  gfx.py        palette, text, panels, buttons, sprite maps, sea/fog drawing
  audio.py      synthesized sfx + music
  data.py       crew classes, weapons, systems, layouts, enemies, seas
  model.py      Room / System / Weapon / Crew / Ship
  battle.py     real-time combat simulation (no rendering; testable headless)
  sector.py     sea chart generation
  events.py     event text & choices
  state.py      run state, outcomes, loot
  render.py     ship & crew drawing
  scenes/       title, map, event, combat, store, shipwright, endings
  app.py        main loop & scene stack
```
