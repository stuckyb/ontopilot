import java.io.FileInputStream;
import java.lang.System;
import java.util.Properties;
import java.util.Arrays;
import java.util.logging.Logger;
import java.util.logging.Level;

import org.python.core.Py;
import org.python.core.PyException;
import org.python.core.PyFile;
import org.python.core.PySystemState;
import org.python.util.PythonInterpreter;
import org.python.core.PlainConsole;


public class Main {
    public static void main(String[] args) throws PyException, Exception {
        Logger logger = Logger.getLogger("Main");

        // Use PlainConsole for all console I/O.  OntoPilot doesn't need the
        // more complicated features of JLineConsole.
        System.getProperties().setProperty(
            "python.console", "org.python.core.PlainConsole"
        );

        // To make the python interpreter accept arguments at the right index.
        String[] args_new = new String[args.length + 1];
        args_new[0] = "";
        for(int i = 1; i < args_new.length; i++) {
            args_new[i] = args[i - 1];
        }

        PySystemState.initialize(
            PySystemState.getBaseProperties(), new Properties(), args_new
        );

        PySystemState systemState = Py.getSystemState();

        // Decide if stdin is interactive; if not, set the primary and
        // secondary prompts (sys.ps1 and sys.ps2) to the empty string.
        boolean interactive = ((PyFile)Py.defaultSystemState.stdin).isatty();
        if (!interactive) {
            systemState.ps1 = systemState.ps2 = Py.EmptyString;
        }

        // Create an interpreter.
        PythonInterpreter interp = new PythonInterpreter();
        systemState.__setattr__("_jy_interpreter", Py.java2py(interp));

        // Verify that we have the correct console type.  Don't use
        // "instanceof" here because that will return true for parent/child
        // class comparisons.
	if (Py.getConsole().getClass() != PlainConsole.class) {
            logger.log(
                Level.WARNING, "Expected the interpreter console to be of " +
                "type org.python.core.PlainConsole, but instead found " +
                Py.getConsole().getClass().getName() + "."
            );
        }

	// Run OntoPilot.
        interp.exec("try:\n import ontopilot_main\nexcept SystemExit: pass");
    }
}
