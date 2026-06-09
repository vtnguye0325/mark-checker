"""Regression tests: 50 correct predictions from predictions.csv.

Each case is (formatted_input, expected_label). To add or remove cases,
edit the CASES list below.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.model_service import predict_one

CASES: list[tuple[str, str]] = [
    (
        "FABFIT. yoga blocks yoga boards yoga cushions yoga gloves yoga straps athletic sporting goods namely adhesive tape for hockey stick and uniform support athletic sporting goods namely athletic wrist and joint supports fitness equipment namely straps used for yoga and other fitness activities and for carrying a yoga mat physical fitness equipment namely resistance bands weighted vests. FABFITFUN. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. Pseudo mark is fab fit fabulous fit",
        "distinctive",
    ),
    (
        "MUXSAM. covers for golf clubs golf accessories namely carriers and dispensers for golf balls golf accessories namely holders specially adapted for holding golf ball markers golf accessory pouches golf accessory namely support for holding a golf club golf bag straps golf bags with or without wheels golf ball markers golf ball sleeves golf balls golf club heads golf divot repair tools golf gloves golf practice nets golf putter covers golf tee bags golf tee markers golf tees golf training equipment namely a golf training cage golf training equipment namely a motorized golf chipping practice aid grip tape for golf clubs grip tape for tennis rackets hand grips for golf clubs head covers for golf clubs putting practice mats weights for attachment to golf clubs for use as a golf swing aid the wording muxsam has no meaning in a foreign language. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "BEELEARNERS. childrens educational toys for developing fine motor science mathematics and language. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. Pseudo mark is bee learners",
        "distinctive",
    ),
    (
        "BALLISTIC GOLF. golf golf clubs. no translation required. mark present in Wordnet. mark length is 2. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "SMACKSTACK. craps game playing equipment. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. Pseudo mark is smack and stack",
        "distinctive",
    ),
    (
        "PROSPERO HALL. board games card games dice games parlor games party games tabletop games equipment sold as a unit for playing board games the english translation of the word prospero in the mark is prosperous. no translation required. mark present in Wordnet. mark length is 2. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "BIG CHUNGUS. board games. no translation required. mark present in Wordnet. mark length is 2. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "MARVELOUS MONKEY. color is not claimed as a feature of the mark the mark consists of the stylized wording marvelous monkey bodytraining apparatus chess games game apparatus namely bases bats and balls for playing indoor and outdoor games jigsaw puzzles plush toys rods for fishing toy masks toy vehicles toys for domestic pets smart robot toys. no translation required. mark present in Wordnet. mark length is 2. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "IBALL. apparatus for electronic games other than those adapted for use with an external display screen or monitor handheld units in the shape of a ball for playing electronic games in the nature of devices that display and play prerecorded messages. BALL. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. Pseudo mark is i ball",
        "distinctive",
    ),
    (
        "TATE. color is not claimed as a feature of the mark the mark consists of stylized wording of the mark tate in lower case font fishing rods fishing rod handles fishing tools the names portraits andor signatures shown in the mark identifies trent s tate whose consents to register is made of record. no translation required. mark present in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "FORLRFIT. ankle weights chest developers dumbbells exercise balls gymnastics rings jump ropes weight lifting gloves yoga blocks yoga straps the wording forlrfit has no meaning in a foreign language. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "INFINE MANNO. color is not claimed as a feature of the mark the mark consists of thestylizedwording infine manno balls for games chess games climbers harness exercise equipment namely chest pulls exercise balls fishing tackle flying discs jump ropes knee guards for athletic use smart robot toys swimming rings toy masks toys for domestic pets waist protectors for athletic use wrist guards for athletic use the english translation of the word infine in the mark is finally. FINALLY MANNO. mark absent in Wordnet. mark length is 2. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "PAWSOME PETS. pets cat toys dog toys pet toys. no translation required. mark present in Wordnet. mark length is 2. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "PADDY PALS. dog toys doll clothing doll costumes dolls clothes dolls pet toys plush dolls plush toys stuffed toy animals stuffed toy bears teddy bears toy for pets stuffed and plush toys. no translation required. mark present in Wordnet. mark length is 2. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "SIKAYE. dolls houses fishing tackle flying discs jigsaw puzzles parlor games radiocontrolled toy vehicles scalemodel vehicles smart robot toys toy drones toy vehicles toy building blocks toy for pets the names portraits andor signatures shown in the mark does not identify a particular living individual the wording sikaye has no meaning in a foreign language. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "LAPECHE. color is not claimed as a feature of the mark the mark consists of the stylized wordinglapeche bath toys cat toys construction toys doll clothing dolls electric action toys electronic learning toys fishing tackle inflatable rideon toys matryoshka dolls musical toys novelty noisemaker toys for parties play motor cars plush toys teddy bears. FISHING. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "BARAIDA. decorative toy mobiles and plush toys for children made of felt gift baskets containing plush toys novelty plush toys for parties novelty toy items in the nature of artificial plush animal tails plush toys stuffed and plush toys the wording baraida has no meaning in a foreign language. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "NUEVERA. color is not claimed as a feature of the mark the mark consists of the wording nuevera in stylized font ascenders being mountaineering equipment field hockey gloves fishing tackle fitness equipment namely straps used for yoga and other fitness activities and for carrying a yoga mat golf training equipment namely a golf training cage hand pads for athletic use handle grips for sporting equipment harnesses specially adapted for carrying snowboards skis and skateboards manual leg exercisers manuallyoperated exercise equipment for physical fitness purposes mountaineering equipment namely hook and ring combinations muscle training braces to be worn on the back for support when playing sports pet toys ski bindings and parts therefor skis swimming equipment namely racing lanes wrist guards for athletic use yoga cushions yoga gloves yoga straps the wording nuevera has no meaning in a foreign language. NINE. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "KLOBROZ. board games cases for toy vehicles childrens educational toys for developing fine motor oral language numbers counting colors and alphabet skills sold in a fabric bag which has a clear vinyl window for viewing small trinkets and toys securely contained within the bag itself construction toys costume masks crib toys dolls and accessories therefor electric action toys electronic novelty toys namely toys that electronically record play back and distort or manipulate voices and sounds finger puppets fishing lure parts memory games pet toys role playing toys in the nature of play sets for children to imitate real life occupations squeeze toys toy cars toy imitation cosmetics toy jewelry toy tools water toys the wording klobroz has no meaning in a foreign language. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "SIMIC. card games playing card game accessories namely playing card cases playing card holders mats for use in connection with playing card games playing cards and card games trading card games. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "AGETASTIC. board games. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "GYMAX. fitness machines and equipment namely weights treadmills rowing machines stair stepping machines resistance machines stationary cycles fitness equipment namely straps used for yoga and other fitness activities and for carrying a yoga mat exercise equipment in the nature of straps that are affixed to doors cable machines exercise equipment for performance of weight resistance exercises yoga straps balance boards for improving strength toning conditioning balance and proprioception yoga blocks stress relief exercise balls exercise equipment namely abdominal boards physical fitness equipment namely exercise bands training bars dumbbells fitness equipment namely a weighted bar to improve posture and overall fitness sporting goods and equipment for speed training namely rings cones speed ladders coaching sticks training arches ankle bands resistance chutes hurdles sports equipment for boxing and martial arts namely boxing gloves mixed martial arts gloves punching mitts and shin guards sports equipment for boxing and martial arts namely boxing gloves boxing bags punching mitts belly protectors groin protectors and shin guards physical fitness equipment namely resistance bands waist trimmer exercise belts weightlifting belts. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "SAY IT AGAIN GAME. game game cards parlor games card games memory games party games. no translation required. mark present in Wordnet. mark length is 4. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "BIRDIE MAKER. golf putting mats. no translation required. mark present in Wordnet. mark length is 2. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "CRIMSON TALON. crimson hunting broadhead arrow point. no translation required. mark present in Wordnet. mark length is 2. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "MODEL O. model gaming mice gaming mouse products namely gaming mice usb computer gaming mouse. no translation required. mark present in Wordnet. mark length is 2. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "CTRL SPORTS. sport fitness equipment namely straps used for yoga and other fitness activities and for carrying a yoga mat the wording ctrl sports has no meaning in a foreign language. no translation required. mark present in Wordnet. mark length is 2. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "K E SWEETS. sweets paper party favors. no translation required. mark present in Wordnet. mark length is 3. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. Pseudo mark is k and e sweets",
        "distinctive",
    ),
    (
        "VUSNUD. bath toys checkers chess pieces childrens educational toys for developing fine motor oral language numbers counting colors and alphabet skills sold in a fabric bag which has a clear vinyl window for viewing small trinkets and toys securely contained within the bag itself childrens multiple activity toys christmas tree ornaments and decorations dolls electric action toys inflatable toys paddle ball games pet toys stuffed and plush toys tabletop games the wording vusnud has no meaning in a foreign language. SATISFYED. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "TESORO. color is not claimed as a feature of the mark the mark consists of the stylized wording tesoro aerobic step machines exercising equipment namely powered treadmills for running hang gliders roller skates skateboards stationary exercise bicycles toy vehicles waist protectors for athletic use bodybuilding apparatus manuallyoperated exercise equipment for physical fitness purposes the english translation of tesoro in the mark is treasure. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "CHAOFAN. badminton sets badminton shuttlecocks bags specially adapted for padel rackets ball pitching machines balls for sports bath toys bats for games billiard markers bodybuilding apparatus bodytraining apparatus bowling apparatus and machinery boxing gloves climbers harness divot repair tool for golfers exercise equipment namely exercise bands training bars rowing machines fishing tackle golf bags with or without wheels grip tape for golf clubs tennis rackets grip tape for sports nets for sports party blowouts party favor hats pet toys pet toys containing catnip pet toys made of rope protective covers for rackets pumps specially adapted for use with balls for games racket cases sports training apparatus namely pitching machines sports training apparatus namely ball return machines sports training apparatus namely soft toss pitching machines storage racks for athletic training equipment table tennis rackets table tennis tables table tennis post sets table tennis rebound board tennis ball throwing apparatus tennis nets toy cars toy figures toy masks toy telescopes toy watches badminton rackets baseball gloves batting gloves bite sensors conical paper party hats elbow guards for athletic use handheld party poppers knee guards for athletic use paper party hats parlor games parlour games plastic party hats shuttlecocks for badminton squash rackets tennis rackets toy for pets toys for domestic pets workout gloves. Chao fan. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. Pseudo mark is chao fan",
        "distinctive",
    ),
    (
        "GUNAT. building games dolls houses dolls jigsaw puzzles kite reels kites parlor games play balloons toy building blocks toy cars toy drones toy robots toy tools toy vehicles controllers for toy cars planes plush toys radiocontrolled toy vehicles smart electronic toy vehicles stuffed toys the english translation of gunat in the mark is gunt. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "AMERICAN HORROR RIDES. rides toy cars toy vehicle track sets and roadways and accessories therefor toy vehicles toy vehicles and accessories therefor toy vehicles with transforming parts toy building structures and toy vehicle tracks toy model cars toy model vehicles and related accessories sold as units toy model kit cars cases for toy vehicles electronic toy vehicles model toy vehicles nonelectronic toy vehicles radio controlled toy vehicles radiocontrolled toy vehicles rideable toy vehicles. no translation required. mark present in Wordnet. mark length is 3. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "AYWEWII. climbers harness darts flying discs novelty toys for playing jokes paper party favors pet toys play swimming pools scent lures for hunting or fishing stuffed toys swimming rings toy building blocks toy models toy robots toy scooters toy vehicles the wording aywewii has no meaning in a foreign language. GRANDMOTHER. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "LQYOYZ. bubble making wand and solution sets carnival masks christmas tree ornaments gyroscopes and flight stabilizers for model aircraft jigsaw puzzles novelty noisemaker toys for parties novelty toys for playing jokes parlour games pet toys piatas remote controls for toy cars planes smart robot toys stuffed toys toy aircraft toy cars toy drones toy figures toy masks toy robots toy vehicles the wording lqyoyz has no meaning in a foreign language. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "SHINSHIN CREATION. creation toy beads toy fuse beads toy bead sets consisting of toy beads glow in the dark toy beads peg boards fittings and a bucket hobby craft toy beads for making fused toy bead designs hobby craft toy bead sets for making fused toy bead designs comprising toy fuse beads pegboards ironing paper and storage case toy bead kit namely toy fuse bead kit including toy fuse beads and peg boards hobby craft kit for making toy fused bead designs comprising toy fuse beads creative patterns with instructions and pegboards the name shinshin does not identify a living individual the wording shinshin has no meaning in a foreign language. Mind and body C rare ground temperature. mark present in Wordnet. mark length is 2. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "CARYMADE. golf accessory pouches golf ball sleeves golf balls golf club bags golf club covers golf club grips golf club heads golf club shafts golf clubs golf gloves golf irons golf putter covers golf putters golf training apparatus namely golf practice platforms head covers for golf clubs. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. Pseudo mark is cary made",
        "distinctive",
    ),
    (
        "KXIN. carnival masks kaleidoscopes novelty noisemaker toys for parties toy christmas trees toy clocks and watches toy masks toy robots windsurfing gloves the wording kxin has no meaning in a foreign language. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "THE DEER SUPPLY COMPANY. company scent eliminating sprays for use during hunting and outdoor recreation. no translation required. mark present in Wordnet. mark length is 4. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "not_distinctive",
    ),
    (
        "RABBOTT. childrens educational games being responsibility charts for developing fine motor social cognitive critical thinking strategy and counting skills. RIBBON. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. Pseudo mark is rabbit",
        "distinctive",
    ),
    (
        "AVANI DOLL. color is not claimed as a feature of the mark doll the mark consists of the wording avani doll in stylized format dolls beds dolls clothes dolls feeding bottles dolls plush toys plush toys with attached comfort blanket stuffed toys teddy bears toy figures toy mobiles the english translation of avani in the mark is earth. avni doll. mark present in Wordnet. mark length is 2. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "TEAISIY. color is not claimed as a feature of the mark the mark consists of the stylized wording teaisiy bath toys drawing toys electronic action toys electronic learning toys electronic toy vehicles flying discs model toy vehicles plastic character toys play balloons radio controlled toy vehicles remotecontrolled toy vehicles toy building blocks toy masks toy robots toy telescopes toy watches toys with led light features for use in performance arts namely dance the wording teaisiy has no meaning in a foreign language. tassia. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "GGIENRUI. elbow guards for athletic use fishing tackle jigsaw puzzles knee guards for athletic use novelty noisemaker toys for parties parlor games smart robot toys toy building blocks toy cameras toy models toy telescopes toy vehicles toy for pets wrist guards for athletic use christmas tree ornaments and decorations the wording ggienrui has no meaning in a foreign language. GG IE NR UI. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "HOWSTART. electronic action toys electronic learning toys electronic novelty toys namely toys that electronically record play back and distort or manipulate voices and sounds infant toys novelty toys for playing jokes plastic character toys play money stuffed and plush toys toy building blocks toy robots toy tools toy vehicles water toys. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. Pseudo mark is how start",
        "distinctive",
    ),
    (
        "SUPERWINKY. color is not claimed as a feature of the mark bath toys drawing toys electronic action toys electronic learning toys electronic toy vehicles flying discs model toy vehicles plastic character toys play balloons radio controlled toy vehicles remotecontrolled toy vehicles toy building blocks toy masks toy robots toy telescopes toy watches toys with led light features for use in performance arts namely dance. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. Pseudo mark is super winky",
        "distinctive",
    ),
    (
        "QUKADARK. christmas tree decorations dolls jigsaw puzzles marionettes novelty toys for playing jokes parlor games party favors in the nature of small toys plush toys puppets smart robot toys snow globes toy fireworks toy cars toy for pets toy robots toy vehicles artificial snow for christmas trees bells for christmas trees building games candle holders for christmas trees carnival masks christmas tree stands christmas trees of synthetic material parlour games remotecontrolled toy vehicles toy building blocks toy drones the wording qukadark has no meaning in a foreign language. KUKADARK. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "SUGAR STACKS. gaming machines with or without video output which accept a wager reconfigurable casino and lottery gaming equipment namely gaming machines and operational game software therefor sold as a unit a feature of gaming machines namely gaming devices which accept a wager gaming software sold as an integral part of electronic gaming machines. no translation required. mark present in Wordnet. mark length is 2. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "VELOCORE. golf club shafts. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "PUPPY CONES. puppy plastic character toys plush toys. no translation required. mark present in Wordnet. mark length is 2. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. no Pseudo mark",
        "distinctive",
    ),
    (
        "COZYCRAFT. hobby craft kits for making ornaments comprising wood paint brushes acrylic paints twine and magnets. no translation required. mark absent in Wordnet. mark length is 1. NICE category is 28. games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees. Pseudo mark is cozy craft",
        "distinctive",
    ),
]


@pytest.mark.parametrize(
    "formatted_input,expected_label",
    CASES,
    ids=[c[0].split(". ")[0] for c in CASES],
)
def test_prediction(formatted_input: str, expected_label: str) -> None:
    result = predict_one(formatted_input)
    assert result["label"] == expected_label
