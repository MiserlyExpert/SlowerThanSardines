"""Event text and choices.

Choice keys:
  text  - label. req - requirements: crew=<class>, doubloons/rum/balls=<n>, crew_n=<n>
  out   - a single outcome, or outs - list of (weight, outcome)
Outcome keys:
  text, doubloons/rum/balls/hull (int or (lo, hi)), heal, all_hurt, crew_hurt,
  add_crew (class or 'random'), lose_crew, weapon (key or 'random'), gusto, upgrade,
  fleet (px the Black Tide moves), fight (enemy key), win (bonus outcome after a win),
  store, exit, boss, next (another event)
Text placeholders: {drunk} {captain} {crew} {ship} {enemy} {sector} {next}
"""

INTRO = dict(
    id='intro',
    title='The Napkin of Destiny',
    text=("Last Tuesday, a Royal spy got gloriously drunk in a pirate tavern and scribbled the location "
          "of the pirates' secret base on a bar napkin. Then he fell asleep in the soup.\n\n"
          "{drunk} found the napkin while looking for the soup. Which makes the {ship} the most "
          "important vessel in the Queen's service.\n\n"
          "Deliver the napkin to the Royal Armada in Royal Waters, five seas away. The Black Tide pirate "
          "fleet wants it back. They are right behind you. No pressure. (Some pressure.)"),
    choices=[dict(text="For Queen and Napkin!", out=dict())],
)

