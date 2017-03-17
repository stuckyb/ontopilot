#
# This package initialization script does five things:
#
#   1. Set the logging level for SLF4J's SimpleLogger.
#   2. Adds all required java library jar files to the classpath.
#   3. Initializes a Python logger object for printing status messages.
#   4. Define strings for recognizing yes/true values in input tables.
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
import os, glob, sys
import logging

# Java imports.
from java.lang import System


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


# Set the default logging level for the SLF4J SimpleLogger to suppress all
# messages below the "WARN" level so that the console doesn't fill up with
# "INFO" messages.  In testing, it appears that this system property needs to
# be set before the SLF4J packages are added to the classpath.  The key string
# for this property can be obtained from SimpleLogger.DEFAULT_LOG_LEVEL_KEY.
System.setProperty('org.slf4j.simpleLogger.defaultLogLevel', 'WARN')

# Get the paths to all of the java libraries needed by the OWL API and add them
# to the classpath.
scriptdir = os.path.dirname(os.path.realpath(__file__))
jlibdir = os.path.realpath(
        os.path.join(scriptdir, '..', '..', 'javalib', '*.jar')
    )
jlibpaths = glob.glob(jlibdir)
for jlibpath in jlibpaths:
    sys.path.append(jlibpath)

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
from errorcheck_buildtarget import ErrorCheckBuildTarget
from update_base_imports_buildtarget import UpdateBaseImportsBuildTarget
from buildtarget_manager import BuildTargetManager

