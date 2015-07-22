#! /bin/python
#from __future__ import print_function

import pyuv
import signal
import sys
import os
import sh
import optparse
import datetime
import pygit2
import dulwich.repo
import dulwich.diff_tree


cwd = os.getcwd()

shgit = sh.git.bake(_cwd=cwd)
shclangformat = sh.Command('clang-format')

user_name = ""
user_mail = ""
for line in pygit2.Config.get_global_config().get_multivar('user.name'):
	 # shgit.config('--get', 'user.name', _iter=True):
	user_name += line
for line in pygit2.Config.get_global_config().get_multivar('user.email'):
	 # shgit.config('--get', 'user.email', _iter=True):
	user_mail += line
print user_name, user_mail

g2repo = pygit2.Repository(cwd)
dwrepo = dulwich.repo.Repo(cwd)


def g2_create_branch(branchname):
	git = g2repo
	branch = git.create_branch(branchname, git.head.get_object())
	ref = git.lookup_reference(branch.name)
	git.checkout(ref)


def dw_commit_file(filename, kind):
	message = 'gitwatch autocommit (dulwich)\n{0} {1}'.format(kind, filename)

	git = dwrepo
	staged = map(str,[filename])
	git.stage( staged )
	index = git.open_index()

	try:
		committer = git._get_user_identity()
	except ValueError:
		committer = user_name + ' <' + user_mail + '>'

	try:
		head = git.head()
	except KeyError:
		return git.do_commit(message, committer=committer)

	changes = list(dulwich.diff_tree.tree_changes(git, index.commit(git.object_store), git['HEAD'].tree))
	if changes and len(changes) > 0:
		return git.do_commit(message, committer=committer)
	return None

def g2_commit_file(filename, kind):
	message = 'gitwatch autocommit (pygit2)\n{0} {1}'.format(kind, filename)

	git = g2repo
	index = git.index
	index.read()
	index.add(filename)
	index.write();

	for entry in index:
		print "added %s %s to index" % (entry.path, entry.hex)

	status = git.status()
	try:
		status[filename]
	except KeyError:
		# If there is nothing different since last save, git status will report no difference.
		return None

	try:
		HEAD = git.revparse_single('HEAD')
		parents = [HEAD.hex]
	except KeyError:
		parents = []

	commit = git.create_commit(
		'HEAD',
		pygit2.Signature(user_name, user_mail),
		pygit2.Signature(user_name, user_mail),
		message,
		index.write_tree(),
		parents
	)

"""
def commit_old(filename):
	repo.index.read()
	print repo.status()
	status = repo.status_file(filename)
	print(status)
	if status in [pygit2.GIT_STATUS_CURRENT, pygit2.GIT_STATUS_IGNORED]:
		pass
	elif status in [pygit2.GIT_STATUS_INDEX_NEW, pygit2.GIT_STATUS_INDEX_MODIFIED, pygit2.GIT_STATUS_INDEX_DELETED]:
		repo.index.add(filename)
		repo.index.write()
		tree = repo.index.write_tree()
		message = "Autocommit"

		ref = repo.create_reference('HEAD', repo.head.get_object().hex).resolve()
		oid = repo.create_commit(ref, author, committer, message, tree,[repo.head.get_object().hex])
		repo.index.write()

	elif status in [pygit2.GIT_STATUS_WT_NEW, pygit2.GIT_STATUS_WT_MODIFIED, pygit2.GIT_STATUS_WT_DELETED]:
		pass
	elif status in [pygit2.GIT_STATUS_CONFLICTED]:
		assert(False)
	else:
		assert(False)
"""

def fsevent_callback(fsevent_handle, filename, events, error):
	if error is not None:
		txt = 'error %s: %s' % (error, pyuv.errno.strerror(error))
	else:
		filename = os.path.relpath(os.path.join(fsevent_handle.path, filename), g2repo.workdir)
		if '.git/' in filename:
			return
		evts = []
		if events & pyuv.fs.UV_RENAME:
			evts.append('rename')
		if events & pyuv.fs.UV_CHANGE:
			evts.append('change')
		txt = 'events: %s' % ', '.join(evts)
	print('file: %s, %s' % (filename, txt))
	g2_commit_file(filename, 'added')




def sig_cb(handle, signum):
	handle.close()


def main(path):
	loop = pyuv.Loop.default_loop()
	try:
		fsevents = pyuv.fs.FSEvent(loop)
		fsevents.start(path, 4, fsevent_callback)	#pyuv.fs.UV_FS_EVENT_RECURSIVE
		fsevents.ref = False
	except pyuv.error.FSEventError as e:
		print('error: %s' % e)
		sys.exit(2)
	signal_h = pyuv.Signal(loop)
	signal_h.start(sig_cb, signal.SIGINT)
	print('Watching path %s' % os.path.abspath(path))
	loop.run()


if __name__ == '__main__':
	parser = optparse.OptionParser()
	parser.add_option('-p', '--path', help='a path to watch', default='.')
	opts, args = parser.parse_args()
	#print git.status()
	branch = 'gitwatch/session-{0}'.format(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M'))
	print 'running on branch', branch
	g2_create_branch(branch)
	main(opts.path)
