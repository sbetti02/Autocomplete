#!/usr/bin/env python

import sqlite3
import string
import autocomplete
from nltk.corpus import brown
from enum import Enum # Not installed on all python installations
from collections import deque
from operator import itemgetter
import time


# TODO: handle connection setup better
# TODO: setup schema with CONSTRAINT Node UNIQUE (p_id,char)

PRINTABLE = set(string.printable)

class SQL_Vars(Enum):
    id = 0
    p_id = 1
    let = 2
    count = 3
    word = 4

def db_connect():
    """
        Functionality used for all functions that need to connect to the database.
        Single source of truth for if database moves or changes for any reason.
    """
    # TODO: Include this function in all functions that need it
    return sqlite3.connect('trie.db')

def get_root(c):
    """
    Retrieves the root node in the trie if it exists

    :param c: the sqlite db cursor
    :returns: the id of the trie root
    :raises Exception: if things go wrong
    """
    c.execute("""SELECT * FROM Trie WHERE p_id is NULL""")
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
        insert_node(c, None, '', 0, '')
        parent = get_root(c)

    curr_word = ""
    for l in sanitize(word):
        curr_word += l
        c.execute("""SELECT * FROM Trie WHERE p_id = ? AND let = ?""", 
            (parent[SQL_Vars.id], l))
        result = c.fetchone()
        if result:
            parent = result
        else:
            c.execute("""INSERT INTO Trie (p_id, let, count, word)
                VALUES (?, ?, ?, ?)""", (parent[SQL_Vars.id], l, 0, curr_word))
            c.execute("""SELECT * FROM Trie WHERE p_id = ? AND let = ?""", 
                (parent[SQL_Vars.id], l))
            parent = c.fetchone()

    c.execute("""UPDATE Trie SET Count = Count + ? WHERE id = ?""", 
                (count, parent[SQL_Vars.id]))
    c.execute("""SELECT * FROM Trie WHERE id = ?""",
                (parent[SQL_Vars.id],))


def insert_node(c, parent, char, count, word):
    """
    Helper function to insert individual characters. Returns the resulting id
    if successful or None if unsuccessful

    :param c: the db cursor
    :param parent: the id of the node's parent
    :param char: the character node to be inserted
    :param count: number of times the character appears
    :returns: the id of the row in the db
    TODO: Should either return the id # or -1 on error
    """
    try:
        c.execute("""INSERT INTO Trie (p_id, let, count, word)
            VALUES (?, ?, ?, ?)""", (parent, char, count, word))
    except:
        return None
    else:
        return c.lastrowid

def find_children(c, p_id):
    """Return all child nodes of parent indicated by *p_id*"""

    c.execute("""SELECT * FROM Trie WHERE p_id = ?""", [p_id])
    return c.fetchall()

def add_words(words):
    """
    Adds multiple words to the persisten trie

    :param words: an iterable strings
    :returns: None
    """
    print "---------\n\n\n"
    vocab = autocomplete.generate_vocabulary(words)
    conn = sqlite3.connect('trie.db')
    cursor = conn.cursor()
    # c.execute("""DROP TABLE IF EXISTS Trie""")
    create_table(cursor)
    # c.execute("""
    #             CREATE TABLE IF NOT EXISTS Trie (
    #                         id INTEGER PRIMARY KEY AUTOINCREMENT,
    #                         p_id INT, 
    #                         let CHAR(1),
    #                         count INT,
    #                         word TEXT);
    #             """)
    # c.execute("""CREATE INDEX p_id_let_ind ON Trie (p_id, let);""")
    num_words = len(vocab)
    i = 0
    for word in vocab:
        _add_word(cursor, word, vocab[word])
        i += 1
        if i%50 == 0:
            print str(i) + '/' + str(num_words)
    # c.execute("""CREATE INDEX p_id_let_ind ON Trie (p_id, let);""")

    conn.commit()
    conn.close()

def create_table(cursor):
    """
        SQL functionality to create a table specified by *table_name* if it 
        doesn't exist and add the p_id_let index to speed up searching
    """

    # TODO: Make more secure

    cursor.execute("""CREATE TABLE IF NOT EXISTS Trie (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        p_id INT, 
                        let CHAR(1),
                        count INT,
                        word TEXT);
            """)
    cursor.execute("CREATE INDEX IF NOT EXISTS p_id_let_ind ON Trie (p_id, let);")


