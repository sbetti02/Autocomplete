#!/usr/bin/env python

import sqlite3
import string
from nltk.corpus import brown
from enum import Enum # Not installed on old python installations
import autocomplete
from collections import deque
import time


# PRINTABLE = set(string.printable)
PRINTABLE = set(string.ascii_lowercase+string.digits)

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
    c.execute("SELECT * FROM Trie_0")
    return c.fetchone()

def drop_tables():
    conn = db_connect()
    cursor = conn.cursor()
    valid_letters = string.ascii_letters + string.digits
    for let in valid_letters:
        table_base_name = "Trie_" + let + "_" 
        for i in range(1, 50):
            table_name = table_base_name + str(i)
            print "dropping " + table_name
            cursor.execute("""DROP TABLE IF EXISTS """ + table_name)
    conn.close()





def create_table(cursor, t_name, parent_t_name):
    """
        SQL functionality to create a table specified by *table_name* if it 
        doesn't exist and add the p_id_let index to speed up searching
    """

    # TODO: Make more secure

    if parent_t_name:
        cursor.execute("""CREATE TABLE IF NOT EXISTS """ + t_name + """ (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            p_id INT, """
                            #FOREIGN KEY(p_id) REFERENCES """ + parent_t_name + """(id),
                            + """let CHAR(1),
                            count INT,
                            word TEXT);
                """)
    else: # creating root node table
        cursor.execute("""CREATE TABLE IF NOT EXISTS """ + t_name + """ (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            p_id INT, 
                            let CHAR(1),
                            count INT,
                            word TEXT);
                """)

    cursor.execute("CREATE INDEX IF NOT EXISTS p_id_let_index ON " + t_name + " (p_id, let);")

def table_name_and_parent_table(word, count):
    if word:
        word_len = len(word)
        table_name = 'Trie_' + str(word[0]) + '_' + str(word_len)
        if word_len > 1:
            parent_t_name = 'Trie_' + str(word[0]) + '_' + str(word_len-1)
        else:
            parent_t_name = 'Trie_0'
    else:
        table_name = 'Trie_0'
        parent_t_name = None
    return (table_name, parent_t_name)

def insert_node(c, p_id, char, count, word):
    """
    Helper function to insert individual characters. Returns the resulting id
    if successful or None if unsuccessful

    :param c: the db cursor
    :param parent: the id of the node's parent
    :param char: the character node to be inserted
    :param count: number of times the character appears
    :returns: the id of the row in the db
    """
    # try:
        # if word:
        #     word_len = len(word)
        #     table_name = 'Trie_' + str(word[0]) + '_' + str(word_len)
        #     if word_len > 1:
        #         parent_t_name = 'Trie_' + str(word[0]) + '_' + str(word_len-1)
        #     else:
        #         parent_t_name = 'Trie_0'
        # else:
        #     table_name = 'Trie_0'
        #     parent_t_name = None
    table_name, parent_t_name = table_name_and_parent_table(word, count)
    create_table(c, table_name, parent_t_name) 
    c.execute("INSERT INTO " + table_name + """ (p_id, let, count, word)
        VALUES (?, ?, ?, ?)""", (p_id, char, count, word))
    # except:
    #     return None
    # else:
    #     return c.lastrowid

def find_child(cursor, p_id, p_word, child_let):
    pass

def _find_node_db(prefix, cursor):
    """
        Find the node indicated by *prefix* in the database accessable via
        *db_cursor* in the respective database if it exists or return None otherwise
    """

    parent = get_root(cursor)
    if not prefix:
        return parent
    let_ind = 0
    prefix_len = len(prefix)
    table_base_name = 'Trie_' + prefix[0] + '_'
    while parent and prefix_len > let_ind:
        table_name = table_base_name + str(let_ind+1)
        cursor.execute("""SELECT * FROM """ + table_name + """ WHERE p_id = ? AND let = ?""",
                          (parent[SQL_Vars.id], prefix[let_ind]))
        # print cursor.fetchall()
        parent = cursor.fetchone()
        let_ind += 1
    return parent

