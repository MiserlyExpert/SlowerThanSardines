"""Static game data: crew classes, weapons, systems, ship layouts, enemies and seas."""

# ---------------------------------------------------------------------------
# Crew
# ---------------------------------------------------------------------------
# helm / sails: evasion % added when manning that station
# guns / shields: reload / regrow speed multiplier when manning
# repair: repair speed multiplier, fight: damage per second in melee
# speed: walking speed in tiles per second
CREW = {
    'captain': dict(title='Captain', hp=100, speed=2.0, helm=15, sails=4, guns=1.10, shields=1.15,
                    repair=1.0, fight=8,
                    desc="Steers like a dream. Unlocks [Captain] options. Ego sold separately."),
    'drunk': dict(title='Drunkard', hp=110, speed=1.4, helm=2, sails=3, guns=1.60, shields=1.0,
                  repair=0.6, fight=16,
                  desc="Best gunner and best brawler aboard. Walks like the deck is moving. (It is.)"),
    'deckhand': dict(title='Deckhand', hp=100, speed=2.0, helm=5, sails=8, guns=1.15, shields=1.15,
                     repair=1.0, fight=7,
                     desc="Good with sails. Knows forty knots, can tie three of them."),
    'monkey': dict(title='Powder Monkey', hp=70, speed=3.0, helm=3, sails=5, guns=1.35, shields=1.1,
                   repair=0.9, fight=5,
                   desc="Small, fast, reloads quick. Suspiciously fond of gunpowder."),
    'carpenter': dict(title='Carpenter', hp=100, speed=1.8, helm=4, sails=4, guns=1.10, shields=1.2,
                      repair=2.2, fight=7,
                      desc="Repairs over twice as fast. Has strong opinions about your joinery."),
    'surgeon': dict(title='Surgeon', hp=90, speed=2.0, helm=4, sails=4, guns=1.05, shields=1.1,
                    repair=0.9, fight=5, heal=4,
                    desc="Heals crew in the same room. Washes hands occasionally."),
    'cook': dict(title='Cook', hp=125, speed=1.7, helm=3, sails=4, guns=1.10, shields=1.1,
                 repair=1.0, fight=9,
                 desc="Hearty stew heals everyone after each leg. Do not ask what's in it."),
    # --- enemies (and the occasional reformed defector) ---
    'pirate': dict(title='Pirate', hp=100, speed=1.9, helm=5, sails=5, guns=1.15, shields=1.1,
                   repair=0.9, fight=8, desc="Arr. That's the whole resume."),
    'brute': dict(title='Pirate Brute', hp=150, speed=1.6, helm=2, sails=4, guns=1.1, shields=1.0,
                  repair=0.8, fight=12, desc="Large. Angry. Possibly a wardrobe with a beard."),
    'ghost': dict(title='Ghost', hp=85, speed=2.2, helm=6, sails=6, guns=1.2, shields=1.1,
                  repair=1.0, fight=9, desc="Deceased, but still clocking in."),
    'marine': dict(title='Royal Marine', hp=100, speed=1.9, helm=6, sails=5, guns=1.2, shields=1.2,
                   repair=1.0, fight=9, desc="Red coat, tall hat, impeccable manners, terrible aim."),
    'admiral': dict(title='Admiral', hp=220, speed=1.6, helm=16, sails=5, guns=1.3, shields=1.2,
                    repair=0.8, fight=14,
                    desc="Admiral Lord Percival Crumpet-Smythe. Has never lost a battle, or a teacup."),
}

# Hands each crew member brings to the ship's work (what other games call 'power').
HANDS = dict(captain=3, drunk=2, deckhand=3, monkey=2, carpenter=3, surgeon=2, cook=3,
             pirate=3, brute=4, ghost=3, marine=3, admiral=4, merchant=2)

HIREABLE = ['deckhand', 'deckhand', 'monkey', 'carpenter', 'surgeon', 'cook', 'drunk', 'drunk', 'captain']

