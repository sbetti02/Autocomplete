import nltk.tokenize
from nltk.corpus import brown
from collections import defaultdict
import re
from operator import itemgetter
import argparse
import os
import persist
from collections import deque
import time



class Trie:
    """
        The Trie class builds and maintains a trie, where each node represents 
        a different letter, and overall represents all of the words seen in 
        the given vocabulary.
    """
    nearby_chars = {} # Mapping of letter to the nearby chars on a keyboard
    further_chars = {} # Mapping of letter to possible but further away chars

    nearby_chars['q'] = ['a','s']
    nearby_chars['w'] = ['q','e','s']
    nearby_chars['e'] = ['w','r','d']
    nearby_chars['r'] = ['e','t','f']
    nearby_chars['t'] = ['r','g','y']
    nearby_chars['y'] = ['t','h','u']
    nearby_chars['u'] = ['y','j','i']
    nearby_chars['i'] = ['u','o','k']
    nearby_chars['o'] = ['i','p','l']
    nearby_chars['p'] = ['o']

    nearby_chars['a'] = ['q','s','z']
    nearby_chars['s'] = ['w','a','d','x','z']
    nearby_chars['d'] = ['e','s','f','c','x']
    nearby_chars['f'] = ['d','r','g','v','c']
    nearby_chars['g'] = ['f','h','t','v','b']
    nearby_chars['h'] = ['g','j','y','n','b']
    nearby_chars['j'] = ['h','u','k','n','m']
    nearby_chars['k'] = ['i','j','l','m']
    nearby_chars['l'] = ['o','k']

    nearby_chars['z'] = ['a','x','s']
    nearby_chars['x'] = ['z','s','d','c']
    nearby_chars['c'] = ['d','f','x','v']
    nearby_chars['v'] = ['c','f','g','b']
    nearby_chars['b'] = ['v','g','h','n']
    nearby_chars['n'] = ['b','h','j','m']
    nearby_chars['m'] = ['n','j','k']

    further_chars['q'] = ['s']
    further_chars['w'] = ['a','d']
    further_chars['e'] = ['s','f']
    further_chars['r'] = ['d','g']
    further_chars['t'] = ['f','h']
    further_chars['y'] = ['g','j']
    further_chars['u'] = ['h','k']
    further_chars['i'] = ['j','l']
    further_chars['o'] = ['k']
    further_chars['p'] = ['l']

    further_chars['a'] = ['w','x']
    further_chars['s'] = ['q','e']
    further_chars['d'] = ['w','r']
    further_chars['f'] = ['e','t']
    further_chars['g'] = ['r','y']
    further_chars['h'] = ['t','u']
    further_chars['j'] = ['y','i']
    further_chars['k'] = ['u','o']
    further_chars['l'] = ['i','p']


    def __init__(self, vocab):
        """ 
            Initializing function for the trie, creates structure 
            from given vocabulary dict 
        """
        self.root = Node("", "")
        self.vocabulary = vocab # should I store this whole thing.?
        self.generate_trie()
        self.total_words = len(self.vocabulary)

    def generate_trie(self):
        """  Adds one word at a time from the vocabulary to the trie  """
        for word in self.vocabulary:
            self.add_word(word)

    def add_word(self, word):
        """ 
            Adds an individual word to the try letter by letter.  
            Calls increment_count on the node of the last letter in the word to 
            keep track of the number of appearances of a particular word. 
        """

        curr_node = self.root
        curr_word = ""
        word_count = self.vocabulary[word]
        for letter in word:
            full_word = curr_word + letter
            child_node = curr_node.child(letter)
            if not child_node:
                child_node = Node(letter, curr_word)
                curr_node.add_child(child_node)
            curr_word = full_word
            curr_node = child_node
            if full_word == word:
                child_node.increment_count(word_count)
                # self.complete_words[full_word] = child_node

    def all_words_with_prefix(self, string):
        """  returns all words that start with a prefix given by 'string'  """
        return self.words_from_node(self.find_node(string))
         

    def words_from_node(self, node):
        """ 
            Recursively traverse through the tree from a given starting node,
            searching for all valid words and returning them in a list 
        """
        if not node:
            return []
        prefixed_words = []
        if node.word_counts:
            prefixed_words.append([node.word, node.word_counts])
        for child in node.children:
            prefixed_words.extend(self.words_from_node(child))
        return prefixed_words

    def find_node(self, string):
        """
            Given a string, traverse through the trie to locate the last letter
            belonging to the string, which represents the string itself
        """
        curr_node = self.root
        curr_word = ""
        for letter in string:
            full_word = curr_word + letter
            child_node = curr_node.child(letter)
            if child_node:
                curr_node = child_node
            else:
                return None
            curr_word = full_word
        return curr_node

    def _print_trie_helper(self, curr_node):
        if curr_node.word_counts:
            print curr_node.word, curr_node.word_counts
        for child in curr_node.children:
            self.print_trie_helper(child)

    def _print_trie(self):
        """  Print out each word on the trie. Used for testing  """
        self._print_trie_helper(self.root)

    def create_from_db(self):
        """
            Create the Trie structure from a representation of a Trie stored in a
            database.  Each node in the database is stored as a tuple of
            (id, p_id, let, count, word)
            Void function
        """

        if self.root.children:
            print "Error: create_from_db given non-empty Trie"
            return None
        db_access_time = 0
        total_time_start = time.time()
        from persist import SQL_Vars
        conn = persist.db_connect()
        cursor = conn.cursor()
        start = time.time()
        sql_node = persist.get_root(cursor)
        db_access_time += time.time()-start
        explore = deque([(sql_node, self.root)])
        while explore:
            sql_node, trie_node = explore.pop()
            start = time.time()
            if sql_node[SQL_Vars.count]:
                self.total_words += 1
            sql_children = persist.find_children(cursor, sql_node[SQL_Vars.id])
            finish = time.time()
            db_access_time += finish-start
            children_trie_nodes = []
            for child_sql_node in sql_children:
                child_trie_node = Node(child_sql_node[SQL_Vars.let], 
                                       sql_node[SQL_Vars.word], 
                                       child_sql_node[SQL_Vars.count])
                children_trie_nodes.append(child_trie_node)
                explore.appendleft((child_sql_node, child_trie_node))
            trie_node.add_children(children_trie_nodes)
        conn.close()
        print "Total time used for func:", time.time()-total_time_start
        print "Total time accessing db to find children:", db_access_time

    def _same_len_word_probs(self, word):
        """
            Return [word, prob] pairs of the probability of spelling *word*
            slightly wrong, exploring all nearby words that have the same
            number of letters as *word*
        """

        SAME_LET_PROB_VAL = 0.75
        NEAR_LET_PROB_VAL = 0.08
        FAR_LET_PROB_VAL = 0.03

        nearby_sequences = [[word[0], SAME_LET_PROB_VAL]]
        for near_char in self.nearby_chars[word[0]]:
            nearby_sequences.append([near_char, NEAR_LET_PROB_VAL]) # TODO: Remove hard code
        for far_char in self.further_chars[word[0]]:
            nearby_sequences.append([far_char, FAR_LET_PROB_VAL])
        for letter in word[1:]:
            new_sequences = []
            for seq in nearby_sequences:
                new_sequences.append([seq[0]+letter, seq[1]*SAME_LET_PROB_VAL])
                if letter in self.nearby_chars:
                    for near_let in self.nearby_chars[letter]:
                        new_sequences.append([seq[0]+near_let, seq[1]*NEAR_LET_PROB_VAL])
                if letter in self.further_chars:
                    for far_let in self.further_chars[letter]:
                        new_sequences.append([seq[0]+far_let, seq[1]*FAR_LET_PROB_VAL])
            nearby_sequences = new_sequences
        return nearby_sequences

    def _all_related_word_probs(self, same_len_seqs_probs):
        """
            Given a list of [word, prob] pairs, explores and finds the probability
            of other words that use any of the words in the given list as a root.
            Returns a list of [word, prob] pairs of words from the original list
            and any new found words.
        """

        EXTRA_LET_PEN_FACTOR = 10

        all_related_sequences = []
        word_len = len(same_len_seqs_probs[0])
        for seq in same_len_seqs_probs:
            found_words = self.all_words_with_prefix(seq[0])
            for found_word, word_count in found_words:
                if found_word == seq[0]:
                    all_related_sequences.append(seq)
                else:
                    extra_lets = len(found_word)-word_len
                    all_related_sequences.append([found_word, 
                                                  seq[1]*(EXTRA_LET_PEN_FACTOR**-extra_lets)])
                all_related_sequences[-1][1] *= (float(word_count)/self.total_words)
        return all_related_sequences


    def local_word_probs(self, word):
        """
            Generate all words close in spelling to *word* and determine the
            probabilities of each possibility.  Then return a list sorted by
            the probability of the word occurring.
        """

        if not word or not re.search('[a-zA-Z]', word[0]):
            return []
        nearby_seq_probs = self._same_len_word_probs(word)
        all_related_seq_probs = self._all_related_word_probs(nearby_seq_probs)
        all_related_seq_probs.sort(key=lambda x: -x[1])
        return all_related_seq_probs


