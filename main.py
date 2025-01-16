

def main():
    import parse_cards

    cardfile = 'cards/base_game.cards'

    cards = parse_cards.from_file(cardfile)
    
    ages = [0 for _ in range(11)]

    for c in cards:
        ages[c.age] += 1
    
    for i in range(1, 11):
        print(f"Cards of age {i}: {ages[i]}")

    for c in cards[:15]:
        print(c)
        input()


if __name__=="__main__":
   main()