NAMES = {
    'captain': ["Capt. Hornbuckle", "Capt. Mabel Stern", "Capt. Fitzwilliam", "Capt. Pemberton",
                "Capt. Ada Gale", "Capt. Thaddeus Hook-Free"],
    'drunk': ["Sloshy Pete", "Barrel Bob", "Tipsy Tess", "Hiccup Hal", "Rummy Ruth",
              "Three-Bottle Bill", "Wobbly Walt", "Grog-Eyed Gus"],
    'generic': ["Barnaby", "One-Sock Sally", "Gilly", "Old Tom", "Mad Meg", "Salty Sue", "Ned",
                "Davey", "Bess", "Finnegan", "Nell", "Tobias", "Marigold", "Flint", "Rosie",
                "Jebediah", "Cuthbert", "Peg", "Lefty", "Ahab Jr.", "Bilbo Baggywrinkle",
                "Horace", "Wendell", "Agnes", "Percival", "Clem", "Dottie", "Ignatius"],
    'pirate': ["Scurvy Dan", "Gutbucket", "Mouldy Mo", "Rancid Ron", "Bilgewater Bess",
               "Two-Teeth Terry", "Stinky Pete", "Gary"],
    'ghost': ["Moaning Mel", "Whispering Wil", "Translucent Tim", "Ectoplasm Ed"],
    'marine': ["Pvt. Pemberton", "Cpl. Fotheringham", "Sgt. Bottomley", "Pvt. Smythe-Smythe",
               "Lt. Crumpet", "Pvt. Higginbotham", "Cpl. Waddington", "Pvt. Pinkerton"],
    'admiral': ["Adm. Crumpet-Smythe"],
}

BARKS = {
    'drunk': ["*hic*", "I see two of 'em. I'll shoot both.", "Is the ship moving or is it me?",
              "This cannon's my best friend.", "Fire in the hole! ...whose hole?",
              "I'm not drunk, I'm nautically flexible.", "Who moved the sea?", "Hold my rum."],
    'captain': ["Steady as she goes!", "Freedom! And also fish!", "I've had worse days. Not many.", "Somebody write this down.",
                "Hold fast, you magnificent idiots!", "Down with the Sardine Tax!", "Nobody panic. Except quietly."],
    'deckhand': ["Aye aye!", "Do I get hazard pay?", "Swabbing can wait, right?", "I joined for the free hat."],
    'monkey': ["More powder! MORE!", "I'm small but I'm loud!", "Can I light the next one?", "Boom! Ha!"],
    'carpenter': ["That's not load-bearing. Probably.", "Measure twice, patch once!",
                  "Who keeps putting holes in my boat?"],
    'surgeon': ["Hold still, this'll hurt a lot.", "I've seen worse. On you, actually.", "Where's my good saw?"],
    'cook': ["Lunch is cancelled!", "Who wants stew? It's survivable!", "Adding cannonballs to the soup."],
    'pirate': ["Arrr!", "Yo ho ho!", "Har har!", "Yer booty or yer life!",
               "We hate the Crown too, but business is business!"],
    'brute': ["SMASH.", "ARRRRRR.", "Me crush."],
    'ghost': ["Wooooo...", "Join usssss...", "Ye forgot to tip the ferryman..."],
    'marine': ["For King and Crumpet!", "Halt, in the name of the Crown!", "Jolly good shot, old bean!",
               "I say! That was my hat!", "Tally-ho!", "Frightfully sorry about this."],
    'admiral': ["Do you know who I AM?", "Fire! And mind the tea service!", "Insolent sardines!",
                "This is most irregular!", "Somebody fetch my other monocle!"],
}

