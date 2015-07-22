# gitwatch

A simple python script that will watch a folder within a git repository and commit every single file change.
I.e. every time you save, the current status gets committed.


## Usage

At the **root** of your repo:  
`gitwatch --path folder` or  
`gitwatch -p folder`.

E.g. `gitwatch -p .`


## Caveats

gitwatch will checkout a separate branch to commit the changes into it.
It's up to the user to rebase, squash or edit these commits by himself later on.

Stop the tool before doing any pulls, rebases, or merges.

Tested on OSX Yosemite.

Deleting files does not work yet, moving neither.


## Requirements (and dependencies)

- Dangling dependency on dulwich (to be removed later)
- Dangling dependency on sh (to be removed as well)
- pygit2, libgit2 (`brew install libgit2 && pip install pygit2`)
- pyuv, libuv (`brew install libuv && pip install pyuv`)
- the former requires glibtool (`brew install libtool`) to compile


## Acknowlegdements

[Autogit](https://github.com/chrisparnin/autogit) was a great help to get the Dulwich and pygit2 commits to run,
especially, [this file](https://github.com/chrisparnin/autogit/blob/master/Sublime%20Text/autogit.py).

## Further development

(Contact me if you want to take over the project)

- better commit messages, customizable commit messages
- more options or a `.gitwatch` config file
- JIRA support (time tracking, i.e. track time between commits, and add `JIRA-PROJECT-ID task-id #time <time-in-minutes>m` to commit message)
