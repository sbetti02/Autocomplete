import nltk.tokenize
from nltk.corpus import brown
from collections import defaultdict
import re
from operator import itemgetter
import argparse
import os

class Trie:
    def __init__(self, vocab):
        self.root = Node("", "")
        self.vocabulary = vocab
        self.generateTrie()

    def generateTrie(self):
        for word in self.vocabulary:
            self.addWord(word)

    def addWord(self, word):
        currNode = self.root
        currWord = ""
        wordCount = self.vocabulary[word]
        for letter in word:
            fullWord = currWord + letter
            childNode = currNode.child(letter)
            if not childNode:
                childNode = Node(letter, currWord)
                currNode.addChild(childNode)
            currWord = fullWord
            currNode = childNode
            if fullWord == word:
                childNode.incrementCount(wordCount)

    def allWordsWithPrefix(self, string):
        currNode = self.findNode(string.lower())
        return self.wordsFromNode(currNode)

    def wordsFromNode(self, node):
        prefixedWords = []
        if node.wordCounts:
            prefixedWords.append([node.word, node.wordCounts])
        for child in node.children:
            prefixedWords.extend(self.wordsFromNode(child))
        return prefixedWords

    def findNode(self, string):
        currNode = self.root
        currWord = ""
        for letter in string:
            fullWord = currWord + letter
            childNode = currNode.child(letter)
            if not childNode:
                newNode = Node(letter, currWord)
                currNode.addChild(newNode)
                currNode = newNode
            else:
                currNode = childNode
            currWord = fullWord
        return currNode

    def printTrieHelper(self, currNode):
        if currNode.wordCounts:
            print currNode.word, currNode.wordCounts
        for child in currNode.children:
            self.printTrieHelper(child)

    def printTrie(self):
        self.printTrieHelper(self.root)

class Node:
    def __init__(self, letter, parentWord):
        self.children = []
        self.letter = letter
        self.word = parentWord + letter
        self.wordCounts = 0
    
    def addChild(self, node):
        self.children.append(node)

    def child(self, letter):
        for child in self.children:
            if child.letter == letter:
                return child
        return None

    def incrementCount(self, increment):
        self.wordCounts = self.wordCounts + increment

# Takes any python iterable
def generateVocabulary(corpus):
    vocab = defaultdict(int)
    for word in corpus:
        if len(word) > 2 or re.search('[a-zA-Z0-9]', word[0]):
            word = word.lower()
            vocab[word] += 1
    return vocab

def runInterpreter(trie):
    inp = ""
    while inp != 'q':
        print "Enter a valid prefix to find the most common words given that prefix"
        inp = raw_input()
        retList = trie.allWordsWithPrefix(inp)
        retList.sort(key=lambda x: -x[1]) # Sort from greatest to least
        print retList[:5]
       

def createTrie(trainingData=""):
    print "Loading..."
    if trainingData:
        if type(trainingData) != str:
            trainingData = " ".join(trainingData)
        trainingSet = nltk.tokenize.word_tokenize(trainingData)
    else:
        trainingSet = brown.sents()[:50000]
        trainingSet = [word for sentence in trainingSet for word in sentence]
    vocabulary = generateVocabulary(trainingSet)
    T = Trie(vocabulary)
    runInterpreter(T)

def main():
    parser = argparse.ArgumentParser(description="Give the most common word given a prefix")
    parser.add_argument("data", nargs="?")
    args = parser.parse_args()

    print "Loading..."
    if not args.data:
        trainingSet = brown.sents()[:50000]
        trainingSet = [word for sentence in trainingSet for word in sentence]
    else:
        if os.path.exists(args.data):
            with open(args.data, "r") as f:
                trainingSet = nltk.tokenize.word_tokenize(f.read())
        else:
            trainingSet = nltk.tokenize.word_tokenize(args.data)

    vocabulary = generateVocabulary(trainingSet)
    T = Trie(vocabulary)
    runInterpreter(T)

if __name__ == "__main__":
    main()
