#!/bin/bash

# The location of the main OntoPilot program, relative to this launch script.
ONTOPILOTPATH="../python-src/ontopilot_main.py"

# The location of the Jython run-time JAR, relative to this launch script.
JYTHONPATH="../java-lib/jython-standalone-2.7.0.jar"

# The location of the Java run-time binary.  If no location is set, we assume
# that "java" is in the user's PATH somewhere.
JAVAPATH=


# Get the location of this launch script.  If the script was not run from a
# symlink, the next two lines are all we need.
SRCPATH=${BASH_SOURCE[0]}
SRCDIR=$(dirname ${SRCPATH})

# If SRCPATH is a symlink, resolve the link (and any subsequent links) until we
# arrive at the actual script location.
while [ -L "${SRCPATH}" ]; do
    SRCPATH=$(readlink ${SRCPATH})

    # If the link target is a relative path, it is relative to the original
    # symlink location, so we must construct a new path for the link target
    # based on SRCDIR (the original symlink location).
    if [ "${SRCPATH:0:1}" != "/" ]; then
        SRCPATH="${SRCDIR}/${SRCPATH}"
    fi

    SRCDIR=$(dirname ${SRCPATH})
done

# Check if java is installed.
if [ -z $JAVAPATH ]; then
    JAVAPATH="java"
fi
if ! command -v $JAVAPATH >/dev/null; then
    echo "ERROR: The Java run-time environment appears to be missing." >&2
    echo "Please install Java in order to run OntoPilot." >&2
    exit 1
fi

# Run OntoPilot, passing on all command-line arguments.
$JAVAPATH -jar "${SRCDIR}/${JYTHONPATH}" "${SRCDIR}/${ONTOPILOTPATH}" "$@"