EVENTS = [
    dict(id='mermaid', text=(
        "A mermaid surfaces beside the hull and asks, very politely, whether anyone has seen her comb. "
        "She describes it. It is a fork. She calls it a comb."),
        choices=[
            dict(text="Hand over a fork from the galley.", outs=[
                (6, dict(text="She is delighted, and tells you where a smuggler dumped his cargo.",
                         rum=3, doubloons=(8, 15))),
                (4, dict(text="She is furious. That was NOT her comb. She slaps the hull with her tail. "
                              "It is a surprisingly strong tail.", hull=-3)),
            ]),
            dict(text="Let {drunk} talk to her.", req=dict(crew='drunk'), out=dict(
                text="{drunk} and the mermaid sing a duet so off-key that a passing whale files a noise "
                     "complaint. She leaves a barnacled chest as thanks for the 'harmonies'.",
                doubloons=(25, 40))),
            dict(text="Sail on. We have a napkin to deliver.", out=dict(
                text="She waves goodbye. With the fork.")),
        ]),
    dict(id='crabs', text=(
        "The crow's nest reports a sandbar covered in crabs. Thousands of them. "
        "They appear to be... organized."),
        choices=[
            dict(text="Land a party and collect dinner.", outs=[
                (5, dict(text="Delicious. The crew eats like royalty, if royalty ate crab with their hands.",
                         heal=35)),
                (5, dict(text="The crabs are organized. They have a king. He has a tiny sword. "
                              "{crew} retreats with 35 fewer hit points and one fewer shred of dignity.",
                         crew_hurt=35)),
            ]),
            dict(text="Let the cook negotiate.", req=dict(crew='cook'), out=dict(
                text="The cook and the Crab King reach an understanding. You don't ask what it is. "
                     "You leave with rum, gold, and a deep sense of unease.", rum=2, doubloons=15)),
            dict(text="Leave the crabs to their revolution.", out=dict(
                text="Somewhere behind you, a tiny trumpet sounds.")),
        ]),
    dict(id='merchant', text=(
        "A merchant cog wallows past, so overloaded it's mostly underwater. "
        "Its captain begs for help with a leak."),
        choices=[
            dict(text="Help bail them out.", out=dict(
                text="{crew} spends an hour bailing water in exchange for coin and a lifetime supply of "
                     "gratitude (non-transferable).", doubloons=(12, 22))),
            dict(text="Send the carpenter.", req=dict(crew='carpenter'), out=dict(
                text="Your carpenter fixes the leak, then rebuilds their entire hold out of spite. "
                     "They pay double and throw in some shot.", doubloons=(35, 45), balls=2)),
            dict(text="Rob them. We're the good guys, but we're also broke.", out=dict(
                text="The 'merchant' crew turns out to be ex-marines. Of course they are.",
                fight='cutter')),
        ]),
    dict(id='fog_voice', tags=['fog'], text=(
        "Out of the fog drifts a voice: 'Ahoy... ahoy...' It seems to be coming from inside the rum barrel."),
        choices=[
            dict(text="Investigate the barrel.", outs=[
                (5, dict(text="It's a parrot. It has been in there since Tuesday. It says 'AHOY' and nothing "
                              "else, ever. Morale is inexplicably through the roof.", gusto=1)),
                (5, dict(text="It's a ghost. A very small, very drunk ghost. It hiccups once and vanishes, "
                              "taking two barrels of rum with it.", rum=-2)),
            ]),
            dict(text="Ignore it and sail faster.", out=dict(
                text="You cannot sail faster. It's fog. That's the whole problem with fog.", fleet=25)),
        ]),
    dict(id='ghost_ship', tags=['fog'], text=(
        "A ship emerges from the fog. Its sails are tattered, its hull glows green, and its crew is waving "
        "in a way that suggests they've been dead for some time."),
        choices=[
            dict(text="Wave back.", out=dict(text="Wrong answer. The ghosts take that as consent to board.",
                                             fight='ghost', win=dict(weapon='grapeshot'))),
            dict(text="Have the surgeon diagnose them from here.", req=dict(crew='surgeon'), out=dict(
                text="'Severely deceased,' announces your surgeon. The ghosts, offended at being diagnosed "
                     "without an appointment, sail off in a huff, dropping a crate of shot.", balls=4)),
            dict(text="Flee into the fog!", outs=[
                (6, dict(text="You escape. The fog was on your side, for once. It took a while, though.",
                         fleet=20)),
                (4, dict(text="The ghost ship is faster. Ghosts don't have to worry about drag.",
                         fight='ghost')),
            ]),
        ]),
    dict(id='kraken', sectors=[2, 3, 4], text=(
        "A tentacle the size of a mainmast rises from the deep and taps your hull. Politely. "
        "Like it's knocking."),
        choices=[
            dict(text="Knock back.", outs=[
                (5, dict(text="The kraken seems pleased. It coughs up something shiny it swallowed years ago.",
                         weapon='random')),
                (5, dict(text="That was apparently rude in kraken. It knocks again. Harder. Through the hull.",
                         hull=-5, crew_hurt=20)),
            ]),
            dict(text="Fire a cannonball at it. (1 cannonball)", req=dict(balls=1), out=dict(
                text="The ball bounces off. The tentacle retreats, more embarrassed than hurt. "
                     "You salvage some floating debris.", balls=-1, doubloons=20)),
            dict(text="{drunk} offers it a drink.", req=dict(crew='drunk'), out=dict(
                text="The kraken accepts. It is now your best friend. It escorts you for a while, "
                     "frightening off the Black Tide's scouts.", rum=-1, fleet=-60)),
        ]),
    dict(id='castaway', text=(
        "A man on a tiny island waves frantically. He has a very long beard, a coconut with a face drawn "
        "on it, and strong opinions about the coconut."),
        choices=[
            dict(text="Rescue him.", outs=[
                (7, dict(text="He joins your crew. He insists the coconut gets its own bunk. It does not.",
                         add_crew='random')),
                (3, dict(text="He's not a castaway. He's a pirate lookout. He fires a flare and cackles. "
                              "Then he sits back down. He seems to genuinely like the island.",
                         fight='sloop')),
            ]),
            dict(text="Just take the coconut.", out=dict(
                text="He weeps. You feel terrible. The coconut is delicious, which makes it worse.", heal=15)),
        ]),
    dict(id='tavern', text=(
        "A floating tavern bobs at anchor, lit by lanterns and poor decisions. "
        "A sign reads: NO FIGHTING (AFTER 9PM). It is 8:57pm."),
        choices=[
            dict(text="Stop for a quick drink. (5 doubloons)", req=dict(doubloons=5), out=dict(
                text="One drink becomes several. The crew returns rested and only slightly fewer.",
                doubloons=-5, rum=3, heal=20)),
            dict(text="Unleash {drunk}.", req=dict(crew='drunk'), out=dict(
                text="In three minutes {drunk} wins a drinking contest, a fistfight, an arm-wrestling "
                     "tournament, and the deed to a slightly used cannon. It is now 9:00pm.",
                weapon='random', doubloons=10)),
            dict(text="Hire a sailor. (30 doubloons)", req=dict(doubloons=30), out=dict(
                text="A sailor of reasonable sobriety signs on.", doubloons=-30, add_crew='random')),
            dict(text="Keep sailing.", out=dict(text="Behind you, a chair flies out of a window. 9pm sharp.")),
        ]),
    dict(id='armada_patrol', text=(
        "A Royal Armada frigate pulls alongside. A young officer in a terrifyingly clean uniform inspects "
        "your papers. 'Courier service? Napkin delivery? How... quaint.'"),
        choices=[
            dict(text="Request supplies in the Queen's name.", outs=[
                (6, dict(text="He sighs and hands over supplies, plus a form to fill out in triplicate.",
                         rum=2, balls=2)),
                (4, dict(text="'Do you have Form 27-B?' You do not. You leave with nothing but a lasting "
                              "resentment of paperwork.")),
            ]),
            dict(text="Pull rank.", req=dict(crew='captain'), out=dict(
                text="Your captain outranks him by two promotions and one exceptional moustache. "
                     "He resupplies you and sends his carpenters over.", hull=8, balls=3)),
            dict(text="Show him the napkin.", out=dict(
                text="He reads it. Goes pale. Salutes. 'Godspeed, courier.' Then he gives you nothing, "
                     "because saluting is free.")),
        ]),
    dict(id='storm', text="Black clouds gather. Thunder rolls. The barometer just says NOPE.",
         choices=[
             dict(text="Ride it out.", outs=[
                 (5, dict(text="The storm batters you, but you survive. Your sails are ragged. "
                               "So is your spirit.", hull=-4)),
                 (5, dict(text="The storm flings you along at terrific speed! You gain distance on the "
                               "Black Tide.", fleet=-40)),
             ]),
             dict(text="Let the captain steer through it.", req=dict(crew='captain'), out=dict(
                 text="Your captain threads the storm like they're parallel parking. "
                      "You emerge well ahead of schedule.", fleet=-55)),
         ]),
    dict(id='bottle', text=(
        "A message in a bottle bobs alongside. 'If you're reading this, I've buried treasure on an island "
        "nearby. Signed, Definitely Not A Trap.'"),
        choices=[
            dict(text="Go dig.", outs=[
                (6, dict(text="There IS treasure! Definitely Not A Trap was a person of their word.",
                         doubloons=(30, 50))),
                (4, dict(text="It's a trap. The island is a pirate camp with a gift shop.", fight='sloop')),
            ]),
            dict(text="Drink whatever's left in the bottle.", out=dict(
                text="It was seawater. {crew} drinks it anyway, to save face.", crew_hurt=10)),
            dict(text="Ignore it.", out=dict(text="It bobs away, disappointed in you.")),
        ]),
    dict(id='derelict', text=(
        "A derelict merchantman lists in the water. No crew in sight. The captain's cabin door creaks "
        "ominously, as doors in these situations always do."),
        choices=[
            dict(text="Search it.", outs=[
                (5, dict(text="Salvage! Coins, shot, and a ship's cat who declines to join you.",
                         doubloons=(20, 35), balls=2)),
                (3, dict(text="Pirate ambush! The oldest trick in the book. Pirates have only read one book.",
                         fight='sloop')),
                (2, dict(text="{crew} falls through a rotten deck and gets wedged in a barrel. "
                              "Freeing them takes hours.", crew_hurt=20, fleet=20)),
            ]),
            dict(text="Strip it for timber.", req=dict(crew='carpenter'), out=dict(
                text="Your carpenter strips the wreck and patches your hull lovingly. Tenderly. "
                     "It's a bit weird to watch, honestly.", hull=7)),
            dict(text="Leave it.", out=dict(text="The door creaks once more, offended.")),
        ]),
    dict(id='rum_strike', text=(
        "The crew gathers on deck, arms crossed. Their spokesperson, {crew}, clears their throat. "
        "'We want more rum. And dental.'"),
        choices=[
            dict(text="Open an extra barrel. (2 rum)", req=dict(rum=2), out=dict(
                text="The crew cheers. Dental is tabled for a later meeting.", rum=-2, heal=25)),
            dict(text="Give a rousing speech.", req=dict(crew='captain'), out=dict(
                text="Your captain's speech about duty, honour and the Queen's famously generous pension plan "
                     "moves the crew to tears. They go back to work inspired and underpaid.", heal=10)),
            dict(text="Refuse.", out=dict(
                text="{crew} 'accidentally' drops a cannonball on your foot. Several times.", crew_hurt=20)),
        ]),
    dict(id='whale', text="A whale surfaces next to the ship and fixes you with one enormous, judgemental eye.",
         choices=[
             dict(text="Stare back.", outs=[
                 (5, dict(text="You win the staring contest. The whale swims off, humbled. Morale soars.",
                          heal=15)),
                 (5, dict(text="You lose. The whale sprays you. Everyone is wet and ashamed.")),
             ]),
             dict(text="Let the powder monkey ride it.", req=dict(crew='monkey'), out=dict(
                 text="Against several laws of physics, the powder monkey rides the whale for a mile and "
                      "comes back with a waterlogged treasure chest.", doubloons=(30, 40))),
         ]),
    dict(id='smugglers', sectors=[1, 2, 3], text=(
        "A smuggler blinks a lantern in code. Your signalman translates: "
        "'Want to buy rum? Not stolen. Only slightly stolen.'"),
        choices=[
            dict(text="Buy rum. (15 doubloons)", req=dict(doubloons=15), out=dict(
                text="Four barrels of extremely legitimate rum.", doubloons=-15, rum=4)),
            dict(text="Let {drunk} sample it first.", req=dict(crew='drunk'), out=dict(
                text="{drunk} samples. And samples. The smugglers, impressed and a little frightened, "
                     "give you the rest for free.", rum=5)),
            dict(text="Report them to the Armada.", out=dict(
                text="They overhear. Smugglers have excellent hearing.", fight='cutter')),
        ]),
    dict(id='sirens', text=(
        "Beautiful singing drifts across the water. The crew starts walking, dreamily, toward the rail."),
        choices=[
            dict(text="Plug everyone's ears with wax.", out=dict(
                text="Everyone survives! Unfortunately nobody can hear orders for an hour.", fleet=15)),
            dict(text="{drunk} sings back.", req=dict(crew='drunk'), out=dict(
                text="{drunk}'s singing is so bad the sirens flee in horror. One drops her purse.",
                doubloons=25)),
            dict(text="Let them listen. What's the worst that could happen?", out=dict(
                text="{crew} walks right off the ship. You fish them out, but they keep humming.",
                crew_hurt=40)),
        ]),
    dict(id='press_gang', text=(
        "A navy press-gang boat approaches. 'We're short-handed! We'll be taking one of your crew "
        "for the Armada. For the Queen!'"),
        choices=[
            dict(text="Hand over a 'volunteer'.", req=dict(crew_n=3), out=dict(
                text="Your crew volunteers {crew} by all taking one big step backward. "
                     "The Armada pays a modest finder's fee.", lose_crew=True, doubloons=35)),
            dict(text="'We're on the Queen's business too!'", req=dict(crew='captain'), out=dict(
                text="Your captain waves the napkin at them. They apologise and leave a crate of shot "
                     "as a peace offering.", balls=4)),
            dict(text="Refuse and sail off.", outs=[
                (5, dict(text="They let you go. They had a quota, not a death wish.")),
                (5, dict(text="They're not navy at all — they're pirates in borrowed hats!", fight='sloop')),
            ]),
        ]),
    dict(id='cursed_gold', text="You fish a chest of gold out of the sea. It's cold to the touch, and whispers.",
         choices=[
             dict(text="Keep it.", out=dict(
                 text="Everyone has nightmares about a man made of eels. The gold spends fine, though.",
                 doubloons=60, all_hurt=15)),
             dict(text="Have the surgeon examine it.", req=dict(crew='surgeon'), out=dict(
                 text="The surgeon declares the gold 'mostly harmless' and the whispering 'probably tinnitus'.",
                 doubloons=50)),
             dict(text="Throw it back.", out=dict(text="The sea burps. Gratitude, presumably.", heal=20)),
         ]),
    dict(id='serpent', tags=['fog'], text=(
        "In the fog, something enormous passes beneath the ship. The water bulges. "
        "Nobody breathes."),
        choices=[
            dict(text="Stay perfectly still.", outs=[
                (7, dict(text="It passes. Everybody exhales. Somebody faints.")),
                (3, dict(text="It notices you.", hull=-6)),
            ]),
            dict(text="Fire a cannonball at it. (1 cannonball)", req=dict(balls=1), outs=[
                (5, dict(text="Direct hit! It sinks into the depths, leaving behind a tooth worth a fortune.",
                         balls=-1, doubloons=45)),
                (5, dict(text="You have made it angry. Well done.", balls=-1, hull=-8)),
            ]),
        ]),
    dict(id='raft', text=(
        "A pirate raft approaches: two pirates and a very small cannon. They are attempting to board you."),
        choices=[
            dict(text="Let them try.", out=dict(
                text="They try. It's adorable. You confiscate their little cannon and their lunch money.",
                weapon='long_nine', doubloons=8)),
            dict(text="Offer them a job.", outs=[
                (5, dict(text="One accepts, swears off piracy, and immediately asks about dental.",
                         add_crew='pirate')),
                (5, dict(text="They accept, then immediately try to steal the napkin. Overboard they go.")),
            ]),
        ]),
    dict(id='lighthouse', text=(
        "A lighthouse keeper rows out to meet you. 'Haven't seen a soul in eleven years,' he says. "
        "'Want to hear about my rock collection?'"),
        choices=[
            dict(text="Listen to the whole thing.", out=dict(
                text="It takes six hours. Some of the rocks are, admittedly, very good rocks. "
                     "He gives you his favourite and some supplies.", fleet=25, doubloons=20, rum=2)),
            dict(text="Politely decline.", out=dict(
                text="He rows away, crushed. You hear him tell a rock about it.")),
        ]),
    dict(id='cannon_sale', text=(
        "A fast-talking salesman on a dinghy waves a cannon at you. 'One owner! Only fired in anger twice! "
        "For you? Special price!'"),
        choices=[
            dict(text="Buy the cannon. (40 doubloons)", req=dict(doubloons=40), out=dict(
                text="It's a real cannon. You're as surprised as he is.", doubloons=-40, weapon='random')),
            dict(text="Haggle.", outs=[
                (5, dict(text="You haggle him down to a crate of shot and a firm handshake.", balls=3,
                         doubloons=-10)),
                (5, dict(text="He haggles YOU. Somehow you pay him to leave.", doubloons=-10)),
            ]),
            dict(text="No thanks.", out=dict(text="'Your loss! Literally! In the next fight!'")),
        ]),
    dict(id='seagull', text=(
        "A seagull lands on the helm, steals {captain}'s lunch, and stares at everybody, daring them."),
        choices=[
            dict(text="Chase it off.", out=dict(
                text="It takes three sailors, a broom and a dignified retreat. The gull keeps the sandwich.",
                crew_hurt=8)),
            dict(text="Adopt it.", out=dict(
                text="It is now the ship's mascot. It is named Admiral Squawk. It outranks you.")),
        ]),
]

