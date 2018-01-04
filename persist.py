#!/usr/bin/env python

import sqlite3
import string
import autocomplete
from nltk.corpus import brown
from enum import Enum # Not installed on all python installations
from collections import deque
from operator import itemgetter
import time
import argparse

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
    return sqlite3.connect('trie.db')

def get_root(cursor):
    """
    Retrieves the root node in the trie if it exists

    :param c: the sqlite db cursor
    :returns: the id of the trie root
    :raises Exception: if things go wrong
    """
    cursor.execute("""SELECT * FROM Trie WHERE p_id is NULL""")
    return cursor.fetchone()

def add_word(word):
    """
    Adds a new word to the persistent trie, used for calling from
    another module.  Opens connection to database

    :param word: word to be added to the persisted trie
    :returns: True if successful, False otherwise
    :raises Exception: if things go wrong
    """

    conn = db_connect()
    cursor = conn.cursor()
    success = _add_word(cursor, word)
    conn.commit()
    conn.close()
    return success

def _add_word(cursor, word, count=1):
    """
    Adds a new word to the persistent trie, used internally with
    add_words.  Assumes cursor to db can be passed in 
    :param cursor: the sqlite db cursor
    :param word: word to be added to the persisted trie
    :param count: Count of times word has been seen that should be added
    :returns: nothing
    :raises Exception: if things go wrong
    """
    if not word:
        return

    root = get_root(cursor)
    if not root:
        insert_node(cursor, None, '', 0, '')
        root = get_root(cursor)
    p_id = root[SQL_Vars.id]

    curr_word = ""
    for l in sanitize(word):
        curr_word += l
        cursor.execute("""SELECT * FROM Trie WHERE p_id = ? AND let = ?""", 
            (p_id, l))
        result = cursor.fetchone()
        if result:
            p_id = result[0]
        else: # For whatever reason, this insert is being optimized by leaving this
              # Insertion/Selection implementation in this fxn instead of moving to 
              # an outer function.
            cursor.execute("""INSERT INTO Trie (p_id, let, count, word) 
                VALUES (?, ?, ?, ?)""", (p_id, l, 0, curr_word))
            cursor.execute("""SELECT * FROM Trie WHERE p_id = ? AND let = ?""", 
                (p_id, l))
            p_id = cursor.fetchone()[0]

    if update_node(cursor, p_id, count) == -1:
        return False
    return True

def insert_node(cursor, p_id, char, count, word):
    """
    Helper function to insert individual characters. Returns the resulting id
    if successful or None if unsuccessful

    :param c: the db cursor
    :param p_id: the id of the node's p_id
    :param char: the character node to be inserted
    :param count: number of times the character appears
    :returns: the id of the row in the db
    """

    try:
        cursor.execute("""INSERT INTO Trie (p_id, let, count, word)
            VALUES (?, ?, ?, ?)""", (p_id, char, count, word))
        cursor.execute("""SELECT * FROM Trie WHERE p_id IS ? AND let IS ?""",
                            (p_id, char))
        return cursor.fetchone()[0]
    except:
        return -1

def update_node(cursor, id, count):
    """
        Use *cursor* to update the count of entries at *id* in db table by *count*
        Returns 0 on success, -1 on failure
    """

    try:
        cursor.execute("""UPDATE Trie SET Count = Count + ? WHERE id = ?""", 
                      (count, id))
        return 0
    except:
        return -1


def find_children(cursor, p_id):
    """Return all child nodes of parent indicated by *p_id*"""

    cursor.execute("""SELECT * FROM Trie WHERE p_id = ?""", [p_id])
    return cursor.fetchall()

def add_words(words):
    """
    Adds multiple words to the persisten trie

    :param words: an iterable strings
    :returns: None
    """
    print "---------\n\n\n"
    vocab = autocomplete.generate_vocabulary(words)
    conn = db_connect()
    cursor = conn.cursor()
    create_table(cursor)
    num_words = len(vocab)
    i = 0
    for word in vocab:
        _add_word(cursor, word, vocab[word])
        i += 1
        if i%50 == 0:
            print str(i) + '/' + str(num_words)
    conn.commit()
    conn.close()