def _find_node_db_test(prefix):
    conn = db_connect()
    cursor = conn.cursor()

    node = _find_node_db(prefix, cursor)

    conn.close()

    return node


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
    if word[0] in """/*-'`,:()&?;!+[]{}^%$#@~""": # TODO: Remove this.
        return

    parent = get_root(c)
    if not parent:
        insert_node(c, None, '', 0, '')
        parent = get_root(c)

    curr_word = ""
    table_base_name = "Trie_" + str(word[0]) + '_'
    let_ind = 1
    for l in sanitize(word):
        table_name, parent_t_name = table_name_and_parent_table(curr_word + l, let_ind)
        curr_word += l
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        fetall = c.fetchall()
        if (table_name,) not in fetall:
            create_table(c, table_name, parent_t_name) # TODO: Can just call create_table directly
        c.execute("SELECT * FROM " + table_name + " WHERE p_id = ? AND let = ?",
            (parent[SQL_Vars.id], l))
        result = c.fetchone()
        if not result:
            insert_node(c, parent[SQL_Vars.id], l, 0, curr_word)
            c.execute("SELECT * FROM " + table_name + " WHERE p_id = ? AND let = ?",
                (parent[SQL_Vars.id], l)) # Have insert_node return so don't call twice
            result = c.fetchone()
        parent = result
        let_ind += 1
    c.execute("UPDATE " + table_name + " SET Count = Count + ? WHERE id = ?", 
                (count, parent[SQL_Vars.id]))
    c.execute("SELECT * FROM " + table_name + " WHERE id = ?""",
                (parent[SQL_Vars.id],))


def add_words(words):
    """
    Adds multiple words to the persisten trie

    :param words: an iterable strings
    :returns: None
    """
    print "---------\n\n\n"
    vocab = autocomplete.generate_vocabulary(words)
    conn = db_connect()
    c = conn.cursor()
    c.execute("""DROP TABLE IF EXISTS Trie""")
    # c.execute("""
    #             CREATE TABLE IF NOT EXISTS Trie (
    #                         id INTEGER PRIMARY KEY AUTOINCREMENT,
    #                         p_id INT, 
    #                         let CHAR(1),
    #                         count INT,
    #                         word TEXT);
    #             """)
    num_words = len(vocab)
    i = 0
    for word in vocab:
        _add_word(c, word, vocab[word])
        i += 1
        if i%50 == 0:
            print str(i) + '/' + str(num_words)

    conn.commit()
    conn.close()


def sanitize(word):
    """
    Maps input to lowercase and removes any non-printable characters

    :param word: string to be sanitized
    :returns: the sanitized string
    """
    word = word.lower()

    return filter(lambda l: l in PRINTABLE, word)



def words_from_node_db(node, cursor):
    """Return a list of all words found in the database that branch from *node*"""

    all_prefixed_words = []
    explore = deque([node])
    while explore:
        node = explore.pop()
        if node[SQL_Vars.count]:
            all_prefixed_words.append([node[SQL_Vars.word], node[SQL_Vars.count]])
        word = node[SQL_Vars.word]
        if word:
            child_tables = ["Trie_" + word[0] + '_' + str(len(word)+1)]
        else:
            child_tables = ["Trie_" + x + '_1' for x in PRINTABLE]
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        fetall = cursor.fetchall()
        child_tables = filter(lambda t: (t,) in fetall, child_tables)
        for child_table in child_tables:
            # if (child_table,) not in fetall:

            cursor.execute("""SELECT * FROM """ + child_table + """ WHERE p_id = ?""", 
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



def main():
    # drop_tables()

    # training_set = brown.sents()[:10000]
    # training_set = [word for sentence in training_set for word in sentence]


    # training_set = ['a' for _ in xrange(1000)]
    # b = ['ads' for _ in xrange(1000)]
    # training_set.extend(b)
    # training_set.append('asdf')
    # add_words(training_set)



    # print _find_node_db_test("")
    # print _find_node_db_test("a")
    # print _find_node_db_test("as")
    # print _find_node_db_test("ad")
    # print _find_node_db_test("ads")
    # print _find_node_db_test("adv")
    # print _find_node_db_test("ade")

    start = time.time()
    prefixed_words = search_pref_db("t")
    print "Time taken to search everything:", time.time()-start
    prefixed_words.sort(key=lambda x: -x[1])
    print prefixed_words





if __name__ == "__main__":
    main()