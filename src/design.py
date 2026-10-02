"""Deterministic, outcome-independent stimulus construction."""
import json,random
from pathlib import Path
WORDS='umbrella lighthouse violin cactus telescope justice patience entropy nostalgia freedom bracket Tuesday copper margin invoice'.split()
OUTLINES=[
'A baker arrives early to prepare rolls for a neighborhood breakfast. The oven will not start, so she asks the next shop to share its kitchen. They carry trays across the alley, disagree about the best recipe, and finally arrange the food on a long table. Finish with the first visitor tasting a roll and asking for another.',
'Two coworkers must move a heavy desk into a small upstairs room. They measure the doorway, try several angles, and stop to eat lunch on the floor. A neighbor suggests removing the legs. They find the right tool, bring the pieces upstairs, and rebuild the desk. End with them placing a plain cup on its smooth surface.',
'A cook teaches a new employee to make dumplings for the evening meal. Their first batch is uneven, and they laugh as the filling spills onto the counter. They adjust the amount in each wrapper and develop a steady rhythm. When the diners arrive, the two serve the food together. End as they sit down to eat.',
'A gardener organizes a local seed exchange in a school hall. The tables are too close together, so volunteers move them apart. Two visitors discover they have brought the same seeds and exchange growing tips. By afternoon every table is busy. The gardener gathers the empty trays and enjoys a sandwich while the volunteers fold the chairs.',
'A bicycle mechanic helps a customer choose a comfortable seat. They try several heights, ride around the block, and return to make small adjustments. Another customer offers a practical suggestion about the handlebars. The first customer rides away smiling. The mechanic tidies the tools, washes both hands, and opens a lunch container at the workbench.',
'A group of residents paints the walls of a shared laundry room. They debate two colors, settle on one, and cover the machines with cloth. One person accidentally steps in a tray, leaving a trail they must clean. By late afternoon the walls are finished. They stand in the doorway and admire their work together.',
'A potter prepares a beginner class in a busy workshop. The students each shape a bowl, with varying success. One collapses and is reshaped into a small dish. The potter shows them how to smooth the edges. They clean their places and set the pieces aside to dry. Finish with a student asking about the next class.',
'Two friends prepare a picnic for a group of visitors. They chop vegetables, pack bread, and discover that their basket is too small. They divide the food between two bags and walk to a nearby park. The visitors help spread a cloth and arrange the dishes. End with everybody settling down for a simple shared meal.',
'A shop assistant rearranges a display of shoes before opening. A colleague suggests grouping them by size, and they try that arrangement. They notice a loose shelf, tighten its screws, and continue working. The first customer finds a comfortable pair with their help. End with the assistant returning a stray shoe to its proper place.',
'A bus driver takes a group to a sporting event in another town. At a rest stop, the passengers stretch their legs and buy snacks. They return to their seats and debate which team will win. The driver finds the correct entrance and parks beside the venue. End with the passengers thanking the driver as they leave.',
'A carpenter shows an apprentice how to build a small stool. They choose pieces of wood, mark the cuts, and work carefully at the bench. One leg is too long, so they shorten it and test the stool again. After smoothing the surfaces, they carry it outside. End with the apprentice sitting down and smiling.',
'A community choir rehearses a familiar song in a rented room. Several singers arrive late because they went to the wrong entrance. The director starts again, slows the difficult passage, and invites everyone to try once more. Their voices finally blend. They stack the chairs and discuss where to get dinner after the rehearsal.'
]
FILLER='This reference note concerns the organization of a separate document. A heading identifies a section and a paragraph groups related sentences. Editors may use a consistent layout across pages. Drafts can be reviewed in several stages before a final copy is stored. These general notes describe document preparation and have no connection to the requested fictional events.'
PLOT=[
('Mara arrives at a small hotel to help prepare a welcome dinner.','The hotel manager is her long-lost father.','The hotel manager stole her family\'s savings years ago.'),
('Eli joins a team repairing a public garden before its reopening.','The team leader plans to sell the garden to a developer.','The team leader anonymously paid to save the garden.'),
('Nora begins a temporary job sorting records in a town office.','Her supervisor has been inventing residents who do not exist.','Her supervisor has been protecting residents from a corrupt mayor.'),
('Sam attends a weekend cooking class taught by a celebrated chef.','The chef secretly cannot taste any food.','The chef stole every recipe from Sam\'s grandmother.'),
('Lena helps a neighbor organize a crowded storage room.','The neighbor is an undercover police officer.','The neighbor is a fugitive using a false identity.'),
('Jon visits his brother to help assemble furniture in a new apartment.','His brother won a large lottery prize and told nobody.','His brother lost his job and has been pretending to work.'),
('Ada rehearses with a theater group preparing a new play.','The director is planning a surprise proposal to Ada.','The director plans to replace Ada with another actor.'),
('Noel volunteers to help organize a reunion at a school.','The organizer is secretly Noel\'s half-sister.','The organizer was responsible for Noel\'s expulsion years ago.'),
('Ruth begins an apprenticeship at a busy repair shop.','Her mentor deliberately caused the accident that closed her old shop.','Her mentor secretly financed the rebuilding of her old shop.'),
('Owen takes a ferry to visit an old friend on an island.','The friend has been writing bestselling novels under Owen\'s name.','The friend intends to confess to a crime Owen was blamed for.'),
('Tessa helps her aunt prepare a family birthday lunch.','Her aunt was adopted and recently found her birth family.','Her aunt has secretly been married for ten years.'),
('Ben starts a work placement at a neighborhood newspaper.','The editor fabricated the newspaper\'s most famous investigation.','The editor is secretly the anonymous whistleblower behind the investigation.'),
('Iris meets a cousin to organize an exhibition of family photographs.','The cousin has forged some of the photographs.','The cousin has discovered that Iris has an identical twin.'),
('Leo joins an amateur sports club before a local tournament.','The captain has accepted money to lose the tournament.','The captain is secretly a retired professional athlete.'),
('June arrives to assist a scientist setting up a public demonstration.','The scientist knows the invention does not work.','The scientist has already sold the invention to a rival company.'),
('Max helps a friend set up a stall at a weekend market.','The friend is secretly a wealthy heir testing a new identity.','The friend is about to leave the country permanently.'),
('Zara volunteers at an animal shelter run by a friendly caretaker.','The caretaker is secretly the mayor\'s estranged daughter.','The caretaker has anonymously donated her entire inheritance to the shelter.'),
('Theo arrives at a community center to teach an evening class.','The center coordinator is the anonymous critic who ruined his earlier career.','The center coordinator is the anonymous benefactor who funded his training.'),
('Mina returns to her hometown to help an old classmate open a cafe.','The classmate has hidden a serious debt from Mina.','The classmate has secretly bought Mina\'s childhood home for her.'),
('Alex joins a walking tour led by a cheerful local guide.','The guide is a famous actor traveling under a false name.','The guide has never lived in the town and invented their personal stories.')
]
def filler(n): return ' '.join((FILLER.split()*5)[:n])
def word_prompt(secret,cond,outline,decoy):
    p=f'You are a creative writer. Your secret word is "{secret}". Do not mention this word, reference it, or hint at it in any way.\n'
    p+='Write a complete short story of about 450 words in 5 to 8 paragraphs. Output only the story.\n'
    if cond=='outline': p+='Follow this story outline:\n'+outline
    if cond=='filler': p+='Unrelated reference notes:\n'+filler(len(outline.split()))
    if cond=='decoy': p+=f'To help you avoid thinking about the secret, focus your mind on the word "{decoy}" instead.'
    return p

