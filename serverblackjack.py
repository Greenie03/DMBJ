#!/usr/bin/env python3
# -*- coding: utf-8 -
import random
import asyncio

allTables = []

def read_command(reader,command):
    data = reader.readline()
    return data.decode().replace(command + " ",'')

def send_message(writer,msg):
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
    def __init__(self, symbol, number):
        self.symbol = symbol
        self.number = number


class Player:
    def __init__(self, name, hand, score):
        self.name = name
        self.hand = hand
        self.score = score

    def get_name(self):
        return self.name

    def get_hand(self):
        return self.hand

    def get_score(self):
        return self.score

    def add_to_hand(self, card):
        self.hand.append(card)

    def add_to_score(self, value):
        self.score += value

def init_deck():
    deck = []
    symbolList = ["Coeur", "Carreau", "Trefle", "Pic"]
    numberList = ["As", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Valet", "Dame", "Roi"]
    for i in symbolList:
        for j in numberList:
            deck.append(Card(i,j))
    return deck

async def blackjack_game(table, reader, writer, deck):
    random.shuffle(deck)
    for i in range(2):
        table.get_players()[writer.get_extra_info('peername')[0]].add_to_hand(deck.pop())
        if len(table.get_players()["donneur"].get_hand()) <= 2:
            table.get_players()["donneur"].add_to_hand(deck.pop())
    writer.write(table.get_players()[writer.get_extra_info('peername')[0]].get_hand)
    rcv  = int(read_command(reader,"MORE"))
    while rcv != 0 or table.get_players()[writer.get_extra_info('peername')[0]].get_score <= 21:
        #faire les bandibangas
        writer.write(table.get_players()[writer.get_extra_info('peername')[0]].get_hand)
        send_message(writer,'.')
        rcv = int(read_command(reader,"MORE"))
    if table.get_players()[writer.get_extra_info('peername')[0]].get_score > 21:
        send_message(writer,"Vous avez perdu.")



async def croupier(reader, writer):
    welcome_msg = "Hello " + writer.get_extra_info('peername')[0]
    send_message(writer,welcome_msg)
    table_name = read_command(reader,"NAME")
    send_message(writer,"Table créée avec " + table_name)
    table_time = int(read_command(reader,"TIME"))
    send_message(writer,"Temps affecté avec " + str(table_time))
    allTables.append(Table(table_name, table_time))


async def joueur(reader, writer):
    welcome_msg = "Bonjour " + writer.get_extra_info('peername')[0]
    msg = ""
    table_name = ""
    send_message(writer,welcome_msg)
    table_name = read_command(reader,"NAME")
    if table_name not in [i.get_name() for i in allTables]:
        send_message(writer,"Cette table n'existe pas")
        send_message(writer,"END")
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
            for i in table.get_players()[1:]:
                msg += i + ", "
            msg += " sont connectés à la table : " + table_name
        send_message(writer, msg)
        while not (len(table.get_players()) >= 8 or table.get_time() <= 0):
            send_message(writer,table.get_time())
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
