# Copyright 2009-2013 Justin Riley
#
# This file is part of StarCluster.
#
# StarCluster is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# StarCluster is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with StarCluster. If not, see <http://www.gnu.org/licenses/>.

import os
import posixpath

from starcluster import utils
from starcluster import static
from starcluster import exception
from starcluster import clustersetup
from starcluster.logger import log


class AdminUsers(clustersetup.DefaultClusterSetup):
    """
    Plugin for adding users to sudoers
    """

    def __init__(self, num_users=None, usernames=None):
        if usernames:
            usernames = [user.strip() for user in usernames.split(',')]
        if num_users:
            try:
                num_users = int(num_users)
            except ValueError:
                raise exception.BaseException("num_users must be an integer")
        elif usernames:
            num_users = len(usernames)
        else:
            raise exception.BaseException(
                "you must provide num_users or usernames or both")
        if usernames and num_users and len(usernames) != num_users:
            raise exception.BaseException(
                "only %d usernames provided - %d required" %
                (len(usernames), num_users))
        self._num_users = num_users
        if not usernames:
            usernames = ['user%.3d' % i for i in range(1, num_users + 1)]
        self._usernames = usernames

        super(AdminUsers, self).__init__()
    
    def run(self, nodes, master, user, user_shell, volumes):
        self._nodes = nodes
        self._master = master
        self._user = user
        self._user_shell = user_shell
        self._volumes = volumes
        log.info("Creating %d admin cluster users" % self._num_users)
        print("Creating %d admin cluster users" % self._num_users)
        for node in nodes:
            #for admin_user in self._usernames:
            #    node.ssh.execute("echo '%s ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/%s; chmod 0440 /etc/sudoers.d/* ; usermod -G admin %s " % (admin_user,admin_user.replace('.','_'),admin_user))
            for admin_user in self._usernames:
                self.pool.simple_job(node.ssh.execute,
                                    ("echo '%s ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/%s; chmod 0440 /etc/sudoers.d/* ; usermod -G admin %s " % (admin_user,admin_user.replace('.','_'),admin_user)),
                                     jobid=node.alias)
        numtasks = len(nodes)*self._num_users
        #print("Creating %d admin cluster users" % numtasks)
        self.pool.wait(numtasks=numtasks)


    def on_add_node(self, node, nodes, master, user, user_shell, volumes):
        self._nodes = nodes
        self._master = master
        self._user = user
        self._user_shell = user_shell
        self._volumes = volumes
        log.info("Creating %d admin users on %s" % (self._num_users, node.alias))
        for admin_user in self._usernames:
            node.ssh.execute("echo '%s ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/%s; chmod 0440 /etc/sudoers.d/* ; usermod -G admin %s " % (admin_user,admin_user,admin_user))
    
    def on_remove_node(self, node, nodes, master, user, user_shell, volumes):
        raise NotImplementedError('on_remove_node method not implemented')
