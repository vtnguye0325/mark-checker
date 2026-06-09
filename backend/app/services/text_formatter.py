from __future__ import annotations

from functools import lru_cache

# NICE class descriptions extracted verbatim from nice_description_preprocessed
# in the training data (modern_bert/data/split/*.pkl).
NICE_DESCRIPTIONS: dict[int, str] = {
    1: "chemicals for use in industry science and photography as well as in agriculture horticulture and forestry unprocessed artificial resins unprocessed plastics fire extinguishing and fire prevention compositions tempering and soldering preparations substances for tanning animal skins and hides adhesives for use in industry putties and other paste fillers compost manures fertilizers biological preparations for use in industry and science",
    2: "paints varnishes lacquers preservatives against rust and against deterioration of wood colorants dyes inks for printing marking and engraving raw natural resins metals in foil and powder form for use in painting decorating printing and art",
    3: "nonmedicated cosmetics and toiletry preparations nonmedicated dentifrices perfumery essential oils bleaching preparations and other substances for laundry use cleaning polishing scouring and abrasive preparations",
    4: "industrial oils and greases wax lubricants dust absorbing wetting and binding compositions fuels and illuminants candles and wicks for lighting",
    5: "pharmaceuticals medical and veterinary preparations sanitary preparations for medical purposes dietetic food and substances adapted for medical or veterinary use food for babies dietary supplements for human beings and animals plasters materials for dressings material for stopping teeth dental wax disinfectants preparations for destroying vermin fungicides herbicides",
    6: "common metals and their alloys ores metal materials for building and construction transportable buildings of metal nonelectric cables and wires of common metal small items of metal hardware metal containers for storage or transport safes",
    7: "machines machine tools poweroperated tools motors and engines except for land vehicles machine coupling and transmission components except for land vehicles agricultural implements other than handoperated hand tools incubators for eggs automatic vending machines",
    8: "hand tools and implements handoperated cutlery side arms except firearms razors",
    9: "scientific research navigation surveying photographic cinematographic audiovisual optical weighing measuring signalling detecting testing inspecting lifesaving and teaching apparatus and instruments apparatus and instruments for conducting switching transforming accumulating regulating or controlling the distribution or use of electricity apparatus and instruments for recording transmitting reproducing or processing sound images or data recorded and downloadable media computer software blank digital or analogue recording and storage media mechanisms for coinoperated apparatus cash registers calculating devices computers and computer peripheral devices diving suits divers masks ear plugs for divers nose clips for divers and swimmers gloves for divers breathing apparatus for underwater swimming fireextinguishing apparatus",
    10: "surgical medical dental and veterinary apparatus and instruments artificial limbs eyes and teeth orthopaedic articles suture materials therapeutic and assistive devices adapted for persons with disabilities massage apparatus apparatus devices and articles for nursing infants sexual activity apparatus devices and articles",
    11: "apparatus and installations for lighting heating cooling steam generating cooking drying ventilating water supply and sanitary purposes",
    12: "vehicles apparatus for locomotion by land air or water",
    13: "firearms ammunition and projectiles explosives fireworks",
    14: "precious metals and their alloys jewellery precious and semiprecious stones horological and chronometric instruments",
    15: "musical instruments music stands and stands for musical instruments conductors batons",
    16: "paper and cardboard printed matter bookbinding material photographs stationery and office requisites except furniture adhesives for stationery or household purposes drawing materials and materials for artists paintbrushes instructional and teaching materials plastic sheets films and bags for wrapping and packaging printers type printing blocks",
    17: "unprocessed and semiprocessed rubber guttapercha gum asbestos mica and substitutes for all these materials plastics and resins in extruded form for use in manufacture packing stopping and insulating materials flexible pipes tubes and hoses not of metal",
    18: "leather and imitations of leather animal skins and hides luggage and carrying bags umbrellas and parasols walking sticks whips harness and saddlery collars leashes and clothing for animals",
    19: "materials not of metal for building and construction rigid pipes not of metal for building asphalt pitch tar and bitumen transportable buildings not of metal monuments not of metal",
    20: "furniture mirrors picture frames containers not of metal for storage or transport unworked or semiworked bone horn whalebone or motherofpearl shells meerschaum yellow amber",
    21: "household or kitchen utensils and containers cookware and tableware except forks knives and spoons combs and sponges brushes except paintbrushes brushmaking materials articles for cleaning purposes unworked or semiworked glass except building glass glassware porcelain and earthenware",
    22: "ropes and string nets tents and tarpaulins awnings of textile or synthetic materials sails sacks for the transport and storage of materials in bulk padding cushioning and stuffing materials except of paper cardboard rubber or plastics raw fibrous textile materials and substitutes therefor",
    23: "yarns and threads for textile use",
    24: "textiles and substitutes for textiles household linen curtains of textile or plastic",
    25: "clothing footwear headwear",
    26: "lace braid and embroidery and haberdashery ribbons and bows buttons hooks and eyes pins and needles artificial flowers hair decorations false hair",
    27: "carpets rugs mats and matting linoleum and other materials for covering existing floors wall hangings not of textile",
    28: "games toys and playthings video game apparatus gymnastic and sporting articles decorations for christmas trees",
    29: "meat fish poultry and game meat extracts preserved frozen dried and cooked fruits and vegetables jellies jams compotes eggs milk cheese butter yogurt and other milk products oils and fats for food",
    30: "coffee tea cocoa and substitutes therefor rice pasta and noodles tapioca and sago flour and preparations made from cereals bread pastries and confectionery chocolate ice cream sorbets and other edible ices sugar honey treacle yeast bakingpowder salt seasonings spices preserved herbs vinegar sauces and other condiments ice frozen water",
    31: "raw and unprocessed agricultural aquacultural horticultural and forestry products raw and unprocessed grains and seeds fresh fruits and vegetables fresh herbs natural plants and flowers bulbs seedlings and seeds for planting live animals foodstuffs and beverages for animals malt",
    32: "beers nonalcoholic beverages mineral and aerated waters fruit beverages and fruit juices syrups and other preparations for making nonalcoholic beverages",
    33: "alcoholic beverages except beers alcoholic preparations for making beverages",
    34: "tobacco and tobacco substitutes cigarettes and cigars electronic cigarettes and oral vaporizers for smokers smokers articles matches",
    35: "advertising business management organization and administration office functions",
    36: "financial monetary and banking services insurance services real estate affairs",
    37: "construction services installation and repair services mining extraction oil and gas drilling",
    38: "telecommunications services",
    39: "transport packaging and storage of goods travel arrangement",
    40: "treatment of materials recycling of waste and trash air purification and treatment of water printing services food and drink preservation",
    41: "education providing of training entertainment sporting and cultural activities",
    42: "scientific and technological services and research and design relating thereto industrial analysis industrial research and industrial design services quality control and authentication services design and development of computer hardware and software",
    43: "services for providing food and drink temporary accommodation",
    44: "medical services veterinary services hygienic and beauty care for human beings or animals agriculture aquaculture horticulture and forestry services",
    45: "legal services security services for the physical protection of tangible property and individuals personal and social services rendered by others to meet the needs of individuals",
}


