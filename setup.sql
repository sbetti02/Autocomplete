/*
Schema for the trie table.
*/

CREATE TABLE trie (
    id INTEGER PRIMARY KEY,
    val TEXT NOT NULL,
    total INTEGER NOT NULL,
    parent INTEGER,
    FOREIGN KEY (parent) REFERENCES trie (id),
    UNIQUE (parent, val) ON CONFLICT FAIL
);
