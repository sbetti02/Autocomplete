from nltk.corpus import brown
from collections import defaultdict
import re
from operator import itemgetter

class Trie:
    def __init__(self, vocab):
        self.root = Node("", "", 0)
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
                childNode = Node(letter, currWord, fullWord in self.vocabulary)
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
        if node.isWord:
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
                newNode = Node(letter, currWord, fullWord in self.vocabulary)
                currNode.addChild(newNode)
                currNode = newNode
            else:
                currNode = childNode
            currWord = fullWord
        return currNode

    def printTrieHelper(self, currNode):
        if currNode.isWord:
            print currNode.word, currNode.wordCounts
        for child in currNode.children:
            self.printTrieHelper(child)

    def printTrie(self):
        self.printTrieHelper(self.root)

class Node:
    def __init__(self, letter, parentWord, isWord):
        self.children = []
        self.letter = letter
        self.word = parentWord + letter
        self.wordCounts = 0
        self.isWord = isWord
    
    def addChild(self, node):
        self.children.append(node)

    def child(self, letter):
        for child in self.children:
            if child.letter == letter:
                return child
        return None

    def incrementCount(self, increment):
        self.wordCounts = self.wordCounts + increment

def generateVocabulary(corpus):
    vocab = defaultdict(int)
    for sentence in corpus:
        for word in sentence:
            if len(word) <= 2 and not re.search('[a-zA-Z0-9]', word[0]):
                continue
            word = word.lower()
            vocab[word] = vocab[word] + 1
    return vocab


def main():
    print "Loading..."
    trainingSet = brown.sents()[:50000]
    vocabulary = generateVocabulary(trainingSet)
    T = Trie(vocabulary)
    inp = ""
    while inp != 'q':
        print "Enter a valid prefix to find the most common associated words"
        inp = raw_input()
        retList = T.allWordsWithPrefix(inp)
        retList.sort(key=lambda x: -x[1]) # Sort from greatest to least
        print retList[:5]

if __name__ == "__main__":
    main()