class Node:
    """  Class for representing nodes on the trie  """

    def __init__(self, letter, parent_word, counts=0):
        """  
            Initialization for the Node class requires a letter and a string
            containing the prior letters in the word the node is representing
        """
        self.children = []
        self.letter = letter
        self.word = parent_word + letter
        self.word_counts = counts
    
    def add_children(self, nodes):
        """Add *nodes* (a list of nodes) as children to a node instance"""
        self.children.extend(nodes)

    def add_child(self, node):
        """  Add a node as a child to a node instance  """
        self.children.append(node)

    def child(self, letter):
        """  
            Locate the child of a node represented by a particular letter
            or return None of no child exists
        """
        for child in self.children:
            if child.letter == letter:
                return child
        return None

    def increment_count(self, increment):
        """  Increment the number of appeaances of a node by 'increment'  """
        self.word_counts = self.word_counts + increment

def generate_vocabulary(corpus):
    """  
        Given any python iterable (that contains a representation of words or
        sentences), return a dictionary mapping words to the number of time that
        word appears
    """
    vocab = defaultdict(int)
    for word in corpus:
        if len(word) > 2 or re.search('[a-zA-Z0-9]', word[0]):
            word = word.lower()
            vocab[word] += 1
    return vocab

def store_trie(trie):
    """
        Store the representation *trie*, an instance of class Trie, in the db
        Returns True if successful and False otherwise.
    """
    return persist.write_trie(trie)

