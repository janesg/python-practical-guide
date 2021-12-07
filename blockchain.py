blockchain = []

def add_value(value = 33.33):
    if len(blockchain) == 0:
        blockchain.append([value])
    else:
        blockchain.append([blockchain[-1], value])

    print(blockchain)

add_value(5.4)
add_value(1.8)
add_value()
add_value(0.2)