DISTRESS = [
    dict(id='survivors', text=(
        "Two survivors cling to a floating door. There is clearly room on the door for both of them, "
        "but they've decided to argue about it instead."),
        choices=[
            dict(text="Rescue them.", out=dict(
                text="One joins your crew. The other refuses to leave the door. Respect.",
                add_crew='random')),
            dict(text="Throw them a rope and a lecture on buoyancy.", out=dict(
                text="They thank you for the rope. The lecture, less so.")),
        ]),
    dict(id='sinking_merchant', text=(
        "A merchant ship is sinking, fast. A pirate sloop circles it like a smug shark."),
        choices=[
            dict(text="Drive off the pirates!", out=dict(
                text="Battle stations!", fight='sloop',
                win=dict(text="The grateful merchants reward you handsomely.", doubloons=(20, 30), rum=2))),
            dict(text="Pretend you didn't see.", out=dict(
                text="Everyone saw you pretend. Morale dips. So, slightly, does your self-respect.")),
        ]),
    dict(id='flare', text=(
        "A red flare arcs over the water from a small, sad-looking ketch."),
        choices=[
            dict(text="Investigate.", outs=[
                (5, dict(text="It's a lost Armada supply ship! They're glad to share.", balls=3, rum=3,
                         hull=4)),
                (3, dict(text="It's an ambush, because of course it is.", fight='brig')),
                (2, dict(text="It's a birthday party. The flare was a candle. You are given cake.", heal=30)),
            ]),
            dict(text="Ignore it.", out=dict(text="It was probably nothing. It was probably fine.")),
        ]),
]

