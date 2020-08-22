import sys
import math
import time
import requests
import random
import logging

CONSOLE_LOG = logging.StreamHandler()
CONSOLE_LOG.setLevel(logging.DEBUG)

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
LOG.addHandler(CONSOLE_LOG)

TOTAL_CUBE_SIZE = 400  # How many cards in the final cube.

# SCRYFALL_FILTER = 'legal:standard legal:pioneer legal:modern legal:vintage (rarity:c OR rarity:u OR rarity:r) usd<=0.25'
SCRYFALL_FILTER = 'usd<=0.50 f:legacy (rarity:c OR rarity:u OR rarity:r)'
SCRYFALL_PAGE_SIZE = 175

ADVENTURE = 'adventure'
TRANSFORM = 'transform'

MYTHIC = 'mythic'
RARE = 'rare'
UNCOMMON = 'uncommon'
COMMON = 'common'

STANDARD = 'standard'
PIONEER = 'pioneer'
MODERN = 'modern'
VINTAGE = 'vintage'

WHITE = 'W'
BLUE = 'U'
BLACK = 'B'
RED = 'R'
GREEN = 'G'
GOLD = 'MULTI'
COLORLESS = 'NONE'

CUBE_COLOR_WEIGHTS = {
    WHITE: 1,
    BLUE: 1,
    BLACK: 1,
    RED: 1,
    GREEN: 1,
    GOLD: 0.2,
    COLORLESS: 0.1,
}

DUPLICATION_CHANCES = {
    RARE: 0.01,
    UNCOMMON: 0.20,
    COMMON: 0.75,
}

DUPLICATION_LIMITS = {
    STANDARD: 3,
    PIONEER: 2,
    MODERN: 1,
    VINTAGE: 0
}


def __fetchCards():
    """
    Fetch and format card data from the scryfall API while respecting rate limits.

    :returns: A list of formatted card objects.
    """
    LOG.info('Fetching cards...')

    raw_cards = []
    
    # Perform the initial request.
    url = 'https://api.scryfall.com/cards/search'
    params = { 'q': SCRYFALL_FILTER }
    request = requests.get(url, params)
    data = request.json()
    raw_cards += data['data']

    page_count = math.ceil(data['total_cards'] / SCRYFALL_PAGE_SIZE)
    current_page = 1
    LOG.info(f'    Got page: {current_page} / {page_count}')

    # Call the API again until we've got all the cards we need.
    while(data['has_more']):
        time.sleep(0.100)  # Sleep for 100ms so we don't overload the API

        request = requests.get(data['next_page'])
        data = request.json()
        raw_cards += data['data']
        
        current_page += 1
        LOG.info(f'    Got page: {current_page} / {page_count}')

    LOG.info(f'Fetching cards: DONE')

    return __formatRawCards(raw_cards)


def __formatRawCards(raw_cards):
    """
    Strip away extra data from the given card objects and leaves only the fields we care about.

    :raw_cards: A list of card objects.
    :returns: A list of card objects.
    """

    cards = []
    for card in raw_cards:

        # Transform cards split 'colors' into 'card_faces' so we want 'color_identity' instead in that case.
        colors_key = 'colors'
        if card['layout'] == TRANSFORM:
            colors_key = 'color_identity'

        cards.append({
            'name': card['name'],
            'colors': card[colors_key],
            'rarity': card['rarity'],
            'legalities': [k for k, v in card['legalities'].items() if v == 'legal'],
            'layout': card['layout'],
        })
    return cards


def __getFormattedLegality(legalities):
    """
    Transform the list of legalities a card has into a single legality representing the most restrictive
    legality the card has. 

    Ex: ['standard', 'modern', 'legacy'] -> 'standard'
    """
    if STANDARD in legalities:
        return STANDARD
    elif PIONEER in legalities:
        return PIONEER
    elif MODERN in legalities:
        return MODERN
    else:
        return VINTAGE


