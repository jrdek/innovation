from typing import List, Generator
from lark import Lark, Transformer
from structs import *
from dogma_ir import DogmaTransformer
from utils.lark_utils import find_unused_rules
import os

def clear_terminal():
    os.system('clear||cls')


"""
The CardStore has a few responsibilities:
- On initialization, parse and build IR trees for every card in the specified file.
- Expose an interface for games to access cards.
(Eventually, it would be nice to more concretely make this a lookup table; this way
GameStates can store IDs instead of full cards.)
"""
class CardStore:
    def __init__(self, paths: Sequence[str]):
        self._index_to_card: Dict[CardId, Card] = {}  # (basically an array of Cards)
        self._name_to_index: Dict[str, CardId] = {}  # enable quick card lookup by name

        clear_terminal()  # TODO: this is just for debugging, remove eventually
        for path in paths:
            total_cards = len(self._index_to_card)
            path_cards: List[Card] = self.populate_cards(path)
            num_path_cards = len(path_cards)
            print(f"Loaded {num_path_cards} cards from {path}.")
            for i, card in enumerate(path_cards):
                self._index_to_card[total_cards + i] = card
                self._name_to_index[card.name] = total_cards + i
        print(f"Total cards loaded: {len(self._index_to_card)}")


    def get(self, id: CardId | str) -> Card | CardId:
        if isinstance(id, CardId):
            return self._index_to_card[id]
        else:
            return self._name_to_index[id]


    # Given a path, load all cards from the path into a CardStore.
    def populate_cards(self, path: str):
        # open the card file
        with open(path) as f:
            cards_txt = f.read()
        
        # parse all cards therein
        parser = Lark.open("grammars/deffect_grammar.lark", start="cards")
        syntax_tree = parser.parse(cards_txt)

        # analyze the grammar vis-a-vis loaded cards
        # TODO: enable this via flag. maybe move elsewhere?
        #print(f'Unused rules: {find_unused_rules(tree, ("grammars/common", "grammars/deffect_grammar"))}')
        #input("(press any key...)")

        # turn parse trees into Card objects
        ir_maker = DogmaTransformer()
        loaded_cards: List[Card] = []
        for i, card in enumerate(syntax_tree.children):
            #print(card.pretty())
            #print("-----\n")
            new_card = ir_maker.transform(card)
            # print(new_card.detailed_str())
            # input(f'(Cards shown: {i+1}/{len(syntax_tree.children)})')
            clear_terminal()
            loaded_cards.append(new_card)
        return loaded_cards


    """
    Output the contents of the CardStore into a tuple of decks (implemented as tuples of int indices).
    """
    def get_innovation_decks(self, names=None) -> List[List[int]]:
        NUM_DECKS = 11  # (there is an empty deck of age-0 cards)
        decks: List[List[int]] = [[] for _ in range(NUM_DECKS)]
        # if names is specified, only use selected cards
        # otherwise, use all cards
        selected_indices: Generator[int] = (self._name_to_index[name] for name in names) if names else range(len(self._index_to_card))
        for i in selected_indices:
            card = self._index_to_card[i]
            decks[card.age].append(i)
        return decks


"""
TODO here:
- almost certainly move the deck-build functionality into here
- --> given a list of card names, build decks containing only them in that order (or error if any aren't in the store)
"""



