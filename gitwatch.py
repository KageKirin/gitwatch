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

global_message = ""

g2repo = pygit2.Repository(cwd)

def g2_get_file_change_kind(filename):
	git = g2repo
	status = git.status()
	try:
		status[filename]
	except KeyError:
		# If there is nothing different since last save, git status will report no difference.
		return "null change"

	fstatus = git.status_file(filename)
	#print(fstatus)
	#print pygit2.GIT_STATUS_CURRENT, pygit2.GIT_STATUS_IGNORED, pygit2.GIT_STATUS_INDEX_NEW, pygit2.GIT_STATUS_INDEX_MODIFIED, pygit2.GIT_STATUS_INDEX_DELETED, pygit2.GIT_STATUS_WT_MODIFIED, pygit2.GIT_STATUS_WT_DELETED
	if fstatus in [pygit2.GIT_STATUS_CURRENT, pygit2.GIT_STATUS_IGNORED]:
		return "null change"
	elif fstatus in [pygit2.GIT_STATUS_INDEX_NEW, pygit2.GIT_STATUS_WT_NEW]:
		return "added"
	elif fstatus in [pygit2.GIT_STATUS_INDEX_MODIFIED, pygit2.GIT_STATUS_WT_MODIFIED]:
		return "updated"
	elif fstatus in [pygit2.GIT_STATUS_INDEX_DELETED, pygit2.GIT_STATUS_WT_DELETED]:
		return "removed"
	#elif status in [pygit2.GIT_STATUS_CONFLICTED]:
	#	assert(False)
	#else:
	#	assert(False)

	return "null change"


def g2_create_branch(branchname):
	git = g2repo
	branch = git.lookup_branch(branchname)
	if branch == None:
		branch = git.create_branch(branchname, git.head.get_object())
	ref = git.lookup_reference(branch.name)
	git.checkout(ref)




def g2_add_file(filename, kind):
	git = g2repo
	status = git.status()
	global global_message
	if filename in status:
		try:
			status[filename]
			index = git.index
			index.read()
			index.add(filename)
			index.write();
			tmp = global_message
			global_message = '{0}{1}'.format(tmp, ('{0} {1} [gitwatch autocommit]\n'.format(kind, filename)))

		except KeyError:
			# If there is nothing different since last save, git status will report no difference.
			return None


def g2_commit_file():
	global global_message
	message = global_message
	global_message = ""

	git = g2repo
	#for entry in index:
	#	print "added %s %s to index" % (entry.path, entry.hex)

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
		git.index.write_tree(),
		parents
	)

timer = pyuv.Timer(pyuv.Loop.default_loop())

def fsevent_callback(fsevent_handle, filename, events, error):
	filename = os.path.relpath(os.path.join(fsevent_handle.path, filename), g2repo.workdir)

	if '.git/' in filename:
		return

	if not os.path.exists(filename):
		return

	if error is not None:
		txt = 'error %s: %s' % (error, pyuv.errno.strerror(error))
	else:
		evts = []
		if events & pyuv.fs.UV_RENAME:
			evts.append('rename')
		if events & pyuv.fs.UV_CHANGE:
			evts.append('change')
		txt = 'events: %s' % ', '.join(evts)

	kind = g2_get_file_change_kind(filename)
	print('file: %s, %s, %s' % (filename, txt, kind))
	g2_add_file(filename, kind)
	print 'starting timer. committing in 30s'
	timer.stop()
	timer.start(timer_callback, 30, 0)

def timer_callback(timer_handle):
	print 'committing current index'
	g2_commit_file()


def sig_cb(handle, signum):
	handle.close()
	print ''
	print "and now, his watch has ended."


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
	parser.add_option('-c', '--continue', dest='newbranch', action='store_false', help='continue watch in current branch', default=True)
	opts, args = parser.parse_args()
	#print git.status()
	#print opts
	#print args

	if opts.newbranch:
		branch = 'gitwatch/session-{0}'.format(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M'))
		print 'Code gathers, and now my watch begins on', branch, '.'
		print 'For your code is dark, and full of horrors.'
		g2_create_branch(branch)
	main(opts.path)