# ---------------------------------------------------------------------------
# Systems
# ---------------------------------------------------------------------------
SYSTEMS = {
    'sails': dict(title='Sails', max=8, cost=15, short='SAIL',
                  desc="Each bar adds 5% evasion and speeds your escape."),
    'guns': dict(title='Gun Deck', max=8, cost=20, short='GUNS',
                 desc="Gun crews: each cannon needs Hands to load it. Man it to load faster. Drunks load fastest."),
    'bulwark': dict(title='Bulwarks', max=8, cost=25, short='BULW',
                    desc="Every 2 Hands brace one oak plate that blocks one cannon shot."),
    'sickbay': dict(title='Sick Bay', max=3, cost=20, short='SICK',
                    desc="Heals crew inside. Smells of vinegar and regret."),
    'helm': dict(title='Helm', max=3, cost=25, short='HELM', sub=True,
                 desc="Must be manned for any evasion or escape. Each level +3% evasion."),
    'nest': dict(title="Crow's Nest", max=3, cost=20, short='NEST', sub=True,
                 desc="Lv1 see enemy crew. Lv2 see enemy reloads. Lv3 +10% accuracy."),
}
SYS_ORDER = ['sails', 'guns', 'bulwark', 'sickbay', 'helm', 'nest']
MANNABLE = ('helm', 'sails', 'guns', 'bulwark')

# ---------------------------------------------------------------------------
# Weapons
# ---------------------------------------------------------------------------
WEAPONS = {
    'long_nine': dict(name='Long Nine', power=1, charge=8.0, shots=1, dmg=1, cost=35,
                      desc="A trusty nine-pounder. Not exciting. Neither is bread."),
    'twin_nines': dict(name='Twin Nines', power=2, charge=10.0, shots=2, dmg=1, cost=60,
                       desc="Two nine-pounders lashed together with enthusiasm."),
    'carronade': dict(name='Carronade', power=2, charge=14.0, shots=1, dmg=3, cost=75,
                      desc="Short, stubby, devastating. The crew calls it Gerald."),
    'chain_shot': dict(name='Chain Shot', power=1, charge=10.0, shots=1, dmg=1, sys=2, cost=55,
                       desc="Two balls on a chain. Shreds rigging: +2 system damage."),
    'grapeshot': dict(name='Grapeshot', power=1, charge=9.0, shots=3, dmg=0, crew=22, cost=50,
                      desc="A bucket of nails fired angrily. Hurts crew, not hulls."),
    'hot_shot': dict(name='Heated Shot', power=2, charge=12.0, shots=1, dmg=1, fire=0.55, cost=65,
                     desc="Cannonballs baked in the galley oven. Starts fires. Cook furious."),
    'swivel': dict(name='Swivel Battery', power=3, charge=12.0, shots=3, dmg=1, cost=90,
                   desc="Three swivel guns. Great for stripping bulwarks."),
    'mortar': dict(name='Bomb Mortar', power=1, charge=11.0, shots=1, dmg=2, pierce=True, ammo=True,
                   breach=0.5, cost=55, desc="Lobs a bomb over bulwarks. Uses a cannonball. Makes leaks."),
    'firebomb': dict(name='Rum Firebomb', power=1, charge=12.0, shots=1, dmg=0, pierce=True, ammo=True,
                     fire=0.95, cost=50, desc="A tragic waste of rum. Ignores bulwarks, sets rooms ablaze."),
    'royal_32': dict(name='Royal 32-Pounder', power=3, charge=16.0, shots=2, dmg=2, cost=125,
                     desc="Liberated from the Royal Armada. They would like it back. Tough."),
    'quick_nine': dict(name='Quick Nine', power=1, charge=5.5, shots=1, dmg=1, cost=45,
                       desc="A light gun with a heroically fast loader. Fires far more often than is wise."),
    'bow_chaser': dict(name='Bow Chaser', power=1, charge=6.5, shots=1, dmg=1, sys=1, cost=50,
                       desc="A long, quick gun for chasing things down. Aims for the rigging."),
    'pepperbox': dict(name='Pepperbox Battery', power=3, charge=15.0, shots=5, dmg=1, cost=105,
                      desc="Five barrels, one fuse, zero safety inspections."),
    'brimstone': dict(name='Brimstone Cannon', power=2, charge=12.0, shots=1, dmg=1, fire=0.85, cost=75,
                      desc="Fires sulphur-packed shot. Smells awful. Burns everything."),
    'hullbreaker': dict(name='Hullbreaker', power=2, charge=15.0, shots=1, dmg=2, hull=2, breach=0.7,
                        cost=90, desc="A huge iron ball built to go in one side and out the other."),
}
LOOT_WEAPONS = ['long_nine', 'long_nine', 'twin_nines', 'carronade', 'chain_shot', 'grapeshot',
                'hot_shot', 'swivel', 'mortar', 'firebomb', 'royal_32', 'quick_nine', 'bow_chaser',
                'pepperbox', 'brimstone', 'hullbreaker']


