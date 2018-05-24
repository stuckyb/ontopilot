# Copyright (C) 2017 Brian J. Stucky
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#
# This package initialization script does five things:
#
#   1. Set the logging level for SLF4J's SimpleLogger.
#   2. Adds all required java library jar files to the classpath.
#   3. Initializes a Python logger object for printing status messages.
#   4. Defines strings for recognizing yes/true values in input tables.
#   5. Adds classes in package modules to the package's top-level scope.
#
# The directory "../../javalib" contains all of the java libraries on which the
# OWL API depends.  The easiest way to get all of these library jar files is to
# extract them from the OWL API distribution jar file (get the OSGI version).
# Unzip the jar file, then merge everything in the "lib" directory of the jar
# file into the "javalib" directory of the PPO source tree.  This will get
# almost everything you need except for a few additional libraries; get these
# from the existing "javalib" directory.  Finally, make sure that the OWL API
# main jar file is also in the "javalib" folder.
#

# Python imports.
from __future__ import unicode_literals
import os, glob, sys
import logging
import time

# Java imports.
from java.lang import System as JavaSystem


class CustomLogHandler(logging.StreamHandler):
    """
    Implements a custom StreamHandler for log messages that uses two different
    message formats: one for INFO messages, and another for everything else.
    The difference between the formats is that INFO messages are not prefixed
    with the log level name since they are intended to be normal UI console
    output, whereas all other log messages are prefixed with the level name.
    """
    def __init__(self):
        logging.StreamHandler.__init__(self)

        self.info_formatter = logging.Formatter('%(message)s')
        self.generic_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )

    def format(self, record):
        if record.levelname == 'INFO':
            return self.info_formatter.format(record)
        else:
            return self.generic_formatter.format(record)


def setLogLevel(level):
    """
    Attempts to set the logging level for all Python and Java loggers.
    Unfortunately, it appears to be impossible to programatically change the
    logging level of SLF4J's SimpleLogger (used by the OWL API) after the SLF4J
    library is added to the classpath, so this function applies to Pyton
    loggers and log4j.

    level: A logging level as defined in Python's logging package.
    """
    # Define log4j level constants that (approximately) correspond with Python
    # logging level constants.
    log4j_levels = {
        logging.CRITICAL: log4j.Level.FATAL,
        logging.ERROR: log4j.Level.ERROR,
        logging.WARNING: log4j.Level.WARN,
        logging.INFO: log4j.Level.INFO,
        logging.DEBUG: log4j.Level.DEBUG
    }

    logger.setLevel(level)
    log4j.Logger.getRootLogger().setLevel(log4j_levels[level])


# Set the default logging level for the SLF4J SimpleLogger to suppress all
# messages below the "WARN" level so that the console doesn't fill up with
# "INFO" messages.  In testing, it appears that this system property needs to
# be set before the SLF4J packages are added to the classpath.  The key string
# for this property can be obtained from SimpleLogger.DEFAULT_LOG_LEVEL_KEY.
JavaSystem.setProperty('org.slf4j.simpleLogger.defaultLogLevel', 'WARN')

# Add the paths to all of the required java libraries to the classpath.  If
# OntoPilot is run from a standalone JAR file, the java libraries will
# automatically be in the classpath, the java-lib directory will be
# non-existent, and jlibpaths will therefore be an empty list, so the classpath
# will not be modified here.
scriptdir = os.path.dirname(os.path.realpath(__file__))
jlibdir = os.path.realpath(
        os.path.join(scriptdir, '..', '..', 'java-lib', '*.jar')
    )
jlibpaths = glob.glob(jlibdir)
for jlibpath in jlibpaths:
    sys.path.append(jlibpath)

# Import Java logging components.  We first need to register the log4j JAR file
# using add_package() so we can do a package-level import.
sys.add_package('org.apache.log4j')
from org.apache import log4j

# Configure log4j and set the root logging level to WARN.  Without these lines,
# using the ELK reasoner (version 0.4.3) will trigger a warning about log4j not
# being configured, and then, once log4j is configured, it will print all
# messages to the console by default, so the logging level needs to be set.
log4j.BasicConfigurator.configure()
log4j.Logger.getRootLogger().setLevel(log4j.Level.WARN)

# Initialize the logger for this package.
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create the custom handler and apply it to the root logger.  If the custom
# handler is instead attached to the package logger, then logging  messages
# will be printed twice, once by the custom handler of the package logger and
# once by the root logger, which is obviously undesirable.
handler = CustomLogHandler()
handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(handler)

# Define string constants for recognizing yes/true values in input data.
TRUE_STRS = ('t', 'true', 'y', 'yes')

# Add top-level classes of contained modules that are used by UI code to the
# package's top-level scope.
from ontoconfig import ConfigError
from basic_buildtargets import InitTarget
from imports_buildtarget import ImportsBuildTarget
from onto_buildtarget import OntoBuildTarget
from modified_onto_buildtarget import ModifiedOntoBuildTarget
from release_buildtarget import ReleaseBuildTarget
from docs_buildtarget import DocsBuildTarget
from errorcheck_buildtarget import ErrorCheckBuildTarget
from update_base_imports_buildtarget import UpdateBaseImportsBuildTarget
from inferencepipeline_buildtarget import InferencePipelineBuildTarget
from findentities_buildtarget import FindEntitiesBuildTarget
from buildtarget_manager import BuildTargetManager

