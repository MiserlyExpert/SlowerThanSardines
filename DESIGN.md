# Slower Than Sardines — Game Design

> *A roguelike naval tactics game about fish, freedom and taxes.*

## Pitch

FTL at sea, side-on, in chunky pixel art. You are the **Free Fishers**, rebels against the Crown's
Sardine Tax. Your crew has stolen the blueprints of **HMS Insufferable**, the Royal Armada's
flagship. Its weakness: the powder magazine sits directly under the Admiral's tea room. Cross five
seas, survive pirates everywhere, outrun the **Royal Armada** (pompous, very British, brass band
included), and sink the Insufferable.

Tone: dry, silly, affectionate. Every event is a small joke; every crew member has opinions.

## Factions

| Faction | Role |
|---|---|
| **Free Fishers** (you) | Rebels. Green flag with a silver sardine. |
| **The Royal Armada** | The pursuing fleet (FTL's rebel fleet). Revenue cutters, frigates, marines in red coats, Admiral Lord Percival Crumpet-Smythe. |
| **Pirates** | Everywhere, hostile to everyone. Sloops, cutters, brigantines, galleons, privateers. |
| **Ghosts** | Haunt the fog. |

## Core loop

1. **Shipyard.** Pick an unlocked ship and choose its starting crew.
2. **Sea chart.** ~20 waypoints per sea. Each leg costs **1 Rum**. With no rum you sail sober, and the crew takes withdrawal damage.
3. **Something happens.** An event, a port market, a pirate attack, or the Armada catching up.
4. **Battle.** Real time with pause.
5. **Loot**, then **upgrade** at the Shipwright.
6. Reach the edge of each sea before the Armada swallows the chart. In the fifth sea, fight HMS Insufferable.

## Ships (side view)

Rows: **0** crow's nest (up the mast), **1** open top deck (helm, sails, forecastle), **2+** below
decks. Rooms on the same deck connect through doorways; decks connect by **ladders**, **stairs**
and **rigging** (rope ladder to the crow's nest). Systems are rooms. Flavour rooms (quarters, galley,
mess hall, hold, powder magazine, brig, bar, beer cellar, crypt) add character, and the powder
magazine can explode.

| Ship | Unlock | Identity |
|---|---|---|
| The Plucky Sardine | start | Balanced rebel sloop |
| The Rusty Cutlass | win 8 battles | Pirates: no sick bay, brawlers, fire cannon |
| HMS Turncoat | reach sea 3 | Royal deserters: thick bulwarks, marines |
| The Floating Tavern | 3 drunks at once | Three drunks, a cook, 25 rum, a Pepperbox |
| The Rum Runner | win 20 battles | Tiny, evasive, quick guns |
| The Damp Mary | defeat a Ghost Ship | Ghost crew, Hullbreaker |

## Systems

| System | Effect |
|---|---|
| Helm | Must be manned for evasion/escape. Captains are best. |
| Sails | +5% evasion per bar; speeds escape. Sails visibly unfurl when powered. |
| Gun Deck | Powers cannons; manning speeds reloads (drunks best). |
| Bulwarks | Every 2 bars = one oak plate that blocks a shot. |
| Sick Bay | Heals crew inside. |
| Crow's Nest | L1 see inside enemy ships; L2 see their reloads; L3 +10% accuracy. |

## Hazards

- **Leaks.** Rooms below the waterline flood at 11%/s, rooms above it at 4%/s. Water flows through
  doorways, pours down hatches, drowns crew above 65%, knocks a bar off a flooded system, and slows
  the ship. Patched leaks are pumped out slowly.
- **Fire.** Spreads, burns systems and crew, and is put out by flooding. A burning powder magazine explodes (-4 hull).

## Boarding

**Grappling Hooks** (port, 60g): select crew standing on your top deck and press Board (20s
cooldown). They land on the enemy's top deck and fight downward. **Recall** brings back crew who are
standing on the enemy's top deck. **Boarding Axes** (45g): +50% melee damage. Killing every enemy
crew member captures the ship for +50% loot. Enemies board you the same way, onto your top deck.

## Cannons and tags

MULTI (3+ shots), FAST (≤7s reload), FIRE, HULL (heavy hull damage), LOB (ignores bulwarks, uses
ammo), CREW (grapeshot), RIGGING (extra system damage), BASIC.

Long Nine, Quick Nine, Bow Chaser, Twin Nines, Swivel Battery, Pepperbox Battery, Carronade,
Hullbreaker, Royal 32-Pounder, Chain Shot, Grapeshot, Heated Shot, Brimstone Cannon, Bomb Mortar,
Rum Firebomb.

## Code layout

```
sardines/
  config.py     constants (640x360 logical, 16x24 px ship tiles)
  font.py       hand-made proportional pixel font
  gfx.py        palette, text, panels, buttons, sprites, sea, fog, portraits
  audio.py      synthesized sfx + chiptune
  data.py       crew, weapons, systems, side-view layouts, enemies, seas, player ships
  model.py      Room / System / Weapon / Crew / Ship: pathing over doors, ladders, stairs; water & fire
  battle.py     combat simulation (headless-testable), AI, boarding
  render.py     side-view ship renderer and crew animation
  sector.py     sea chart generation
  events.py     event text & choices
  state.py      run state, outcomes, loot
  profile.py    unlocks & lifetime stats
  scenes/       title, shipyard, map, event, combat, store, shipwright, endings
```