def weapon_tags(d):
    """Short labels describing what a cannon is good at."""
    tags = []
    if d['shots'] >= 3:
        tags.append('MULTI')
    if d['charge'] <= 7:
        tags.append('FAST')
    if d.get('fire', 0) >= 0.5:
        tags.append('FIRE')
    if d.get('hull') or d['dmg'] >= 3:
        tags.append('HULL')
    if d.get('pierce'):
        tags.append('LOB')
    if d.get('crew'):
        tags.append('CREW')
    if d.get('sys'):
        tags.append('RIGGING')
    if d.get('ammo'):
        tags.append('AMMO')
    if not tags:
        tags.append('BASIC')
    return tags


TAG_COLORS = dict(MULTI='#3a7bd5', FAST='#5fbf4f', FIRE='#f08a2c', HULL='#d9453b', LOB='#7a4ea3',
                  CREW='#e8b33a', RIGGING='#3fb8af', AMMO='#a9a6b3', BASIC='#a8743f')

# ---------------------------------------------------------------------------
# Ship layouts (side view). Rooms: (kind, gx, row, width). Row 0 = crow's nest, row 1 = open top deck,
# rows 2+ = below decks. kind is a system name or a flavour room. Links join a room to the one below it:
# ('ladder' | 'rigging', column, upper_row) or ('stairs', column, upper_row) which runs from column (top)
# to column + 1 (bottom). Masts are tile columns.
# ---------------------------------------------------------------------------
# Modules: rooms with a mechanic, installed into EMPTY slots (or upgraded) in port.
MODULES = {
    'galley': dict(title='Galley', max=3, cost=40,
                   desc="Hot food. +1 Hand per level, and the crew heals 10 HP per level after every leg. "
                        "A Cook doubles the healing."),
    'hold': dict(title='Cargo Hold', max=3, cost=30,
                 desc="Room for trade goods: +6 cargo per level. Buy cheap in one port, sell dear in another."),
    'magazine': dict(title='Powder Magazine', max=3, cost=45,
                     desc="Lobbed cannons (mortar, firebomb) load 20% faster per level, and you salvage "
                          "+1 cannonball per level after each win. Explodes if it burns too long."),
    'armory': dict(title='Armory', max=3, cost=60,
                   desc="Grappling hooks and cutlasses: lets your crew BOARD enemy ships. Each level: +25% "
                        "melee damage and a shorter boarding cooldown."),
    'brig': dict(title='The Brig', max=2, cost=35,
                 desc="Take prisoners: after a win, a 40% chance per level to capture one. Ransom them for "
                      "doubloons or offer them a job."),
    'chartroom': dict(title='Chart Room', max=3, cost=40,
                      desc="Charting an escape course is 20% faster per level, and the Royal Armada gains "
                           "10% less ground per level each leg."),
    'bar': dict(title='The Bar', max=3, cost=40, desc="Brews 1 Rum per level after every leg."),
    'crypt': dict(title='The Crypt', max=2, cost=50,
                  desc="Crew who die in battle have a 30% chance per level to come back as a Ghost."),
}
# Trade goods: buy where they're cheap, sell where they're dear. Needs a Cargo Hold to carry much.
GOODS = {
    'fish': dict(title='Salted Fish', price=8, icon='fish',
                 desc="Technically illegal under the Sardine Tax. Everyone buys it anyway."),
    'spice': dict(title='Spice', price=16, icon='spice', desc="Makes the Admiral's tea interesting."),
    'silk': dict(title='Silk', price=26, icon='silk', desc="Smuggled, smooth, and suspiciously Royal-blue."),
    'tea': dict(title='Contraband Tea', price=34, icon='tea',
                desc="Untaxed tea. The single most dangerous substance known to the Crown."),
}
BASE_CARGO = 2
CARGO_PER_HOLD = 6

