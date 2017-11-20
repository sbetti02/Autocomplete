#!/usr/bin/env python

import sqlite3
import string

# TODO: handle connection setup better
# TODO: setup schema with CONSTRAINT Node UNIQUE (p_id,char)

PRINTABLE = set(string.printable)

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
    Adds a new word to the persistent trie

    :param word: word to be added to the persisted trie
    :returns: nothing
    :raises Exception: if things go wrong
    """
    conn = sqlite3.connect('trie.db')
    c = conn.cursor()

    parent = get_root(c)
    for l in sanitize(word):
        c.execute("""SELECT id FROM Trie WHERE p_id = ? AND char = ?""", (parent, l))
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
        c.execute("""INSERT INTO Trie (p_id, char, count)
            VALUES (?, ?, ?)""", (parent, char, count))
        c.commit()
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
    for word in words:
        # TODO: improve connection handling; don't want to open and close for every word
        add_word(word)


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