def __getCardCounts():
    """
    Get an object containing count information for each color and rarity.

    Format: {'white': {'rare': 1, 'uncommon': 6, 'common': 62}, ...}
    """
    rarities = __getRarityCounts()
    output = {color: {RARE: 0, UNCOMMON: 0, COMMON: 0} for color in CUBE_COLOR_WEIGHTS}
    
    for rarity in [RARE, UNCOMMON, COMMON]:
        color_choices = random.choices(
            [color for color in CUBE_COLOR_WEIGHTS], 
            weights=[weight for weight in CUBE_COLOR_WEIGHTS.values()], 
            k=rarities[rarity]
        )

        for color in color_choices:
            output[color][rarity] += 1

    return output


def __getRarityCounts():
    """
    Get the number of cards belonging to each rarity that we want in the cube.
    """

    rare_count =  math.floor(TOTAL_CUBE_SIZE * 0.01)  # 1% rares.
    uncommon_count = math.floor(TOTAL_CUBE_SIZE * 0.20)  # 20% uncommons.
    common_count = TOTAL_CUBE_SIZE - rare_count - uncommon_count  # ~79% commons ('all remaining' to handle rounding with floor().)

    return {
        RARE: rare_count,
        UNCOMMON: uncommon_count,
        COMMON: common_count
    }
    

def __getCardsOfRarity(rarity, cards):
    """
    Get a list of cards with the given rarity.

    :rarity: A string describing the desired rarity.
    :cards: A list of card objects to search.
    :returns: A list of cards objects with the given rarity.
    """
    return list(filter(lambda card: card['rarity'] == rarity, cards))


def __getCardsOfColor(color, cards):
    """
    Get a list of cards of the given color.

    :color: A string representing the color to search for.
    :cards: A list of card objects.
    :returns: A list of card objects of the given color.
    """

    if color == GOLD:
        return list(filter(lambda card: len(card['colors']) > 1, cards))
    if color == COLORLESS:
        return list(filter(lambda card: len(card['colors']) == 0, cards))
    else:
        return list(filter(lambda card: set(card['colors']) == set(color), cards))


def __addDuplicates(cards):
    """
    Add duplicates to the card pool.

    :cards: A list of card objects to search.
    :returns: A list of card objects with random duplicates.
    """ 
    duplicates = []

    for card in cards:
        rarity = card['rarity']
        legality = __getFormattedLegality(card['legalities'])

        # Skip if duplication chance is 0.
        if rarity in DUPLICATION_CHANCES and DUPLICATION_CHANCES[rarity] != 0:
            # While random number <= duplication chance and we haven't hit the duplication limit for the card, slap on some duplicates!
            while(
                DUPLICATION_CHANCES[rarity] >= random.uniform(0, 1) 
                and duplicates.count(card) < DUPLICATION_LIMITS[legality]
            ):
                duplicates.append(card)

    return cards + duplicates
            

def __createCube(cards):    
    """
    Creates desired cube from "cards" list. Also handles multi-colored and colorless cards.

    :cards: list of cards from which cube is created.
    """
    cube = []
    cards_with_dupes = __addDuplicates(cards)
    random.shuffle(cards_with_dupes)
    card_counts = __getCardCounts()

    for color in card_counts:
        cards_of_color = __getCardsOfColor(color, cards_with_dupes)
        for rarity, count in card_counts[color].items():
            cube += __getCardsOfRarity(rarity, cards_of_color)[:count]

    return cube


def __outputCube(cards, filename):
    """
    Takes a list of cards and a file name, and outputs a file containing the card names
    """
    with open(filename, "a") as file:
        for card in cards:
            card_name = card['name']

            # Adventure cards should not use the split ('//') syntax for TappedOut imports.
            if card['layout'] in [ADVENTURE, TRANSFORM]:
                card_name = card_name.split(' // ')[0]
            
            file.write(f"{card_name}\n")


def generateNewCube(filename):
    cards = __fetchCards()
    cube = __createCube(cards)
    __outputCube(cube, filename)