EMPTY_DESC = "An empty compartment. Buy a module for it at a port's shipyard."

LAYOUTS = {
    'courier': dict(
        rooms=[('nest', 6, 0, 1), ('helm', 0, 1, 3), ('sails', 3, 1, 6), ('empty', 9, 1, 3),
               ('empty', 0, 2, 3), ('guns', 3, 2, 5), ('galley', 8, 2, 3),
               ('sickbay', 1, 3, 3), ('bulwark', 4, 3, 3), ('hold', 7, 3, 3)],
        links=[('rigging', 6, 0), ('ladder', 1, 1), ('stairs', 4, 1), ('ladder', 10, 1),
               ('ladder', 2, 2), ('ladder', 6, 2), ('stairs', 8, 2)],
        masts=[6, 10, 1]),
    'raider': dict(
        rooms=[('nest', 5, 0, 1), ('helm', 0, 1, 3), ('sails', 3, 1, 6), ('empty', 9, 1, 3),
               ('brig', 0, 2, 2), ('guns', 2, 2, 6), ('armory', 8, 2, 3),
               ('bulwark', 1, 3, 4), ('hold', 5, 3, 5)],
        links=[('rigging', 5, 0), ('ladder', 1, 1), ('stairs', 3, 1), ('ladder', 10, 1),
               ('ladder', 3, 2), ('ladder', 8, 2)],
        masts=[5, 9]),
    'tavern': dict(
        rooms=[('helm', 0, 1, 3), ('sails', 3, 1, 4), ('empty', 7, 1, 5),
               ('sickbay', 0, 2, 3), ('bar', 3, 2, 6), ('guns', 9, 2, 3),
               ('bulwark', 1, 3, 4), ('galley', 5, 3, 5)],
        links=[('ladder', 1, 1), ('stairs', 4, 1), ('ladder', 10, 1), ('ladder', 2, 2), ('ladder', 7, 2)],
        masts=[5]),
    'runner': dict(
        rooms=[('nest', 4, 0, 1), ('helm', 0, 1, 3), ('sails', 3, 1, 4), ('chartroom', 7, 1, 2),
               ('guns', 1, 2, 4), ('bulwark', 5, 2, 3),
               ('sickbay', 2, 3, 3), ('hold', 5, 3, 2)],
        links=[('rigging', 4, 0), ('ladder', 1, 1), ('ladder', 7, 1), ('ladder', 3, 2), ('ladder', 6, 2)],
        masts=[4, 7]),
    'ghostly': dict(
        rooms=[('nest', 4, 0, 1), ('helm', 0, 1, 3), ('sails', 3, 1, 5), ('empty', 8, 1, 3),
               ('crypt', 0, 2, 3), ('guns', 3, 2, 5), ('brig', 8, 2, 2),
               ('bulwark', 1, 3, 4), ('empty', 5, 3, 4)],
        links=[('rigging', 4, 0), ('ladder', 1, 1), ('stairs', 3, 1), ('ladder', 9, 1),
               ('ladder', 2, 2), ('ladder', 6, 2)],
        masts=[4, 9]),
    'small': dict(
        rooms=[('helm', 0, 1, 3), ('sails', 3, 1, 4), ('empty', 7, 1, 2),
               ('guns', 1, 2, 4), ('bulwark', 5, 2, 3), ('empty', 2, 3, 4)],
        links=[('ladder', 1, 1), ('ladder', 7, 1), ('ladder', 3, 2)],
        masts=[4, 7]),
    'medium': dict(
        rooms=[('nest', 5, 0, 1), ('helm', 0, 1, 3), ('sails', 3, 1, 5), ('empty', 8, 1, 3),
               ('empty', 0, 2, 3), ('guns', 3, 2, 5), ('empty', 8, 2, 2),
               ('sickbay', 1, 3, 3), ('bulwark', 4, 3, 3), ('empty', 7, 3, 3)],
        links=[('rigging', 5, 0), ('ladder', 1, 1), ('stairs', 4, 1), ('ladder', 9, 1),
               ('ladder', 2, 2), ('ladder', 6, 2), ('ladder', 8, 2)],
        masts=[5, 9, 1]),
    'large': dict(
        rooms=[('nest', 6, 0, 1), ('helm', 0, 1, 3), ('sails', 3, 1, 6), ('empty', 9, 1, 3),
               ('empty', 0, 2, 3), ('guns', 3, 2, 6), ('empty', 9, 2, 3),
               ('sickbay', 1, 3, 3), ('empty', 4, 3, 2), ('bulwark', 6, 3, 3), ('empty', 9, 3, 2)],
        links=[('rigging', 6, 0), ('ladder', 1, 1), ('stairs', 4, 1), ('ladder', 10, 1), ('ladder', 2, 2),
               ('ladder', 5, 2), ('ladder', 7, 2), ('ladder', 10, 2)],
        masts=[6, 10, 1]),
    'huge': dict(
        rooms=[('nest', 7, 0, 1), ('helm', 0, 1, 3), ('sails', 3, 1, 7), ('empty', 10, 1, 4),
               ('galley', 0, 2, 4), ('guns', 4, 2, 6), ('armory', 10, 2, 3),
               ('sickbay', 1, 3, 3), ('magazine', 4, 3, 3), ('bulwark', 7, 3, 3), ('empty', 10, 3, 2),
               ('hold', 3, 4, 7)],
        links=[('rigging', 7, 0), ('ladder', 1, 1), ('stairs', 4, 1), ('ladder', 11, 1), ('ladder', 2, 2),
               ('ladder', 5, 2), ('ladder', 8, 2), ('ladder', 11, 2), ('ladder', 5, 3), ('ladder', 8, 3)],
        masts=[7, 11, 1]),
}
LAYOUTS['frigate'] = dict(LAYOUTS['large'], rooms=[
    ('nest', 6, 0, 1), ('helm', 0, 1, 3), ('sails', 3, 1, 6), ('empty', 9, 1, 3),
    ('chartroom', 0, 2, 3), ('guns', 3, 2, 6), ('galley', 9, 2, 3),
    ('sickbay', 1, 3, 3), ('magazine', 4, 3, 2), ('bulwark', 6, 3, 3), ('empty', 9, 3, 2)])

