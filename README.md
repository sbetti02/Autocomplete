# Autocomplete

Takes a prefix and returns the most common words that start with the given prefix. A trie is created which represents English words learned from the first 50,000 sentences of the Brown corpus. 

Counters keep track of the number of times each word has been encountered so that only the top results are returned.

Note that the `brown` corpus must be downloaded through nltk for the program to operate correctly

## TODO
- [ ] Work on serializing trie structure for quick startup
- [ ] Allow updating word counts based on user 
- [ ] Look into slick integration with [Readline library](https://docs.python.org/2/library/readline.html)
