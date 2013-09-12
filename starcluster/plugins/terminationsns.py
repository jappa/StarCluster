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

script_template="""
#! /bin/sh
### BEGIN INIT INFO
# Provides: ec2-terminate
# Required-Start: $network $syslog
# Required-Stop:
# Default-Start:
# Default-Stop:
# Short-Description: restart
# Description: send termination email
### END INIT INFO
#

export AWS_CONFIG_FILE=%(aws_config)s
export AWS_DEFAULT_REGION=%(aws_region)s # config file not picking up region for some reason
sudo -E aws sns publish --topic-arn=%(topic_arn)s --message="%(sns_message)s"
sleep 3 # make sure the message has time to send

exit 0
"""

aws_config="""
[default]
AWS_ACCESS_KEY_ID=%(aws_access_key)s
AWS_SECRET_ACCESS_KEY=%(aws_secret_key)s
"""

add_service_cmd="""
sudo chmod +x /etc/init.d/ec2-shutdown; sudo update-rc.d ec2-shutdown start 10 0 6 .
"""

install_awscli_cmd="""
sudo pip install awscli
"""


class TerminationSNS(clustersetup.DefaultClusterSetup):
    """
    Plugin for adding Amazon SNS notification in case of node shutdown
    
    """

    def __init__(self, topic_arn=None, message=None,
                 aws_access_key=None,
                 aws_secret_key=None,
                 aws_region=None):
        
        self._topic_arn = topic_arn
        self._message = message

        self._aws_access_key = aws_access_key
        self._aws_secret_key = aws_secret_key
        self._aws_region     = aws_region

        self._aws_config_location = '/etc/default/sns_config'

        super(TerminationSNS, self).__init__()
    
    def _install_service(self,node):
        node.ssh.execute(add_service_cmd)
    
    def _install_awscli(self,node):
        node.ssh.execute(install_awscli_cmd)
    
    def _write_aws_config(self,node):
        nconn = node.ssh
        aws_config = nconn.remote_file(self._aws_config_location)
        aws_config.write(self.generate_config_script())
        aws_config.close()
        
    
    def _write_init_script(self,node):
        nconn = node.ssh
        init_script = nconn.remote_file('/etc/init.d/ec2-shutdown')
        init_script.write(self.generate_init_script())
        init_script.close()
    
    def generate_config_script(self):
        return aws_config % dict(aws_access_key=self._aws_access_key,
                                 aws_secret_key=self._aws_secret_key)
    
    def generate_init_script(self):
        return script_template % dict(aws_config=self._aws_config_location,
                                      aws_region=self._aws_region,
                                      topic_arn=self._topic_arn,
                                      sns_message=self._message)
    
    def run(self, nodes, master, user, user_shell, volumes):
        self._nodes = nodes
        self._master = master
        self._user = user
        self._user_shell = user_shell
        self._volumes = volumes

        log.info("Adding SNS node termination notification ARN: %s" % self._topic_arn)

        for node in nodes:
            self.pool.simple_job(self._write_aws_config,(node),
                                 jobid=node.alias)
        self.pool.wait(len(nodes))
            
        for node in nodes:
            self.pool.simple_job(self._write_init_script,(node),
                                 jobid=node.alias)
        self.pool.wait(len(nodes))
        
        for node in nodes:
            self.pool.simple_job(self._install_awscli,(node),
                                 jobid=node.alias)
        self.pool.wait(len(nodes))
        
        for node in nodes:
            self.pool.simple_job(self._install_service,(node),
                                 jobid=node.alias)
        self.pool.wait(len(nodes))
        

    def on_add_node(self, node, nodes, master, user, user_shell, volumes):
        raise NotImplementedError('on_add_node method not implemented')
    
    def on_remove_node(self, node, nodes, master, user, user_shell, volumes):
        raise NotImplementedError('on_remove_node method not implemented')
