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
                   repair=0.9, fight=8, desc="Arr. That's the whole résumé."),
    'brute': dict(title='Pirate Brute', hp=150, speed=1.6, helm=2, sails=4, guns=1.1, shields=1.0,
                  repair=0.8, fight=12, desc="Large. Angry. Possibly a wardrobe with a beard."),
    'ghost': dict(title='Ghost', hp=70, speed=2.2, helm=6, sails=6, guns=1.2, shields=1.1,
                  repair=1.0, fight=9, desc="Deceased, but still clocking in."),
    'dread': dict(title='Dread Captain', hp=200, speed=1.8, helm=15, sails=5, guns=1.3, shields=1.2,
                  repair=1.0, fight=15, desc="Captain Bartholomew 'Barnacle' Vane. Wants the napkin."),
}

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
    'dread': ["Barnacle Vane"],
}

BARKS = {
    'drunk': ["*hic*", "I see two of 'em. I'll shoot both.", "Is the ship moving or is it me?",
              "This cannon's my best friend.", "Fire in the hole! ...whose hole?",
              "I'm not drunk, I'm nautically flexible.", "Who moved the sea?", "Hold my rum."],
    'captain': ["Steady as she goes!", "I've had worse days. Not many.", "Somebody write this down.",
                "Hold fast, you magnificent idiots!", "For Queen and napkin!", "Nobody panic. Except quietly."],
    'deckhand': ["Aye aye!", "Do I get hazard pay?", "Swabbing can wait, right?", "I joined for the free hat."],
    'monkey': ["More powder! MORE!", "I'm small but I'm loud!", "Can I light the next one?", "Boom! Ha!"],
    'carpenter': ["That's not load-bearing. Probably.", "Measure twice, patch once!",
                  "Who keeps putting holes in my boat?"],
    'surgeon': ["Hold still, this'll hurt a lot.", "I've seen worse. On you, actually.", "Where's my good saw?"],
    'cook': ["Lunch is cancelled!", "Who wants stew? It's survivable!", "Adding cannonballs to the soup."],
    'pirate': ["Arrr!", "Give us the napkin!", "Yo ho ho!", "Har har!", "Yer booty or yer life!"],
    'brute': ["SMASH.", "ARRRRRR.", "Me crush."],
    'ghost': ["Wooooo...", "Join usssss...", "Ye forgot to tip the ferryman..."],
    'dread': ["Ye'll never reach the Armada!", "I'll have that napkin!", "Fire everything! Even Gary!"],
}

# ---------------------------------------------------------------------------
# Systems
# ---------------------------------------------------------------------------
SYSTEMS = {
    'sails': dict(title='Sails', max=8, cost=15, short='SAIL',
                  desc="Each bar adds 5% evasion and speeds your escape."),
    'guns': dict(title='Gun Deck', max=8, cost=20, short='GUNS',
                 desc="Bars power your cannons. Man it to reload faster. Drunks reload fastest."),
    'bulwark': dict(title='Bulwarks', max=8, cost=25, short='BULW',
                    desc="Every 2 bars raise one oak plate that blocks one cannon shot."),
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
                     desc="Property of the Royal Armada. Please return if found. (Don't.)"),
}
LOOT_WEAPONS = ['long_nine', 'long_nine', 'twin_nines', 'carronade', 'chain_shot', 'grapeshot',
                'hot_shot', 'swivel', 'mortar', 'firebomb', 'royal_32']

# ---------------------------------------------------------------------------
# Ship layouts: (system, gx, gy, w, h). Bow points right; enemies are mirrored.
# ---------------------------------------------------------------------------
LAYOUTS = {
    'courier': [('sickbay', 0, 1, 2, 2), ('sails', 2, 0, 2, 2), ('bulwark', 2, 2, 2, 2),
                (None, 4, 1, 2, 2), ('guns', 6, 0, 2, 2), ('nest', 6, 2, 2, 2), ('helm', 8, 1, 2, 2)],
    'small': [('bulwark', 0, 0, 2, 2), ('sails', 0, 2, 2, 2), ('guns', 2, 0, 2, 2),
              ('sickbay', 2, 2, 2, 2), ('helm', 4, 1, 2, 2)],
    'medium': [('sickbay', 0, 1, 2, 2), ('sails', 2, 0, 2, 2), ('bulwark', 2, 2, 2, 2),
               (None, 4, 1, 2, 2), ('guns', 6, 0, 2, 2), (None, 6, 2, 2, 2), ('helm', 8, 1, 2, 2)],
    'large': [('sickbay', 0, 1, 2, 2), ('sails', 2, 0, 3, 2), ('bulwark', 2, 2, 3, 2),
              ('guns', 5, 0, 2, 2), (None, 5, 2, 2, 2), (None, 7, 1, 2, 2), ('helm', 9, 1, 2, 2)],
    'huge': [('sickbay', 0, 1, 2, 3), ('sails', 2, 0, 3, 2), (None, 2, 2, 3, 1),
             ('bulwark', 2, 3, 3, 2), ('guns', 5, 0, 3, 2), (None, 5, 2, 3, 1), (None, 5, 3, 3, 2),
             ('helm', 8, 1, 2, 3)],
}

