"""Event text and choices.

Choice keys:
  text  - label. req - requirements: crew=<class>, doubloons/rum/balls=<n>, crew_n=<n>
  out   - a single outcome, or outs - list of (weight, outcome)
Outcome keys:
  text, doubloons/rum/balls/hull (int or (lo, hi)), heal, all_hurt, crew_hurt,
  add_crew (class or 'random'), lose_crew, weapon (key or 'random'), gusto, upgrade,
  fleet (px the Royal Armada moves), fight (enemy key), win (bonus outcome after a win),
  store, exit, boss, next (another event)
Text placeholders: {drunk} {captain} {crew} {ship} {enemy} {sector} {next}
"""

INTRO = dict(
    id='intro',
    title='The Sardine Rebellion',
    text=("By Royal Decree, every fish in the sea is now Property of His Majesty. Sardines require a licence. "
          "Small sardines require a smaller, more expensive licence.\n\n"
          "Enough is enough. You and the crew of {ship} are the Free Fishers: fishermen turned freedom "
          "fighters. Last night {drunk} stole the blueprints of HMS Insufferable, the Crown's gigantic "
          "flagship and floating tax office. They reveal one weakness: the powder magazine sits directly "
          "under the Admiral's tea room.\n\n"
          "HMS Insufferable waits at anchor in the King's Waters, five seas away. Sail there and sink it. "
          "The Royal Armada is already chasing you, at a dignified pace, with a brass band."),
    choices=[dict(text="Down with the Sardine Tax!", out=dict())],
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
                     "complaint. She leaves a barnacled chest to thank them for the 'harmonies'.",
                doubloons=(25, 40))),
            dict(text="Sail on. We have a revolution to run.", out=dict(
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
            dict(text="Rob them. We're freedom fighters, but we're also broke.", out=dict(
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
                     "frightening off the Armada's scouts.", rum=-1, fleet=-60)),
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
    dict(id='inspection', text=(
        "A Royal Armada cutter signals you to heave to for inspection. An officer squints at your ship "
        "through a monocle, then through a second, larger monocle."),
        choices=[
            dict(text="Pretend to be humble fishermen.", outs=[
                (6, dict(text="'Carry on, peasants.' He even buys some fish. You were, technically, humble "
                              "fishermen.", doubloons=12)),
                (4, dict(text="He spots the rebel flag you forgot to take down. It has a sardine on it. "
                              "Awkward.", fight='revenue')),
            ]),
            dict(text="Claim to be a visiting Duke.", req=dict(crew='captain'), out=dict(
                text="Your captain announces themself as the Duke of Little Soggington. The officer bows so "
                     "deeply he falls overboard. You help yourself to his supplies while he fishes himself out.",
                balls=3, rum=2)),
            dict(text="Open fire. Viva la sardine!", out=dict(
                text="'How DARE you,' he says, mostly to his monocle.", fight='revenue')),
        ]),
    dict(id='taxman', text=(
        "A Royal Revenue officer rows over with a ledger the size of a door. 'Sardine Tax, Herring Levy, "
        "and the Breathing-Near-The-King's-Water Duty. That will be thirty doubloons.'"),
        choices=[
            dict(text="Pay the tax. (30 doubloons)", req=dict(doubloons=30), out=dict(
                text="He hands you a receipt. There is a small tax on the receipt.", doubloons=-32)),
            dict(text="Offer him a bowl of stew.", req=dict(crew='cook'), out=dict(
                text="He eats it. He is never the same again. He forgives your taxes, quits the Crown and "
                     "rows off to become a poet, leaving his cashbox behind.", doubloons=(20, 30))),
            dict(text="Throw his ledger in the sea.", out=dict(
                text="He blows a tiny silver whistle. A revenue cutter appears from behind a rock. "
                     "It was waiting there the whole time. Taxmen are patient.", fight='revenue',
                win=dict(text="You find the tax chest. It's full of everyone else's money.", doubloons=30))),
        ]),
    dict(id='tea_time', text=(
        "Through the spyglass: an entire Armada squadron, sitting perfectly still in the water. "
        "It's four o'clock. They're having tea."),
        choices=[
            dict(text="Sneak past quietly.", out=dict(
                text="You tiptoe past. Nobody even looks up. Somebody asks for the milk.", fleet=-45)),
            dict(text="Steal their biscuits.", outs=[
                (5, dict(text="You row off with the biscuit tin. It's solid silver. The biscuits are stale.",
                         doubloons=30, heal=15)),
                (5, dict(text="A marine catches you mid-biscuit. Tea time is OVER.", fight='revenue')),
            ]),
            dict(text="Have {drunk} play the bagpipes at them.", req=dict(crew='drunk'), out=dict(
                text="Twelve ships spill their tea at once. The squadron is too upset to give chase. "
                     "Several officers are weeping.", fleet=-70)),
        ]),
    dict(id='wanted', text=(
        "A wanted poster is nailed to a buoy. It shows your ship, drawn badly. The caption reads: "
        "WANTED: THE PLUCKY SARDINE. SLOWER THAN SARDINES. SMELLS LIKE THEM TOO."),
        choices=[
            dict(text="Tear it down.", out=dict(
                text="Morale improves. The crew agrees the drawing made the ship look fat.", heal=10)),
            dict(text="Let {drunk} make some improvements.", req=dict(crew='drunk'), out=dict(
                text="{drunk} draws a moustache on the Admiral's portrait in the corner and adds the words "
                     "'SMELLS LIKE A CRUMPET'. Morale skyrockets.", heal=25)),
            dict(text="Claim the reward yourself.", out=dict(
                text="It turns out you can't hand yourself in for the reward. You tried, though. "
                     "The clerk was very confused.", fleet=15)),
        ]),
    dict(id='pirate_parley', text=(
        "A pirate brig hails you. 'Oi! You the lot what keeps annoying the Armada? We like you. "
        "A bit. Still gonna rob you, though.'"),
        choices=[
            dict(text="Fight them.", out=dict(text="'Nothing personal!' they shout. It feels personal.",
                                             fight='brig')),
            dict(text="Pay for safe passage. (20 doubloons)", req=dict(doubloons=20), out=dict(
                text="They take the coin and throw you a jaunty salute. One of them winks. Why the wink?",
                doubloons=-20)),
            dict(text="Propose an alliance against the Crown.", req=dict(crew='captain'), out=dict(
                text="Your captain's speech about freedom, fish and the tyranny of licences moves the pirate "
                     "captain to tears. 'Down with the Crown!' he sobs, and throws you a crate of shot. "
                     "'Now get lost before I change me mind.'", balls=4, rum=2)),
        ]),
    dict(id='storm', text="Black clouds gather. Thunder rolls. The barometer just says NOPE.",
         choices=[
             dict(text="Ride it out.", outs=[
                 (5, dict(text="The storm batters you, but you survive. Your sails are ragged. "
                               "So is your spirit.", hull=-4)),
                 (5, dict(text="The storm flings you along at terrific speed! You gain distance on the "
                               "Armada.", fleet=-40)),
             ]),
             dict(text="Let the captain steer through it.", req=dict(crew='captain'), out=dict(
                 text="Your captain threads the storm like they're parallel parking. "
                      "The Armada, who refuse to sail in weather 'this common', fall well behind.", fleet=-55)),
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
        "A Royal Navy press-gang boat approaches. 'We're short-handed! We'll be taking one of your crew "
        "for His Majesty's service. It's an honour! Mostly.'"),
        choices=[
            dict(text="Send {drunk} as the 'volunteer'.", req=dict(crew='drunk'), out=dict(
                text="{drunk} goes willingly. An hour later, the Armada rows them back with a crate of rum, "
                     "a formal apology and a strongly worded letter.", rum=3)),
            dict(text="Fight them off!", out=dict(text="'Resisting the press! Most irregular!'",
                                                  fight='revenue')),
            dict(text="Hand someone over.", req=dict(crew_n=3), out=dict(
                text="Your crew volunteers {crew} by all taking one big step backward. You'll miss them. "
                     "A bit.", lose_crew=True, doubloons=20)),
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
                (5, dict(text="They accept, then immediately try to sell your blueprints to the Crown. "
                              "Overboard they go.")),
            ]),
        ]),
    dict(id='lighthouse', text=(
        "A lighthouse keeper rows out to meet you. 'Haven't seen a soul in eleven years,' he says. "
        "'Want to hear about my rock collection?'"),
        choices=[
            dict(text="Listen to the whole thing.", out=dict(
                text="It takes six hours. Some of the rocks are, admittedly, very good rocks. "
                     "He gives you his favourite and some supplies.", fleet=25, doubloons=20, rum=2)),
            dict(text="Ask him to shine his light at the Armada.", out=dict(
                text="He swings the great lamp around and blinds an entire Armada squadron. 'Eleven years "
                     "I've waited to do that,' he says quietly.", fleet=-40)),
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
        "A fishing boat is sinking. A Royal Revenue cutter circles it, demanding tax on the water it's "
        "taking on."),
        choices=[
            dict(text="Rescue the fishermen!", out=dict(
                text="Battle stations!", fight='revenue',
                win=dict(text="One of the grateful fishermen joins the rebellion.", add_crew='random'))),
            dict(text="Pretend you didn't see.", out=dict(
                text="Everyone saw you pretend. Morale dips. So, slightly, does your self-respect.")),
        ]),
    dict(id='flare', text=(
        "A red flare arcs over the water from a small, sad-looking ketch."),
        choices=[
            dict(text="Investigate.", outs=[
                (5, dict(text="It's a rebel supply drop, left by sympathisers! Long live the sardine!",
                         balls=3, rum=3, hull=4)),
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
    "A {enemy} cuts across your bow. Their captain yells something about your 'outstanding fish licence'.",
    "{enemy_name}, a {enemy}, swings alongside. Someone over there is already laughing at your ship.",
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


def armada_event():
    return dict(id='armada', text=(
        "The Royal Armada has caught up with you! A frigate in gleaming white and gold swings its broadside "
        "toward you while a brass band on its deck plays something smug."),
        choices=[
            dict(text="Fight for freedom!", out=dict(fight='frigate')),
            dict(text="Offer a bribe. (40 doubloons)", req=dict(doubloons=40), outs=[
                (5, dict(text="The captain pockets it and looks the other way. Corruption! Finally, something "
                              "on your side.", doubloons=-40)),
                (5, dict(text="He pockets it, arrests the bribe for corrupting an officer, then attacks you.",
                         doubloons=-40, fight='frigate')),
            ]),
        ])


def exit_event(sector, nxt):
    if sector.final:
        return dict(id='finale', title='HMS Insufferable', text=(
            "There she is. HMS Insufferable: four decks, nine hundred guns (allegedly), a ballroom, two "
            "string quartets and a gift shop. She is so large she has her own weather.\n\n"
            "On the quarterdeck, Admiral Lord Percival Crumpet-Smythe lowers his teacup. "
            "'The sardine rebels? Here? How frightfully common. Sink them, and do it before the scones go cold.'"),
            choices=[dict(text="Sink the Insufferable! (Final battle)", out=dict(fight='boss', boss=True)),
                     dict(text="Not yet. Let me prepare.", out=dict())])
    return dict(id='exit', text=(
        "You reach the edge of {sector}. Beyond lies {next}.\n\nOnce you leave, there's no coming back."),
        choices=[dict(text="Set sail for {next}.", out=dict(exit=True)),
                 dict(text="Stay a little longer.", out=dict())])