# ---------------------------------------------------------------------------
# Enemies
# ---------------------------------------------------------------------------
ENEMIES = {
    # ---- pirates: everywhere, hostile to everyone ----
    'sloop': dict(name='Pirate Sloop', faction='pirate', layout='small', hull=8,
                  sys=dict(helm=1, sails=2, guns=2, bulwark=0, sickbay=0),
                  weapons=['twin_nines'], crew=['pirate', 'pirate', 'pirate'], grapple=0.25, flee=True,
                  names=["The Soggy Biscuit", "The Mild Peril", "The Rusty Cutlass", "The Leaky Larry"]),
    'cutter': dict(name='Smuggler Cutter', faction='pirate', layout='small', hull=8,
                   sys=dict(helm=1, sails=5, guns=2, bulwark=2, sickbay=0),
                   weapons=['chain_shot', 'grapeshot'], crew=['pirate', 'pirate'], grapple=0.0, flee=True,
                   rum=2, names=["The Definitely Fish", "The Not Rum", "The Innocent Crate"]),
    'brig': dict(name='Pirate Brigantine', faction='pirate', layout='medium', hull=12,
                 sys=dict(helm=1, sails=3, guns=4, bulwark=2, sickbay=1),
                 weapons=['twin_nines', 'long_nine'], crew=['pirate', 'pirate', 'pirate', 'brute'],
                 grapple=0.5, flee=True,
                 names=["The Salty Revenge", "The Grumpy Gull", "The Scurvy Dog", "The Bad Idea"]),
    'galleon': dict(name='Pirate Galleon', faction='pirate', layout='large', hull=17,
                    sys=dict(helm=1, sails=2, guns=6, bulwark=2, sickbay=1),
                    weapons=['carronade', 'twin_nines', 'mortar'],
                    crew=['pirate', 'pirate', 'pirate', 'brute', 'brute'], grapple=0.7, flee=True,
                    names=["The Floating Tax Evasion", "The Big Problem", "The Bilge Queen"]),
    'ghost': dict(name='Ghost Ship', faction='ghost', layout='medium', hull=10,
                  sys=dict(helm=1, sails=4, guns=3, bulwark=2, sickbay=0),
                  weapons=['grapeshot', 'long_nine'], crew=['ghost', 'ghost', 'ghost', 'ghost'],
                  grapple=1.0, flee=False, names=["The Damp Mary", "The Eternal Overtime"]),
    # ---- the Crown: hunting you ----
    'revenue': dict(name='Royal Revenue Cutter', faction='crown', layout='small', hull=9,
                    sys=dict(helm=1, sails=3, guns=2, bulwark=2, sickbay=0),
                    weapons=['twin_nines'], crew=['marine', 'marine', 'marine'], grapple=0.3, flee=True,
                    gold=1.4, names=["HMS Audit", "HMS Receipt", "HMS Paperwork", "HMS Surcharge"]),
    'privateer': dict(name='Crown Privateer', faction='pirate', layout='medium', hull=13,
                      sys=dict(helm=1, sails=3, guns=4, bulwark=2, sickbay=1),
                      weapons=['swivel', 'long_nine'], crew=['pirate', 'pirate', 'pirate', 'pirate'],
                      grapple=0.2, flee=True,
                      names=["The Letter of Marque-ish", "The Technically Legal", "The Loophole"]),
    'frigate': dict(name='Royal Frigate', faction='crown', layout='large', hull=20,
                    sys=dict(helm=1, sails=4, guns=7, bulwark=4, sickbay=1),
                    weapons=['swivel', 'carronade', 'hot_shot'],
                    crew=['marine', 'marine', 'marine', 'marine', 'marine'], grapple=0.6, flee=False,
                    names=["HMS Pompous", "HMS Stiff Upper Lip", "HMS Jolly Good", "HMS Frightfully Sorry"]),
    'boss': dict(name='Royal Flagship', faction='crown', layout='huge', hull=32,
                 sys=dict(helm=2, sails=2, guns=10, bulwark=6, sickbay=2),
                 weapons=['royal_32', 'swivel', 'hot_shot', 'mortar'],
                 crew=['admiral', 'marine', 'marine', 'marine', 'marine', 'marine', 'marine'],
                 grapple=1.0, flee=False, names=["HMS Insufferable"]),
}

