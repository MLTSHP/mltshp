from fabric.api import *

env.use_shell = False # to avoid password prompt for sudo.
#env.hosts = ['ec2-50-16-114-84.compute-1.amazonaws.com']
env.user = 'ubuntu'
#env.password = 'asdf'

def buildserver():
    put('new-server.sh', '.')
    run('chmod 755 new-server.sh')
    run('./new-server.sh')
