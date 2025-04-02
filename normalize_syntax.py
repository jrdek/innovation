from lark import Visitor

"""
In our tree, we want to interpret `stmts` objects.

One good approach to this is as follows:
1. Normalize the tree's nodes. For instance, `kind_of_card cards` and `kind_of_card card` are identical and should be collapsed.
2. Convert the tree to an IR. This may be a good place to deal with referents ('it', 'the same', etc).
3. Optionally optimize the IR. (This'll stay a TODO for a while, I expect)
4. Convert the IR to a function which takes a GameState, an "invoking player" ("me"), and a "target player" ("you"); and returns a new, resulting GameState.
"""

class NormalizeSyntax(Visitor):
    def general_zone(self, node):
        if "hand" in node.children[0]:
            node.children[0] = "hand"
        elif "score pile" in node.children[0]:
            node.children[0] = "score"
        elif "achievements" in node.children[0]:
            node.children[0] = "achievements"
        elif "board" in node.children[0]:
            node.children[0] = "board"
    
    def player_adj(self, node):
        # discard the flexibility in phrasing for later ease of parsing.
        # imagine the word "of" before these; we'll only include the person!
        # (that this is a "player_adj" suffices to know it's an adjective)
        if node.children[0] == "my":
            node.children[0] = "me"
        elif node.children[0] == "your":
            node.children[0] = "you"
        elif node.children[0] == "their":
            node.children[0] = "that player"
        elif node.children[0] in ("everyone's", "everyone else's", "anyone's", "anyone else's"):
            node.children[0] = node.children[0][:-2]  # just trim off the `'s`
        # specific players is either "someone's" or "someone s.t. <condition>'s".
        # but the rule cuts off the "'s" in both, so no edits needed.
    
    def value(self, node):
        if node.children[0] == "feature_of_card":
            ...
        elif node.children[0] == "any number of":
            ...
        elif node.children[0] == "the democracy record":
            ...
        elif node.children[0] == "player_adj":
            ...
        # "chosen" is fine
        elif node.children[0] == "#":
            ...  # do something to the `countable` if needed?? TODO
        elif node.children[-1] == "zone":
            ...  # x-est value in your zone
        else:
            print(node.children[0])
            assert node.children[0] == "value"
            # TODO: What if I want nodes to normalize themselves? Re-paradigm?
            # FIXME: this is crashing rn! 