# ---------------------------------------------------------------------------
# Seas (sectors)
# ---------------------------------------------------------------------------
SECTORS = [
    dict(name='The Shallows', fog=1, ports=2, pool=['sloop', 'sloop', 'cutter', 'revenue'],
         blurb="Gentle waters, amateur pirates, and an alarming number of crabs."),
    dict(name="Smuggler's Reach", fog=2, ports=2, pool=['cutter', 'sloop', 'brig', 'revenue'],
         blurb="Every crate here says NOT RUM in suspiciously large letters."),
    dict(name='The Murk', fog=5, ports=1, pool=['brig', 'ghost', 'privateer', 'revenue'],
         blurb="Fog so thick you could spread it on toast. Visibility: vibes only."),
    dict(name='Kraken Deeps', fog=2, ports=2, pool=['brig', 'privateer', 'galleon', 'revenue'],
         blurb="The water is very deep and the locals are very large."),
    dict(name="The King's Waters", fog=2, ports=1, pool=['privateer', 'galleon', 'revenue', 'frigate'],
         final=True, blurb="The Crown's home waters. Everything is polished. Even the seagulls salute."),
]


# ---------------------------------------------------------------------------
# Player ships (unlockable, like FTL's hangar)
# ---------------------------------------------------------------------------
BASE_CREW = ['captain', 'drunk', 'deckhand', 'monkey', 'carpenter', 'surgeon', 'cook']
SHIPS = {
    'sardine': dict(name='The Plucky Sardine', faction='rebel', layout='courier', hull=30, gusto=8,
                    sys=dict(sails=2, guns=3, bulwark=2, sickbay=1, helm=1, nest=1),
                    weapons=['twin_nines', 'mortar'], crew=['captain', 'drunk', 'deckhand'],
                    rum=12, balls=6, doubloons=30, extra_crew=[],
                    blurb="A fishing sloop with a grudge. Balanced, plucky, and slightly fishy.",
                    unlock=None),
    'cutlass': dict(name='The Rusty Cutlass', faction='pirate', layout='raider', hull=28, gusto=9,
                    sys=dict(sails=3, guns=4, bulwark=2, sickbay=0, helm=1, nest=1),
                    weapons=['twin_nines', 'brimstone'], crew=['pirate', 'brute', 'drunk'],
                    rum=14, balls=4, doubloons=40, extra_crew=['pirate', 'brute'],
                    blurb="Defected pirates. No sick bay (they 'walk it off'), big guns, bigger arms.",
                    unlock=('wins', 8, "Win 8 battles (across all voyages).")),
    'turncoat': dict(name='HMS Turncoat', faction='crown', layout='frigate', hull=34, gusto=10,
                     sys=dict(sails=2, guns=3, bulwark=4, sickbay=1, helm=2, nest=2),
                     weapons=['long_nine', 'long_nine', 'chain_shot'], crew=['captain', 'marine', 'marine'],
                     hands_bonus=1,
                     rum=8, balls=6, doubloons=20, extra_crew=['marine'],
                     blurb="A Royal frigate whose crew mutinied over the biscuit ration. Thick bulwarks, "
                           "terrible tea.",
                     unlock=('best_sea', 3, "Reach the third sea.")),
    'tavern': dict(name='The Floating Tavern', faction='tavern', layout='tavern', hull=32, gusto=9,
                   sys=dict(sails=1, guns=4, bulwark=2, sickbay=2, helm=1, nest=0),
                   weapons=['pepperbox', 'bow_chaser'], crew=['drunk', 'drunk', 'cook', 'drunk'],
                   rum=25, balls=4, doubloons=25, extra_crew=[],
                   blurb="Technically a pub. Three drunks, a cook, 25 barrels of rum. Genuinely slower "
                         "than sardines.",
                   unlock=('max_drunks', 3, "Have 3 Drunkards in your crew at once.")),
    'runner': dict(name='The Rum Runner', faction='smuggler', layout='runner', hull=24, gusto=10,
                   sys=dict(sails=5, guns=3, bulwark=2, sickbay=1, helm=1, nest=1),
                   weapons=['twin_nines', 'quick_nine'], crew=['captain', 'monkey', 'deckhand'],
                   hands_bonus=2,
                   rum=18, balls=3, doubloons=45, extra_crew=[],
                   blurb="Small, fast and very good at not being caught. Thin hull, absurd evasion.",
                   unlock=('wins', 20, "Win 20 battles (across all voyages).")),
    'mary': dict(name='The Damp Mary', faction='ghost', layout='ghostly', hull=30, gusto=9,
                 sys=dict(sails=3, guns=4, bulwark=2, sickbay=0, helm=1, nest=1),
                 weapons=['twin_nines', 'hullbreaker'], crew=['ghost', 'ghost', 'ghost', 'ghost'],
                 rum=10, balls=6, doubloons=30, extra_crew=['ghost'],
                 blurb="A haunted ship crewed by ghosts, who don't need a sick bay on account of being "
                       "dead already. Wooooo.",
                 unlock=('ghosts', 1, "Defeat a Ghost Ship.")),
}
SHIP_ORDER = ['sardine', 'cutlass', 'turncoat', 'tavern', 'runner', 'mary']
