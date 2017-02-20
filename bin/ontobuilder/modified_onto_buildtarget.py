
# Python imports.
import os
from ontology import Ontology
from buildtarget import BuildTarget
from onto_buildtarget import OntoBuildTarget
from inferred_axiom_adder import InferredAxiomAdder

# Java imports.


class ModifiedOntoBuildTarget(BuildTarget):
    """
    Manages the process of building an "modified" ontology from the standard
    compiled ontology.  In this case, "modified" means either with imports
    merged into the main ontology, with inferred axioms added, or both.
    """
    def __init__(self, config, args):
        """
        config: An OntoConfig instance.
        args: A "struct" of configuration options (typically, parsed
            command-line arguments).  The supported members are 'merge_imports'
            and 'reason', which must both be booleans.
        """
        BuildTarget.__init__(self)

        self.config = config
        self.mergeimports = args.merge_imports
        self.prereason = args.reason

        self.obt = OntoBuildTarget(self.config, args)

        # If we have nothing to do, then there are no dependencies.
        if self.mergeimports or self.prereason:
            self.addDependency(self.obt)

    def _retrieveAndCheckFilePaths(self):
        """
        Verifies that all files and directories needed for the build exist.
        """
        # Verify that the main ontology file exists.
        fpath = self.obt.getOutputFilePath()
        if not(os.path.isfile(fpath)):
            raise RuntimeError(
                'The main compiled ontology file could not be found: {0}.'.format(fpath)
            )

        # Verify that the build directory exists.
        destdir = os.path.dirname(self.getOutputFilePath())
        if not(os.path.isdir(destdir)):
            raise RuntimeError(
                'The destination directory for the ontology does not exist: {0}.'.format(destdir)
            )

    def getOutputFilePath(self):
        """
        Returns the path of the enhanced ontology file.
        """
        main_ontpath = self.obt.getOutputFilePath()
        destpath = main_ontpath

        # If we are merging the imports into the ontology, modify the file name
        # accordingly.
        if self.mergeimports:
            parts = os.path.splitext(destpath)
            destpath = parts[0] + '-merged' + parts[1]

        # If we are adding inferred axioms to the ontology, modify the file
        # name accordingly.
        if self.prereason:
            parts = os.path.splitext(destpath)
            destpath = parts[0] + '-reasoned' + parts[1]

        return destpath

    def getBuildNotRequiredMsg(self):
        return 'The compiled ontology files are already up to date.'

    def _isBuildRequired(self):
        """
        Checks if the modified ontology already exists, and if so, whether file
        modification times indicate that the modified ontology is already up to
        date.  Returns True if the modified ontology needs to be updated.
        """
        # If neither modification is requested, then no build is required.
        if not(self.mergeimports) and not(self.prereason):
            return False

        foutpath = self.getOutputFilePath()
        main_ontpath = self.obt.getOutputFilePath()

        if os.path.isfile(foutpath):
            # If the main ontology file is newer than the compiled ontology, a
            # new build is needed.
            if os.path.isfile(main_ontpath):
                mtime = os.path.getmtime(foutpath)

                return mtime < os.path.getmtime(main_ontpath)
            else:
                # If the main ontology file does not exist, a build is
                # required.
                return True
        else:
            # If the modified ontology file does not exist, a build is
            # obviously required.
            return True

    def _run(self):
        """
        Runs the build process and produces a new, modified version of the main
        OWL ontology file.
        """
        if not(self._isBuildRequired()):
            return

        self._retrieveAndCheckFilePaths()

        mainont = Ontology(self.obt.getOutputFilePath())

        if self.mergeimports:
            # Merge the axioms from each imported ontology directly into this
            # ontology (that is, do not use import statements).
            print 'Merging all imported ontologies into the main ontology...'
            for importIRI in mainont.getImports():
                mainont.mergeOntology(importIRI)

        if self.prereason:
            print 'Checking whether the ontology is logically consistent...'
            entcheck_res = mainont.checkEntailmentErrors()
            if not(entcheck_res['is_consistent']):
                raise RuntimeError(
                    'The ontology is inconsistent (that is, it has no \
models).  This is often caused by the presence of an individual (that is, a \
class instance) that is explicitly or implicitly a member of two disjoint \
classes.  It might also indicate an underlying modeling error.  You must \
correct this problem before inferred axioms can be added to the ontology.'
                )

            print 'Running reasoner and adding inferred axioms...'
            inf_types = self.config.getInferenceTypeStrs()
            annotate_inferred = self.config.getAnnotateInferred()
            iaa = InferredAxiomAdder(mainont, self.config.getReasonerStr())
            iaa.addInferredAxioms(inf_types, annotate_inferred)

        # Write the ontology to the output file.
        fileoutpath = self.getOutputFilePath()
        print 'Writing compiled ontology to ' + fileoutpath + '...'
        mainont.saveOntology(fileoutpath)