# ---------------------------------------------------------------------------
# Enemies
# ---------------------------------------------------------------------------
ENEMIES = {
    'sloop': dict(name='Pirate Sloop', layout='small', hull=8,
                  sys=dict(helm=1, sails=2, guns=2, bulwark=0, sickbay=0),
                  weapons=['twin_nines'], crew=['pirate', 'pirate', 'pirate'], grapple=0.25, flee=True,
                  names=["The Soggy Biscuit", "The Mild Peril", "The Rusty Cutlass", "The Leaky Larry"]),
    'cutter': dict(name='Smuggler Cutter', layout='small', hull=8,
                   sys=dict(helm=1, sails=5, guns=2, bulwark=2, sickbay=0),
                   weapons=['chain_shot', 'grapeshot'], crew=['pirate', 'pirate'], grapple=0.0, flee=True, rum=2,
                   names=["The Definitely Fish", "The Not Rum", "The Innocent Crate"]),
    'brig': dict(name='Pirate Brigantine', layout='medium', hull=12,
                 sys=dict(helm=1, sails=3, guns=4, bulwark=2, sickbay=1),
                 weapons=['twin_nines', 'long_nine'], crew=['pirate', 'pirate', 'pirate', 'brute'],
                 grapple=0.5, flee=True,
                 names=["The Salty Revenge", "The Grumpy Gull", "The Scurvy Dog", "The Bad Idea"]),
    'privateer': dict(name='Rogue Privateer', layout='medium', hull=13,
                      sys=dict(helm=1, sails=3, guns=4, bulwark=2, sickbay=1),
                      weapons=['swivel', 'long_nine'], crew=['pirate', 'pirate', 'pirate', 'pirate'],
                      grapple=0.2, flee=True,
                      names=["The Letter of Marque-ish", "The Technically Legal", "The Loophole"]),
    'ghost': dict(name='Ghost Ship', layout='medium', hull=10,
                  sys=dict(helm=1, sails=4, guns=3, bulwark=2, sickbay=0),
                  weapons=['grapeshot', 'long_nine'], crew=['ghost', 'ghost', 'ghost', 'ghost'],
                  grapple=1.0, flee=False, names=["The Damp Mary", "The Eternal Overtime"]),
    'galleon': dict(name='Pirate Galleon', layout='large', hull=17,
                    sys=dict(helm=1, sails=2, guns=6, bulwark=2, sickbay=1),
                    weapons=['carronade', 'twin_nines', 'mortar'],
                    crew=['pirate', 'pirate', 'pirate', 'brute', 'brute'], grapple=0.7, flee=True,
                    names=["The Floating Tax Evasion", "The Big Problem", "The Bilge Queen"]),
    'tide': dict(name='Black Tide Man-o-War', layout='large', hull=20,
                 sys=dict(helm=1, sails=4, guns=7, bulwark=4, sickbay=1),
                 weapons=['swivel', 'carronade', 'firebomb'],
                 crew=['pirate', 'pirate', 'brute', 'brute', 'brute'], grapple=0.8, flee=False,
                 names=["The Black Tide", "The Inevitable", "The Told-You-So"]),
    'boss': dict(name="The Leviathan's Grin", layout='huge', hull=30,
                 sys=dict(helm=2, sails=2, guns=10, bulwark=6, sickbay=2),
                 weapons=['royal_32', 'swivel', 'firebomb', 'mortar'],
                 crew=['dread', 'pirate', 'pirate', 'pirate', 'brute', 'brute', 'brute'],
                 grapple=1.0, flee=False, names=["The Leviathan's Grin"]),
}

# ---------------------------------------------------------------------------
# Seas (sectors)
# ---------------------------------------------------------------------------
SECTORS = [
    dict(name='The Shallows', fog=1, ports=2, pool=['sloop', 'sloop', 'cutter'],
         blurb="Gentle waters, amateur pirates, and an alarming number of crabs."),
    dict(name="Smuggler's Reach", fog=2, ports=2, pool=['cutter', 'sloop', 'brig'],
         blurb="Where every crate says NOT RUM in suspiciously large letters."),
    dict(name='The Murk', fog=5, ports=1, pool=['brig', 'ghost', 'privateer'],
         blurb="Fog so thick you could spread it on toast. Visibility: vibes only."),
    dict(name='Kraken Deeps', fog=2, ports=2, pool=['brig', 'privateer', 'galleon'],
         blurb="The water is very deep and the locals are very large."),
    dict(name='Royal Waters', fog=2, ports=1, pool=['privateer', 'galleon', 'brig'], final=True,
         blurb="The Royal Armada is near. So, unfortunately, is everyone else."),
]
