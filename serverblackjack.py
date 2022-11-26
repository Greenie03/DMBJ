#!/usr/bin/env python3
# -*- coding: utf-8 -
import random
import asyncio

allTables = []


async def read_command(reader, command):
    data = await reader.readline()
    return data.decode().replace(command + " ", '')


async def send_message(writer, msg):
    writer.write(str(msg).encode() + b"\r\n")


class Table:
    def __init__(self, name, time):
        self.name = name
        self.time = time
        self.players = dict()

    def add_player(self, name):
        self.players[name] = Player(name, [], 0)

    def get_name(self):
        return self.name

    def get_time(self):
        return self.time

    def get_players(self):
        return self.players

    def set_time(self, new_time):
        self.time = new_time


class Card:
    def __init__(self, symbol, number,value):
        self.symbol = symbol
        self.number = number
        self.value = value

    def get_number(self):
        return self.number

    def get_value(self):
        return self.value

    def get_symbol(self):
        return self.symbol

    def __str__(self):
        return self.number + " de " + self.symbol


class Player:
    def __init__(self, name, hand, score):
        self.name = name
        self.hand = hand
        self.score = score
        self.is_playing = False

    def get_name(self):
        return self.name

    def get_hand(self):
        return self.hand

    def display_hand(self):
        d = ""
        for i in self.hand:
            d += str(i) +", "
        return d

    def get_score(self):
        return self.score

    def add_to_hand(self, card):
        self.hand.append(card)
        if self.score > 10 and card.get_number() == "As":
            self.score += card.get_value() - 10
        else:
            self.score += card.get_value()


def init_deck():
    deck = []
    symbolList = ["Coeur", "Carreau", "Trefle", "Pic"]
    numberList = {"As":11, "2":2, "3":3, "4":4, "5":5, "6":6, "7":7, "8":8, "9":9, "10":10, "Valet":10, "Dame":10, "Roi":10}
    for i in symbolList:
        for j in numberList:
            deck.append(Card(i, j, numberList[j]))
    return deck


async def blackjack_game(table, reader, writer, deck):
    
    random.shuffle(deck)
    for i in range(2):
        table.get_players()[writer.get_extra_info('peername')[0]].add_to_hand(deck.pop())
        if len(table.get_players()["donneur"].get_hand()) <= 2:
            table.get_players()["donneur"].add_to_hand(deck.pop())
    writer.write(("donneur : " + str(table.get_players()["donneur"].get_hand()[0]) + ", votre main : " + table.get_players()[writer.get_extra_info('peername')[0]].display_hand() + ", votre score : " + str(table.get_players()[writer.get_extra_info('peername')[0]].get_score())).encode() + b"\r\n")
    await send_message(writer, '.')
    data = await reader.readline()
    rcv = int(data.decode().replace("MORE ", ''))
    while rcv != 0 and table.get_players()[writer.get_extra_info('peername')[0]].get_score() <= 21:
        if rcv == 1:
            table.get_players()[writer.get_extra_info('peername')[0]].add_to_hand(deck.pop())
            writer.write(("donneur : " + str(table.get_players()["donneur"].get_hand()[0]) + ", votre main : " +
                      table.get_players()[
                          writer.get_extra_info('peername')[0]].display_hand() + ", votre score : " + str(
                    table.get_players()[writer.get_extra_info('peername')[0]].get_score())).encode() + b"\r\n")
        await send_message(writer, '.')
        data = await reader.readline()
        rcv = int(data.decode().replace("MORE ", ''))
    card = deck.pop()
    while table.get_players()["donneur"].get_score() + card.get_value() <= 17:
        table.get_players()["donneur"].add_to_hand(card)
        card = deck.pop()
    await send_message(writer, "score du donneur : " + str(table.get_players()["donneur"].get_score()))
    if table.get_players()[writer.get_extra_info('peername')[0]].get_score() > table.get_players()["donneur"].get_score() and table.get_players()[writer.get_extra_info('peername')[0]].get_score() < 21:
        await send_message(writer,"Vous avez gagné")
    elif table.get_players()[writer.get_extra_info('peername')[0]].get_score() == table.get_players()[
            "donneur"].get_score() and table.get_players()["donneur"].get_score() < 21:
        await send_message(writer, "Vous avez fait égalité")
    else:
        await send_message(writer, "Vous avez perdu")
    await send_message(writer, "END")

async def croupier(reader, writer):
    welcome_msg = "Hello " + writer.get_extra_info('peername')[0]
    await send_message(writer, welcome_msg)
    data = await reader.readline()
    table_name = data.decode().replace("NAME ", '')
    await send_message(writer, "Table créée avec " + table_name)
    data = await reader.readline()
    table_time = int(data.decode().replace("TIME ", ''))
    await send_message(writer, "Temps affecté avec " + str(table_time))
    allTables.append(Table(table_name, table_time))


async def joueur(reader, writer):
    welcome_msg = "Bonjour " + writer.get_extra_info('peername')[0]
    msg = ""
    table_name = ""
    await send_message(writer, welcome_msg)
    data = await reader.readline()
    table_name = data.decode().replace("NAME ", '')
    if table_name not in [i.get_name() for i in allTables]:
        await send_message(writer, "Cette table n'existe pas")
        await send_message(writer, "END")
    else:
        for i in allTables:
            if i.get_name() == table_name:
                table = i
        table.add_player("donneur")
        table.add_player(writer.get_extra_info('peername')[0])
        msg = ""
        if len(table.get_players()) <= 2:
            msg = writer.get_extra_info('peername')[0] + " est connecté à la table : " + table_name
        else:
            for i in table.get_players():
                msg += i + ", "
            msg += " sont connectés à la table : " + table_name
        await send_message(writer, msg)
        while not (len(table.get_players()) >= 8 or table.get_time() <= 0):
            await send_message(writer, table.get_time())
            await asyncio.sleep(1)
            table.set_time(table.get_time() - 1)
        if table in allTables:
            allTables.remove(table)
        deck = init_deck()
        await blackjack_game(table, reader, writer, deck)


async def main():
    croupier_server = await asyncio.start_server(croupier, "10.0.1.1", 668)
    joueur_server = await asyncio.start_server(joueur, "10.0.1.1", 667)
    await croupier_server.serve_forever()
    await joueur_server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())