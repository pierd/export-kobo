# export-kobo
A Python tool to export annotations and highlights from a Kobo SQLite file as Markdown.

**Tested with Kobo Clara Colour**

## Usage

```bash
$ # print all books with annotations/highlights
$ python3 export-kobo.py KoboReader.sqlite --list

$ # export annotations and highlights for a book as Markdown
$ python3 export-kobo.py KoboReader.sqlite --bookid 12

$ # export with debug information (position, timestamps, etc.)
$ python3 export-kobo.py KoboReader.sqlite --bookid 12 --debug

$ # export with custom color labels
$ python3 export-kobo.py KoboReader.sqlite --bookid 12 --colors "yellow,red,blue,green"

$ # export without color marks
$ python3 export-kobo.py KoboReader.sqlite --bookid 12 --no-colors

$ # print the help
$ python3 export-kobo.py --help
```

#### Example output

```bash
$ python3 export-kobo.py KoboReader.sqlite --list
ID   AUTHOR                         TITLE
--------------------------------------------------------------------------------
1    Lewis Carroll                  Alice in Wonderland
2    Herman Melville                Moby Dick
...
```

```markdown
$ python3 export-kobo.py KoboReader.sqlite --bookid 1
---
title: Alice in Wonderland
author: Lewis Carroll
---
# "Alice in Wonderland" by Lewis Carroll

### CHAPTER II. The Pool of Tears

> 🟡 "Curiouser and curiouser!" cried Alice (she was so much surprised, that for the moment she quite forgot how to speak good English);

> 🔴 Poor Alice!

- My annotation about this passage
```

## Installation

1. Clone this repository:
    ```bash
    $ git clone https://github.com/pierd/export-kobo
    ```

2. Enter the directory where ``export-kobo.py`` is:
    ```bash
    $ cd export-kobo
    ```

3. Copy in the same directory the ``KoboReader.sqlite`` file
   from the ``.kobo/`` hidden directory of the USB drive
   that appears when you plug your Kobo device to the USB port of your PC.
   You might need to enable the ``View hidden files`` option
   in your file manager to see the hidden directory;
   Example command to copy the SQL file from the Kobo Reader on macOS and Linux:
   ```bash
   $ cp /Volumes/KOBOeReader/.kobo/KoboReader.sqlite ./
   ```

4. Now you can run the script as explained above, for example:
    ```bash
    $ python3 export-kobo.py KoboReader.sqlite --list
    ```

## Notes

1. Bear in mind that no official specifications are published by Kobo,
   hence the script works as far as
   my understanding of the database structure of ``KoboReader.sqlite`` is correct,
   and its schema remains the same.

2. Although the ``KoboReader.sqlite`` file is opened in read-only mode,
   it is advisable to make a copy of it on your PC
   and export your notes from this copy,
   instead of directly accessing the file on your Kobo eReader device.

## Difference from Original Version

Totally revamped for my own use.

## Acknowledgments

[Elia Scotto](https://www.scotto.me) for the [original version](https://github.com/eliascotto/export-kobo).
