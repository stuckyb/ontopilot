
# Python imports.
from ontobuilder import logger
from ontology import Ontology
from buildtarget import BuildTargetWithConfig
from onto_buildtarget import OntoBuildTarget

# Java imports.


class ErrorCheckBuildTarget(BuildTargetWithConfig):
    """
    A build target that checks the main ontology file for common entailment
    errors, including inconsistency and incoherence.
    """
    def __init__(self, args, config=None):
        """
        args: A "struct" of configuration options (typically, parsed
            command-line arguments).  The required members are
            'no_def_expand' (boolean) and 'config_file' (string).
        config (optional): An OntoConfig instance.
        """
        BuildTargetWithConfig.__init__(self, args, config)

        self.obt = OntoBuildTarget(args, self.config)

        self.addDependency(self.obt)

    def _isBuildRequired(self):
        """
        This always returns True, because if the user is requesting an
        entailments check, we should try to do so.
        """
        return True

    def _run(self):
        """
        Checks for entailment errors in the main ontology.
        """
        mainont = Ontology(self.obt.getOutputFilePath())

        logger.info('Checking for entailment errors...')
        entcheck_res = mainont.checkEntailmentErrors()

        if not(entcheck_res['is_consistent']):
            logger.info(
                '\nERROR: The ontology is inconsistent (that is, it has no '
                'models).  This is often caused by the presence of an '
                'individual (that is, a class instance) that is explicitly or '
                'implicitly a member of two disjoint classes.  It might also '
                'indicate an underlying modeling error.  Regardless, it is a '
                'serious problem because an inconsistent ontology cannot be '
                'used for logical inference.\n'
            )
        else:
            class_list = entcheck_res['unsatisfiable_classes']
            if len(class_list) > 0:
                iri_strs = [ent.getIRI().toString() for ent in class_list]
                classes_str = '<' + '>\n<'.join(iri_strs) + '>'

                logger.info(
                    '\nERROR: The ontology is consistent but incoherent '
                    'because it contains one or more unsatisfiable classes.  '
                    'This usually indicates a modeling error.  The following '
                    'classes are unsatisfiable:\n' + classes_str + '\n'
                )
            else:
                logger.info(
                    '\nThe ontology is consistent and coherent.  No '
                    'entailment problems were found.\n'
                )