def run_interpreter(trie):
    """
        Run an interpreter for a trie that repeatedly asks for prefixes to Enter
        and returns the top 5 most common words given that particular prefix
    """

    inp = ""
    while inp != 'quit()':
        print "Enter a valid prefix to find the most common words given that prefix"
        print "as well as the most likely word attempted to spell given the prefix"
        print "Enter quit() to exit"
        inp = raw_input('> ')
        if inp == 'quit()':
            return
        os.system('clear')
        s = time.time()
        ret_list = trie.all_words_with_prefix(inp.lower())
        print "Search time:", time.time() - s
        ret_list.sort(key=lambda x: -x[1]) # Sort from greatest to least
        num_to_print = min(5, len(ret_list))
        if num_to_print == 0:
            print "No words were found..."
        for i in xrange(num_to_print):
            print str(i+1)+'. ' + str(ret_list[i][0]) + ' - ' + str(ret_list[i][1])
        nearby_words = trie.local_word_probs(inp.lower())
        nearby_words.sort(key=lambda x: -x[1])
        num_to_print = min(5, len(nearby_words))
        print "\nProbability of attempt at spelling particular word"
        for i in xrange(num_to_print):
            print str(i+1)+'. ' + str(nearby_words[i][0]) + ' - ' + str(nearby_words[i][1])

       
def create_trie(training_data=""):
    """
        An outer function used for instantiating a Trie from another module.
        Either takes input training data or builds from the first 50000 
        sentences of the Brown corpus
    """

    print "Loading..."
    if training_data:
        if type(training_data) != str:
            training_data = " ".join(training_data)
        training_set = nltk.tokenize.word_tokenize(training_data)
    else:
        training_set = brown.sents()[:50000]
        training_set = [word for sentence in training_set for word in sentence]
    vocabulary = generate_vocabulary(training_set)
    T = Trie(vocabulary)
    return T

def main():
    """
        If instantiating from command line, either build the Trie from the 
        first 50,000 sentences of the Brown corpus or through a file specified
        on the command line.  Once built, run an interpreter with the Trie.
    """

    parser = argparse.ArgumentParser(description="Give the most common word given a prefix")
    parser.add_argument("data", nargs="?")
    parser.add_argument("-db", action="store_true")
    args = parser.parse_args()

    print "Loading..."
    if args.db:
        T = Trie({})
        T.create_from_db()
        run_interpreter(T)
        return

    if not args.data:
        training_set = brown.sents()[:50000]
        training_set = [word for sentence in training_set for word in sentence]
    else: # Want to read from a file or string
        if os.path.exists(args.data):
            with open(args.data, "r") as f:
                training_set = nltk.tokenize.word_tokenize(f.read())
        else:
            training_set = nltk.tokenize.word_tokenize(args.data)
    vocabulary = generate_vocabulary(training_set)
    T = Trie(vocabulary)
    run_interpreter(T)

if __name__ == "__main__":
    main()