QUIET = [
    "Nothing but water. Lots of it. {crew} points out that it's 'very wet', which is true.",
    "Calm seas. The crew plays cards. {drunk} cheats, and loses anyway.",
    "A pleasant breeze. Somebody starts a sea shanty. Somebody else ends it.",
    "You pass a rock shaped exactly like the Queen. Everyone salutes, just in case.",
    "An empty patch of sea. {crew} spends the afternoon arguing with a seagull, and loses.",
]

FIGHT_INTROS = [
    "A {enemy} bears down on you, flags flying. Its crew is chanting something rude about your mother.",
    "Sails on the horizon! It's {enemy_name}, a {enemy}, and they've already opened their gunports.",
    "A {enemy} cuts across your bow. Their captain yells 'Hand over the napkin!' How do they know?!",
    "{enemy_name} drifts out from behind an island. It's a {enemy}. They look bored. You look like fun.",
]

PORT_TEXT = [
    "You drop anchor at a bustling port. The tavern is called The Drowned Rat. The food is called worse.",
    "A sleepy harbour town. The shipwright is awake, the shopkeeper is awake, the dog is not.",
    "A floating market lashed together from fifty boats. Everything is for sale, including, briefly, your ship.",
]


def fight_event(enemy_key, enemy_title, enemy_name, rng):
    return dict(id='fight', text=rng.choice(FIGHT_INTROS).replace('{enemy}', enemy_title)
                .replace('{enemy_name}', enemy_name),
                choices=[
                    dict(text="Battle stations!", out=dict(fight=enemy_key)),
                    dict(text="Try to outrun them.", outs=[
                        (4, dict(text="You slip away! It costs time, though.", fleet=20)),
                        (6, dict(text="They're faster. They're always faster.", fight=enemy_key)),
                    ]),
                ])


