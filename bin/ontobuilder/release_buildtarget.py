
# Python imports.
import os
import datetime
from ontology import Ontology
from buildtarget import BuildTargetWithConfig
from modified_onto_buildtarget import ModifiedOntoBuildTarget
from inferred_axiom_adder import InferredAxiomAdder
from collections import namedtuple

# Java imports.


class _ArgsType:
    """
    A simple "struct"-type class for copying arguments from another struct-type
    class (such as ArgumentParser objects).
    """
    def __init__(self, structobj):
        """
        The attributes from structobj will be copied to this object.
        """
        for key, value in vars(structobj).iteritems():
            setattr(self, key, value)


# Define a simple "struct" type for gathering file path and IRI information.
FileInfo = namedtuple(
    'FileInfo', ['sourcepath', 'destpath', 'oldIRI', 'destIRI', 'versionIRI']
)


class ReleaseBuildTarget(BuildTargetWithConfig):
    """
    Manages the process of building a complete release version of the compiled
    ontology and imports modules.
    """
    def __init__(self, args, config=None):
        """
        args: A "struct" of configuration options (typically, parsed
            command-line arguments).  The required members are 'merge_imports'
            (boolean), 'reason' (boolean), 'no_def_expand' (boolean), and
            'config_file' (string).
        config (optional): An OntoConfig instance.
        """
        BuildTargetWithConfig.__init__(self, args, config)

        # Each release will include a merged, prereasoned ontology file, a
        # merged, unreasoned ontology file, and an unmerged, unreasoned
        # ontology file.  So we need to set dependencies for each of those
        # build targets.
        newargs = _ArgsType(args)
        newargs.merge_imports = True
        self.mobt_merged = ModifiedOntoBuildTarget(newargs, self.config)

        newargs = _ArgsType(args)
        newargs.merge_imports = True
        newargs.reason = True
        self.mobt_merged_reasoned = ModifiedOntoBuildTarget(newargs, self.config)

        self.addDependency(self.mobt_merged)
        self.addDependency(self.mobt_merged_reasoned)

    def _generateReleaseDirPath(self):
        """
        Returns the path for the release directory.
        """
        datestr = datetime.date.today().isoformat()
        release_dir = os.path.join(
            self.config.getProjectDir(), 'releases', datestr
        )

        return release_dir

    def _generateImportFileInfo(self, sourcepath, old_iri):
        """
        Generates and returns a FileInfo object for a release import module
        file.

        sourcepath: The location of the source import module file.
        old_iri (str): The old (current) IRI of the import module.
        """
        release_dir = self._generateReleaseDirPath()

        # Get the path to the module, relative to the main project location.
        mod_relpath = os.path.relpath(sourcepath, self.config.getProjectDir())

        destpath = os.path.join(release_dir, mod_relpath)

        destIRI = self.config.generateReleaseIRI(mod_relpath)

        versionIRI = self.config.generateReleaseIRI(destpath)

        finfo = FileInfo(
            sourcepath=sourcepath, destpath=destpath, oldIRI=old_iri,
            destIRI=destIRI, versionIRI=versionIRI
        )

        return finfo

    def _generateOntologyFileInfo(self, sourcepath, suffix, is_main):
        """
        Generates and returns a FileInfo object for a release ontology file.

        sourcepath: The location of the source ontology file.
        suffix (str): The suffix to attach to the base ontology file name.
        is_main (bool): Whether this is the main ontology file.
        """
        release_dir = self._generateReleaseDirPath()

        # Parse the base ontology file name.
        ofnparts = os.path.splitext(
            os.path.basename(self.config.getOntologyFilePath())
        )

        destpath = os.path.join(
            release_dir, ofnparts[0] + suffix + ofnparts[1]
        )

        if is_main:
            destIRI = self.config.getReleaseOntologyIRI()
        else:
            destIRI = self.config.generateReleaseIRI(
                os.path.basename(destpath)
            )

        versionIRI = self.config.generateReleaseIRI(destpath)

        finfo = FileInfo(
            sourcepath=sourcepath, destpath=destpath, oldIRI='',
            destIRI=destIRI, versionIRI=versionIRI
        )

        return finfo

    def _generateBuildInfo(self):
        """
        Generates the paths and IRIs needed to build the release.  Sets three
        class attributes: release_dir, which the absolute local path of the
        release directory, and ont_fileinfos and imports_fileinfos, which are
        lists of FileInfo objects that describe how to build the release
        components.
        """
        # Parse the base ontology file name.
        ofnparts = os.path.splitext(
            os.path.basename(self.config.getOntologyFilePath())
        )

        # Gather the ontology file information.  Get the compiled main ontology
        # file path from one of the modified ontology dependencies.
        self.ont_fileinfos = []

        spath = self.mobt_merged.getOntoBuildTarget().getOutputFilePath()
        self.ont_fileinfos.append(
            self._generateOntologyFileInfo(spath, '-raw', False)
        )

        spath = self.mobt_merged.getOutputFilePath()
        self.ont_fileinfos.append(
            self._generateOntologyFileInfo(spath, '-merged', False)
        )

        spath = self.mobt_merged_reasoned.getOutputFilePath()
        self.ont_fileinfos.append(
            self._generateOntologyFileInfo(spath, '', True)
        )

        # Gather the imports file information.
        self.imports_fileinfos = []

        ibt = self.mobt_merged.getOntoBuildTarget().getImportsBuildTarget()
        importsinfos = ibt.getImportsInfo()
        for importsinfo in importsinfos:
            self.imports_fileinfos.append(
                self._generateImportFileInfo(
                    importsinfo.filename, importsinfo.iristr
                )
            )

    def getBuildNotRequiredMsg(self):
        return 'The release files are already up to date.'

    def _isBuildRequired(self):
        """
        Checks if all of the release files already exist.  If not, returns
        True.  Otherwise, checking the build status is deferred to the
        dependencies: if any dependencies require a build, then the release
        will automatically be built, too (this is automatically enforced by the
        base class).
        """
        self._generateBuildInfo()

        for fileinfo in (self.ont_fileinfos + self.imports_fileinfos):
            if not(os.path.isfile(fileinfo.destpath)):
                return True

        return False

    def _makeReleaseDirs(self, dirpath):
        """
        Attempts to create one or more directories in a path string.  If a
        non-directory file system object with same name already exists, or if
        directory creation fails for some other reason, an exception will be
        thrown.
        """
        if os.path.exists(dirpath):
            if not(os.path.isdir(dirpath)):
                raise RuntimeError(
                    'A file with the same name as the build folder/directory, '
                    '"{0}", already exists.  Please delete, move, or rename '
                    'the conflicting file before '
                    'continuing.'.format(dirpath)
                )

        if not(os.path.exists(dirpath)):
            try:
                os.makedirs(dirpath)
            except OSError:
                raise RuntimeError(
                    'The release folder/directory, "{0}", could not be '
                    'created.  Please make sure that you have permission to '
                    'create new files and directories in the project '
                    'location.'.format(dirpath)
                )

    def _run(self):
        """
        Runs the build process to produce a new ontology release.
        """
        # We don't need to run generateBuildInfo() here because the base class
        # ensures that _isBuildRequired() will always be called prior to this
        # method, so generateBuildInfo() will have already been run.

        release_dir = self._generateReleaseDirPath()

        # Create the main release directory, if needed.
        if not(os.path.exists(release_dir)):
            self._makeReleaseDirs(release_dir)

        # Get the path to the released imports modules directory and create it,
        # if needed.
        if len(self.imports_fileinfos) > 0:
            dirpath = os.path.dirname(self.imports_fileinfos[0].destpath)
            if not(os.path.exists(dirpath)):
                self._makeReleaseDirs(dirpath)

        # Create the release import module files.
        for fileinfo in self.imports_fileinfos:
            ont = Ontology(fileinfo.sourcepath)
            ont.setOntologyID(fileinfo.destIRI, fileinfo.versionIRI)
            ont.saveOntology(fileinfo.destpath)

        # Create the release ontology files.
        for fileinfo in self.ont_fileinfos:
            ont = Ontology(fileinfo.sourcepath)
            ont.setOntologyID(fileinfo.destIRI, fileinfo.versionIRI)

            # Update the IRIs of any released import modules that are
            # explicitly imported by the ontology.
            for ifinfo in self.imports_fileinfos:
                if ont.hasImport(ifinfo.oldIRI):
                    ont.updateImportIRI(ifinfo.oldIRI, ifinfo.versionIRI)

            ont.saveOntology(fileinfo.destpath)

