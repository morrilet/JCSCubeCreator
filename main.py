import time
import requests
import random

def fetchCards():
    """
    Fetch and format card data from the scryfall API while respecting rate limits.

    :returns: A list of formatted card objects.
    """

    raw_cards = []
    
    # Perform the initial request.
    url = 'https://api.scryfall.com/cards/search'
    params = {
        'q': 'legal:standard legal:pioneer legal:modern legal:vintage (rarity:c OR rarity:u OR rarity:r) usd<=0.25'
    }
    request = requests.get(url, params)
    data = request.json()
    raw_cards += data['data']

    # Call the API again until we've got all the cards we need.
    while(data['has_more']):
        time.sleep(0.100)  # Sleep for 100ms so we don't overload the API

        request = requests.get(data['next_page'])
        data = request.json()
        raw_cards += data['data']

    return __formatRawCards(raw_cards)


def __formatRawCards(raw_cards):
    """
    Strip away extra data from the given card objects and leaves only the fields we care about.

    :raw_cards: A list of card objects.
    :returns: A list of card objects.
    """

    cards = []
    for card in raw_cards:
        cards.append({
            'name': card['name'],
            'colors': card['colors'],
            'rarity': card['rarity'],
        })
    return cards


def getCardsOfRarity(rarity, cards):
    """
    Get a list of cards with the given rarity.

    :rarity: A string describing the desired rarity.
    :cards: A list of card objects to search.
    :returns: A list of cards objects with the given rarity.
    """

    return list(filter(lambda card: card['rarity'] == rarity, cards))


def getCardsOfColors(colors, cards, exact=True):
    """
    Get a list of cards with the given colors exactly.

    :colors: A list of strings describing the desired color identity.
    :cards: A list of card objects to search.
    :returns: A list of cards objects with the given color identity.
    """
    if exact:
        return list(filter(lambda card: set(card['colors']) == set(colors), cards))
    else:
        return list(filter(lambda card: set(card['colors']).issuperset(colors), cards))

def createCube(cards):
    """
    Creates desired cube from "cards" list.

    :cards: list of cards from which cube is created.

    """

    c = 'common'
    u = 'uncommon'
    r = 'rare'

    random.shuffle(cards)

    whiteCards = getCardsOfColors(['W'], cards)
    blueCards = getCardsOfColors(['U'], cards)
    blackCards = getCardsOfColors(['B'], cards)
    redCards = getCardsOfColors(['R'], cards)
    greenCards = getCardsOfColors(['G'], cards)
    #multiCards = getCardsOfColors(??, cards)
    #colorless = getCardsOfColors(??, cards)

    whiteCommons = getCardsOfRarity(c, whiteCards)[:50]
    blueCommons = getCardsOfRarity(c, blueCards)[:51]
    blackCommons = getCardsOfRarity(c, blackCards)[:50]
    redCommons = getCardsOfRarity(c, redCards)[:51]
    greenCommons = getCardsOfRarity(c, greenCards)[:50]
    #multiCommons = getCardsOfRarity(c, multiCards)[:32]
    #colorlessCommons = getCardsOfRarity(c, multiCards)[:32]

    whiteUncommons = getCardsOfRarity(u, whiteCards)[:13]
    blueUncommons = getCardsOfRarity(u, blueCards)[:12]
    blackUncommons = getCardsOfRarity(u, blackCards)[:13]
    redUncommons = getCardsOfRarity(u, redCards)[:13]
    greenUncommons = getCardsOfRarity(u, greenCards)[:13]
    # multiUncommons = getCardsOfRarity(u, multiCards)[:8]
    # colorlessUncommons = getCardsOfRarity(u, multiCards)[:8]

    blueRares = getCardsOfRarity(r, blueCards)[:1]
    blackRares = getCardsOfRarity(r, blackCards)[:1]
    redRares = getCardsOfRarity(r, redCards)[:1]
    greenRares = getCardsOfRarity(r, greenCards)[:1]

    commons = whiteCommons + blueCommons + blackCommons + redCommons + greenCommons  # + multiCommons + colorlessCommons
    uncommons = whiteUncommons + blueUncommons + blackUncommons + redUncommons + greenUncommons  # + multiUncommons + colorlessUncommons
    rares = whiteCards + blueRares + blackRares + redRares + greenRares  # + multiRares + colorlessRares

    return commons + uncommons + rares