def port_event(rng):
    return dict(id='port', text=rng.choice(PORT_TEXT),
                choices=[dict(text="Visit the market.", out=dict(store=True)),
                         dict(text="Weigh anchor and leave.", out=dict())])


def tide_event():
    return dict(id='tide', text=(
        "The Black Tide has caught up with you! A pirate man-o-war, black sails snapping, swings its "
        "broadside toward you. This is going to be unpleasant."),
        choices=[
            dict(text="Fight them.", out=dict(fight='tide')),
            dict(text="Offer a bribe. (40 doubloons)", req=dict(doubloons=40), outs=[
                (5, dict(text="They take the money and wave you on. Honour among thieves!", doubloons=-40)),
                (5, dict(text="They take the money. Then they attack anyway. Honour among thieves?",
                         doubloons=-40, fight='tide')),
            ]),
        ])


def exit_event(sector, nxt):
    if sector.final:
        return dict(id='finale', title='Royal Waters', text=(
            "There! On the horizon! The Royal Armada's flagship, bunting and all, with a brass band "
            "warming up on deck.\n\nBetween you and it, rising from the waves like a bad decision: "
            "The Leviathan's Grin, flagship of the Black Tide. Dread Captain Barnacle Vane himself "
            "roars across the water: 'THAT NAPKIN IS MINE!'"),
            choices=[dict(text="Over my dead napkin! (Final battle)", out=dict(fight='boss', boss=True)),
                     dict(text="Not yet. Let me prepare.", out=dict())])
    return dict(id='exit', text=(
        "You reach the edge of {sector}. Beyond lies {next}.\n\nOnce you leave, there's no coming back."),
        choices=[dict(text="Set sail for {next}.", out=dict(exit=True)),
                 dict(text="Stay a little longer.", out=dict())])
