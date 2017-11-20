import nltk.tokenize
from nltk.corpus import brown
from collections import defaultdict
import re
from operator import itemgetter
import argparse
import os

class Trie:
    """
        The Trie class builds and maintains a trie, where each node represents 
        a different letter, and overall represents all of the words seen in 
        the given vocabulary.
    """

    def __init__(self, vocab):
        """ 
            Initializing function for the trie, creates structure 
            from given vocabulary dict 
        """
        self.root = Node("", "")
        self.vocabulary = vocab
        self.generate_trie()

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

class Node:
    """  Class for representing nodes on the trie  """
    
    def __init__(self, letter, parent_word):
        """  
            Initialization for the Node class requires a letter and a string
            containing the prior letters in the word the node is representing
        """
        self.children = []
        self.letter = letter
        self.word = parent_word + letter
        self.word_counts = 0
    
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

def run_interpreter(trie):
    """
        Run an interpreter for a trie that repeatedly asks for prefixes to Enter
        and returns the top 5 most common words given that particular prefix
    """
    inp = ""
    while inp != 'q':
        print "Enter a valid prefix to find the most common words given that prefix"
        inp = raw_input('> ')
        ret_list = trie.all_words_with_prefix(inp.lower())
        ret_list.sort(key=lambda x: -x[1]) # Sort from greatest to least
        print ret_list[:5]
       
def createTrie(training_data=""):
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
    args = parser.parse_args()

    print "Loading..."
    if not args.data:
        training_set = brown.sents()[:50000]
        training_set = [word for sentence in training_set for word in sentence]
    else:
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
