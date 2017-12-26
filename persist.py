#!/usr/bin/env python

import sqlite3
import string
import autocomplete
from nltk.corpus import brown
from enum import Enum # Not installed on all python installations


# TODO: handle connection setup better
# TODO: setup schema with CONSTRAINT Node UNIQUE (p_id,char)

PRINTABLE = set(string.printable)
class SQL_Vars(Enum):
    id = 0
    p_id = 1
    let = 2
    count = 3

def get_root(c):
    """
    Retrieves the root node in the trie if it exists

    :param c: the sqlite db cursor
    :returns: the id of the trie root
    :raises Exception: if things go wrong
    """
    c.execute("""SELECT id FROM Trie WHERE p_id is NULL""")
    return c.fetchone()


def add_word(word):
    """
    Adds a new word to the persistent trie, used for calling from
    another module.  Opens connection to database

    :param word: word to be added to the persisted trie
    :returns: nothing
    :raises Exception: if things go wrong
    """
    if not word:
        return
    conn = sqlite3.connect('trie.db')
    c = conn.cursor()

    parent = get_root(c)

    if not parent:
        insert_node(c, NULL, '', 0)
        parent = get_root(c)


    for l in sanitize(word):
        c.execute("""SELECT id FROM Trie WHERE p_id = ? AND let = ?""", (parent.id, l))
        result = c.fetchone()
        if result:
            parent = result
        else:
            pass
            # insert word from l onwards, using parent as jumping off point
    # TODO: execute if haven't inserted into trie
    c.execute("""UPDATE Trie SET Count = Count + 1 WHERE id = parent""")

    conn.commit()
    conn.close()


def _add_word(c, word, count=1):
    """
    Adds a new word to the persistent trie, used internally with
    add_words.  Assumes cursor to db can be passed in 

    :param c: the sqlite db cursor
    :param word: word to be added to the persisted trie
    :param count: Count of times word has been seen that should be added
    :returns: nothing
    :raises Exception: if things go wrong
    """
    if not word:
        return

    parent = get_root(c)

    if not parent:
        insert_node(c, None, '', 0)
        parent = get_root(c)


    print word
    for l in sanitize(word):
        c.execute("""SELECT * FROM Trie WHERE p_id = ? AND let = ?""", 
            (parent[SQL_Vars.id], l))
        result = c.fetchone()
        if result:
            parent = result
        else:
            c.execute("""INSERT INTO Trie (p_id, let, count)
                VALUES (?, ?, ?)""", (parent[SQL_Vars.id], l, 0))
            c.execute("""SELECT id FROM Trie WHERE p_id = ? AND let = ?""", 
                (parent[SQL_Vars.id], l))
            parent = c.fetchone()
        print parent

    c.execute("""UPDATE Trie SET Count = Count + ? WHERE id = ?""", 
                (count, parent[SQL_Vars.id]))
    #c.execute("""SELECT * FROM Trie WHERE )

    # c.execute("""SELECT * FROM Trie WHERE id = ?""", 
    #     (parent[SQL_Vars.id]))
    # t = c.fetchone()
    # print t


def insert_node(c, parent, char, count):
    """
    Helper function to insert individual characters. Returns the resulting id
    if successful or None if unsuccessful

    :param c: the db cursor
    :param parent: the id of the node's parent
    :param char: the character node to be inserted
    :param count: number of times the character appears
    :returns: the id of the row in the db
    """
    try:
        c.execute("""INSERT INTO Trie (p_id, let, count)
            VALUES (?, ?, ?)""", (parent, char, count))
    except:
        return None
    else:
        return c.lastrowid


def add_words(words):
    """
    Adds multiple words to the persisten trie

    :param words: an iterable strings
    :returns: None
    """
    print "---------\n\n\n"
    vocab = autocomplete.generate_vocabulary(words)
    conn = sqlite3.connect('trie.db')
    c = conn.cursor()
    c.execute("""DROP TABLE IF EXISTS Trie""")
    c.execute("""
                CREATE TABLE IF NOT EXISTS Trie (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            p_id INT, 
                            let CHAR(1),
                            count INT);
                """)
    num_words = len(vocab)
    i = 0
    for word in vocab:
        _add_word(c, word, vocab[word])
        i += 1
        if i%50 == 0:
            print str(i) + '/' + str(num_words)

    conn.commit()
    conn.close()



def write_trie(root):
    """
    Persist a trie structure to the db

    :param root:
    :returns: None
    """
    parent = get_root(c)
    for child in root.children:
        pass


def sanitize(word):
    """
    Maps input to lowercase and removes any non-printable characters

    :param word: string to be sanitized
    :returns: the sanitized string
    """
    word = word.lower()

    return filter(lambda l: l in PRINTABLE, word)


def main():
    training_set = brown.sents()[:10000]
    training_set = [word for sentence in training_set for word in sentence]
    add_words(training_set)
    #create_trie_from_db()



if __name__ == "__main__":
    main()