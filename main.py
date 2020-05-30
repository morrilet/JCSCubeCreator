import time
import requests

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


def getCardsOfColors(colors, cards):
    """
    Get a list of cards with the given colors exactly.

    :colors: A list of strings describing the desired color identity.
    :cards: A list of card objects to search.
    :returns: A list of cards objects with the given color identity.
    """

    return list(filter(lambda card: set(card['color']).issuperset(colors), cards))