def write_trie(Trie):
    """
    Persist a trie structure to the db

    :param Trie: A Trie object
    :returns: True if successful, False if found error
    """
    conn = db_connect()
    cursor = conn.cursor()

    create_table(cursor)

    # db_root = get_root(cursor)
    # if not db_root:
    #     insert_node(c, None, '', 0, '')
    #     db_root = get_root(cursor)
    explore = deque()
    explore.append((Trie.root,None))
    while explore:
        curr_node, p_id = explore.pop()
        if p_id and p_id % 50 == 0:
            print p_id
        # print "Writing", curr_node
        cursor.execute("""SELECT * FROM Trie WHERE p_id=? AND let=?""", 
                        (p_id, curr_node.letter))
        db_node = cursor.fetchone()
        if db_node: # If the Trie node already exists in the table
            cursor.execute("""UPDATE Trie SET Count = Count + ? WHERE id = ?""", 
                          (curr_node.word_counts, db_node[SQL_Vars.id]))
        else: # Need to make new entry in table for Trie
            insert_node(cursor, p_id, curr_node.letter, curr_node.word_counts, curr_node.word)
            cursor.execute("""SELECT * FROM Trie WHERE p_id IS ? AND let IS ?""",
                            (p_id, curr_node.letter)) # TODO: remove once insert returning correctly
            db_node = cursor.fetchone()
        p_id = db_node[SQL_Vars.id]
        for child in curr_node.children:
            explore.appendleft((child, p_id))

    cursor.execute("CREATE INDEX IF NOT EXISTS p_id_let_index ON Trie (p_id, let);")
    conn.commit()
    conn.close()
    return True

    # parent = get_root(c)
    # for child in root.children:
    #     pass


def sanitize(word):
    """
    Maps input to lowercase and removes any non-printable characters

    :param word: string to be sanitized
    :returns: the sanitized string
    """
    word = word.lower()

    return filter(lambda l: l in PRINTABLE, word)

def _find_node_db(prefix, db_cursor):
    """
        Find the node indicated by *prefix* in the database accessable via
        *db_cursor* in the respective database if it exists or return None otherwise
    """

    curr_node = get_root(db_cursor)
    let_ind = 0
    prefix_len = len(prefix)
    while curr_node and prefix_len > let_ind:
        db_cursor.execute("""SELECT * FROM Trie WHERE p_id = ? AND let = ?""", 
                            (curr_node[SQL_Vars.id], prefix[let_ind]))
        curr_node = db_cursor.fetchone()
        let_ind += 1
    return curr_node


def _find_node_db_test(prefix):
    conn = sqlite3.connect('trie.db')
    c = conn.cursor()

    node = _find_node_db(prefix, c)

    conn.close()

    return node

def words_from_node_db(node, cursor):
    """Return a list of all words found in the database that branch from *node*"""

    all_prefixed_words = []
    explore = deque([node])
    while explore:
        node = explore.pop()
        if node[SQL_Vars.count]:
            all_prefixed_words.append([node[SQL_Vars.word], node[SQL_Vars.count]])
        cursor.execute("""SELECT * FROM Trie WHERE p_id = ?""", 
                    (node[SQL_Vars.id],))
        children = cursor.fetchall()
        for child in children:
            explore.appendleft(child)
    return all_prefixed_words

def search_pref_db(prefix):
    """
        Find and return a list of the words that begin with *prefix* found in
        the database speficied by *db_cursor* sorted from most to least common
    """

    conn = sqlite3.connect('trie.db')
    cursor = conn.cursor()

    curr_node = _find_node_db(prefix, cursor)
    prefixed_words = words_from_node_db(curr_node, cursor)


    conn.close()
    return prefixed_words

def drop_table():
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("""DROP TABLE IF EXISTS Trie""")
    conn.close()


def main():
    # drop_table()
    # training_set = brown.sents()[:10000]
    # training_set = [word for sentence in training_set for word in sentence]
    # add_words(training_set)

    # create_trie_from_db()
    start = time.time()
    prefixed_words = search_pref_db("")
    print "Time taken to search everything:", time.time()-start
    prefixed_words.sort(key=lambda x: -x[1])
    # print prefixed_words

    # print find_node_from_db("")



if __name__ == "__main__":
    main()