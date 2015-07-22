#! /bin/python

#import git
#repo = git.Repo( '.' )
#print repo.git.status()

#import sh
#git = sh.git.bake(_cwd='.')
#print git.status()

#import pygit2
#repo = pygit2.Repository('.')
#print repo.path
#print repo.status()

import dulwich.repo
repo = dulwich.repo.Repo('.')
print repo
index = repo.open_index()
print index
print list(index)