def format_fields(
    mark: str,
    description: str,
    nice_class: int,
    translation: str = "",
    pseudo_mark: str = "",
) -> list[str]:
    """
    Build the eight ordered fields of the bert_input_processed representation.

    Field order (matches training):
      mark, description, translation, wordnet_flag, mark_length,
      nice_category, nice_description, pseudo_mark

    Joining these with '. ' yields the exact training-time string (see
    ``format_input``). Returning the parts lets callers that need per-field
    boundaries — e.g. leave-one-out attribution in ``model_service.explain_one``
    — avoid re-splitting the joined string on '. ', which is ambiguous because
    user-supplied fields (mark/description/translation/pseudo_mark) can
    themselves contain '. ' and would shift every field's alignment.

    Args:
        translation: Foreign-language translation of the mark. Leave empty if not applicable.
        pseudo_mark: Space-separated constituent words of a compound mark. Leave empty if not applicable.
    """
    mark = mark.strip()
    description = description.strip()

    return [
        mark,
        description,
        _translation(translation),
        _wordnet_flag(mark),
        f"mark length is {len(mark.split())}",
        f"NICE category is {nice_class}",
        NICE_DESCRIPTIONS.get(nice_class, ""),
        _pseudo_mark(pseudo_mark),
    ]


def format_input(
    mark: str,
    description: str,
    nice_class: int,
    translation: str = "",
    pseudo_mark: str = "",
) -> str:
    """Builds the bert_input_processed string matching training-time format."""
    return ". ".join(format_fields(mark, description, nice_class, translation, pseudo_mark))


def _translation(user_input: str) -> str:
    return user_input.strip() if user_input.strip() else "no translation required"


@lru_cache(maxsize=1)
def _wordnet():
    """Load the WordNet corpus reader once.

    The corpus is baked into the image at build time (see backend/Dockerfile and
    the NLTK_DATA env var) and is never downloaded at request time. A missing
    corpus is a deployment misconfiguration, not something to paper over: a
    silent "absent" default would corrupt the WordNet field of every prediction,
    so we fail loudly instead.
    """
    try:
        from nltk.corpus import wordnet as wn

        wn.synsets("test")  # force NLTK's lazy loader; LookupError if data absent
    except (LookupError, ImportError) as exc:
        raise RuntimeError(
            "WordNet corpus unavailable. It must be baked into the image at build "
            "time via NLTK_DATA (see backend/Dockerfile)."
        ) from exc
    return wn


def _wordnet_flag(mark: str) -> str:
    wn = _wordnet()
    found = any(bool(wn.synsets(tok)) for tok in mark.lower().split())
    return "mark present in Wordnet" if found else "mark absent in Wordnet"


def _pseudo_mark(user_input: str) -> str:
    # Empty input means there is no pseudo mark — do not attempt to derive one
    # from the mark itself.
    if user_input.strip():
        return f"Pseudo mark is {user_input.strip()}"
    return "no Pseudo mark"