def create_table(cursor):
    """
        SQL functionality to create a table specified by *table_name* if it 
        doesn't exist and add the p_id_let index to speed up searching
    """

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
    explore = deque()
    explore.append((Trie.root,None))

    while explore:
        curr_node, p_id = explore.pop()
        if p_id and p_id % 50 == 0:
            print p_id
        cursor.execute("""SELECT id FROM Trie WHERE p_id=? AND let=?""", 
                      (p_id, curr_node.letter))
        next_p_id = cursor.fetchone()
        if next_p_id: # If the Trie node already exists in the table
            next_p_id = next_p_id[0]
            if update_node(cursor, next_p_id, curr_node.word_counts) == -1:
                return False
        else: # Need to make new entry in table for Trie
            next_p_id = insert_node(cursor, p_id, curr_node.letter, curr_node.word_counts, curr_node.word)
            print next_p_id
            if next_p_id == -1:
                return False
        for child in curr_node.children:
            explore.appendleft((child, next_p_id))

    conn.commit()
    conn.close()
    return True

def sanitize(word):
    """
    Maps input to lowercase and removes any non-printable characters

    :param word: string to be sanitized
    :returns: the sanitized string
    """
    word = word.lower()

    return filter(lambda l: l in PRINTABLE, word)

def _find_node_db(cursor, prefix):
    """
        Find the node indicated by *prefix* in the database accessable via
        *cursor* in the respective database if it exists or return None otherwise
    """

    curr_node = get_root(cursor)
    let_ind = 0
    prefix_len = len(prefix)
    while curr_node and prefix_len > let_ind:
        cursor.execute("""SELECT * FROM Trie WHERE p_id = ? AND let = ?""", 
                            (curr_node[SQL_Vars.id], prefix[let_ind]))
        curr_node = cursor.fetchone()
        let_ind += 1
    return curr_node

def _find_node_db_test(prefix):
    conn = db_connect()
    cursor = conn.cursor()

    node = _find_node_db(cursor, prefix)

    conn.close()

    return node

def words_from_node_db(cursor, node):
    """Return a list of all words found in the database that branch from *node*"""

    all_prefixed_words = []
    if not node:
        return []
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

def search_pref_db(prefix): # finding all words necessary for future functionality
    """
        Find and return a list of the words that begin with *prefix* found in
        the database speficied by *db_cursor* sorted from most to least common
    """

    conn = db_connect()
    cursor = conn.cursor()

    curr_node = _find_node_db(cursor, prefix)
    prefixed_words = words_from_node_db(cursor, curr_node)

    conn.close()
    return prefixed_words

def drop_table():
    """
        Outer functionality to drop the Trie table if needed
    """
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("""DROP TABLE IF EXISTS Trie""")
    create_table(cursor) # leave base table instantiation
    conn.close()

def add_brown_to_db(num_sentences=50000):
    """
        Add the first *num_sentences* sentences from the Brown corpus to the db
    """
    sentences = brown.sents()[:num_sentences]
    words = [word for sentence in sentences for word in sentence]
    add_words(words)

def most_common_words(prefix, count=5):
    """
        Return the most common *count* words associated with a particular prefix
    """
    prefixed_words = search_pref_db(prefix)
    prefixed_words.sort(key=lambda x: -x[1])
    return prefixed_words[:count]

def run_interpreter_db(top_words=5):
    """
        Run an interpreter for a trie stored in the db that repeatedly asks for 
        prefixes to Enter and returns the top *top_words* most common words given 
        that particular prefix
    """
    inp = ""
    while inp != 'quit()':
        print "Enter a valid prefix to find the most common words given that prefix"
        print "Enter quit() to exit"
        inp = raw_input('> ')
        if inp == 'quit()':
            return
        word_list = most_common_words(inp.lower(), top_words)
        num_to_print = min(top_words, len(word_list))
        if num_to_print == 0:
            print "No words were found..."
        for i in xrange(num_to_print):
            print str(i+1)+'. ' + str(word_list[i][0]) + ' - ' + str(word_list[i][1])


def main():
    parser = argparse.ArgumentParser(description="Give the most common word given a prefix")
    parser.add_argument("-add_words", action="store_true") # TODO: let person indicate how many to add
    parser.add_argument("-no_Int", action="store_true") # don't want to run interpreter
    parser.add_argument("-clear_db", action="store_true")
    args = parser.parse_args()
    if args.clear_db:
        drop_table()
    if args.add_words:
        add_brown_to_db()
    if not args.no_Int:
        run_interpreter_db()


if __name__ == "__main__":
    main()