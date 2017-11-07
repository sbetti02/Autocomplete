#!/usr/bin/env python

import sqlite3
import string

# CONSTRAINT Node UNIQUE (p_id,char)

printable = set(string.printable)

def get_root(c):
    c.execute("""SELECT id FROM Trie WHERE p_id is NULL""")
    return c.fetchone()

def add_word(word):
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
    """Helper function to insert letters. Returns the resulting id 
       if successful or None if unsuccessful"""

    try:
        c.execute("""INSERT INTO Trie (p_id, char, count)
            VALUES (?, ?, ?)""", (parent, char, count))
        c.commit()
    except:
        return None
    else:
        return c.lastrowid

def add_words(words):
    for word in words:
        # TODO: improve connection handling; don't want to open and close for every word
        add_word(word)

def write_trie(root):
    parent = get_root(c)
    for child in root.children:
        pass

def sanitize(word):
    word = word.lower()
    return filter(lambda l: l in printable, word)
