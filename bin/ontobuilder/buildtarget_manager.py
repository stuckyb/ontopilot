#
# Provides high-level management of build targets.  Associates build target
# classes with target names and sets of command-line arguments and returns an
# instance of the appropriate build target after inspecting command-line
# argument values.
#

# Python imports.
import abc
from collections import namedtuple

# Java imports.


# Define a simple "struct"-like type for associating build target classes with
# target names and sets of command-line argument values.  The members are:
#   tclass: The target class.
#   name (string): The name to associate with the target.
#   argvals (dict): A dictionary of argname/value pairs.
TargetMap = namedtuple('TargetMap', 'tclass, name, argvals')


class BuildTargetManager:
    """
    Manages build targets.  Build targets are associated with target names and
    (optional) additional sets of command-line argument values, and when a
    matching target name and set of arguments is passed in by client code, the
    associated target is instantiated and returned.
    """
    def __init__(self):
        # The list of build target mappings.
        self.targetmaps = []

    def addBuildTarget(self, targetclass, targetname, **extra_args):
        """
        Adds a build target mapping.

        targetclass: The class of the build target.
        targetname: The name to associate with the build target.
        extra_args: Additional command-line argment values to map to the
            target.  This should be a dictionary of argname/value pairs.
        """
        targetmap = TargetMap(
            tclass=targetclass, name=targetname, argvals=extra_args
        )
        self.targetmaps.append(targetmap)

    def _getBuildTargetNames(self):
        """
        Returns a list of valid build target names.
        """
        tnames = list(set([tmap.name for tmap in self.targetmaps]))
        tnames.sort()

        return tnames

    def _getBuildTargetNamesStr(self):
        """
        Returns a string containing the valid build target names.
        """
        tnames = self._getBuildTargetNames()

        names_str = ''
        if len(tnames) == 1:
            names_str = '"' + tnames[0] + '"'
        elif len(tnames) == 2:
            names_str = '"' + '" or "'.join(tnames) + '"'
        elif len(tnames) > 2:
            names_str = '"' + '", "'.join(tnames[:len(tnames) - 1]) + '", '
            names_str += 'or "' + tnames[-1] + '"'

        return names_str

    def _getMatchingTargets(self, targetname, args):
        """
        Returns a list of all target maps that match the specified target name
        and argment values.  Supports partial matching of target names.  The
        target maps are returned sorted in descending order by the number of
        matching arguments.
        """
        matches = []

        for targetmap in self.targetmaps:
            if targetmap.name.startswith(targetname):
                # Count the total number of matching argument values.
                matching_argcnt = 0
                for argname in targetmap.argvals:
                    # Check if the attribute exists in the provided argument
                    # set.  Using hasattr() would require less code, but
                    # doesn't work well with properties.
                    has_arg = True
                    try:
                        getattr(args, argname)
                    except AttributeError:
                        has_arg = False

                    if (
                        has_arg and
                        (targetmap.argvals[argname] == getattr(args, argname))
                    ):
                        matching_argcnt += 1

                if matching_argcnt == len(targetmap.argvals):
                    matches.append(targetmap)

        # Sort the target maps by the number of matching arguments.
        matches.sort(
            key=lambda targetmap: len(targetmap.argvals), reverse=True
        )

        return matches

    def getBuildTarget(self, targetname, args):
        """
        Returns an instance of the specified build target.  If more than one
        build target has the same name, targets with the greatest number of
        additional command-line argument mappings will be matched first (that
        is, more specific target specifications will be matched before more
        general target specifications).
        """
        # Gather all target maps with matching target names and argument sets.
        matches = self._getMatchingTargets(targetname, args)

        targetmatch = None
        if len(matches) > 1:
            # Attempt to dis-ambiguate the target specification.  The matching
            # target maps will already be in descending order sorted by the
            # number of matching arguments, so we just need to see if the first
            # match has more arguments than the next.
            if len(matches[0].argvals) > len(matches[1].argvals):
                targetmatch = matches[0]
            else:
                tnames = list(set([tmapping.name for tmapping in matches]))
                tnames.sort()
                tnames_str = '"' + '", "'.join(tnames) + '"'
                raise RuntimeError(
                    'The specified build target, "{0}", matched more than one '
                    'build target name.  Please provide the full build target '
                    'name (or enough characters to disambiguate it).  The '
                    'following targets matched: {1}.'.format(
                        targetname, tnames_str
                    )
                )
        elif len(matches) == 1:
            targetmatch = matches[0]
        else:
            raise RuntimeError(
                'Unknown build target: "{0}".  Valid build target names are: '
                '{1}.'.format(targetname, self._getBuildTargetNamesStr())
            )

        target = targetmatch.tclass(args)

        return target