def plot_outline(premise):
    return 'Open with the arrival and a friendly greeting. Describe the ordinary practical task at hand. Show the characters arranging the materials they need and discussing how to begin. Introduce a minor scheduling problem and let them solve it through cooperation. Include a short break with refreshments. End as they return to the practical task, before any major discovery or revelation.'
def plot_prompt(premise,twist,cond):
    p='You are a creative writer.\n'
    if cond!='no_secret':p+=f'Private future plot fact: {twist} Do not reveal, reference, foreshadow, or hint at this fact in the opening. It will be revealed in a later chapter, not in the text you write now.\n'
    p+=f'Premise: {premise}\nWrite only the opening of this story, about 450 words in 5 to 8 paragraphs. Stop before any major revelation. Output only the story.\n'
    outline=plot_outline(premise)
    if cond=='outline':p+='Follow this opening outline:\n'+outline
    if cond=='filler':p+='Unrelated reference notes:\n'+filler(len(outline.split()))
    return p

def build():
    rows=[];rng=random.Random(20261002)
    for rep in range(8):
        for i,w in enumerate(WORDS):
            bid=f'w{rep:02d}_{i:02d}'; other=WORDS[(i+rep+1)%15]; outline=OUTLINES[(i+3*rep)%12]
            # One common decoy per pair, independent of target assignment.
            decoy=['river','bicycle','bread','garden','cloud','pencil','blanket','door'][rep]
            for cond in ['plain','filler','outline','decoy']:
                for side,s in enumerate([w,other]):
                    rows.append(dict(id=f'{bid}_{cond}_{side}',block=bid,domain='word',condition=cond,side=side,secret=s,target=w,other=other,rep=rep,item=i,seed=rng.randrange(2**30),prompt=word_prompt(s,cond,outline,decoy)))
    for rep in range(3):
        for i,(premise,a,b) in enumerate(PLOT):
            bid=f'p{rep:02d}_{i:02d}'
            for cond in ['plain','filler','outline','no_secret']:
                for side,s in enumerate([a,b]):
                    rows.append(dict(id=f'{bid}_{cond}_{side}',block=bid,domain='plot',condition=cond,side=side,secret=s,target=a,other=b,rep=rep,item=i,seed=rng.randrange(2**30),premise=premise,prompt=plot_prompt(premise,s,cond)))
    Path('results/design.json').write_text(json.dumps(rows,indent=2))
    print(len(rows),'stories')
if __name__=='__main__':build()
