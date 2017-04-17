import java.io.FileInputStream;
import java.lang.System;
import java.util.Properties;
import java.util.Arrays;

import org.python.core.Py;
import org.python.core.PyException;
import org.python.core.PyFile;
import org.python.core.PySystemState;
import org.python.util.JLineConsole;
import org.python.util.InteractiveConsole;
import org.python.util.InteractiveInterpreter;

public class Main {
    private static InteractiveConsole newInterpreter(boolean interactiveStdin) {
        if (!interactiveStdin) {
            return new InteractiveConsole();
        }

        String interpClass = PySystemState.registry.getProperty(
            "python.console", ""
        );
        if (interpClass.length() > 0) {
            try {
                return (InteractiveConsole)Class.forName(
            interpClass).newInstance();
            } catch (Throwable t) {
                // fall through
            }
        }

        return new InteractiveConsole();
    }

    public static void main(String[] args) throws PyException, Exception {
        // To make the python interpreter accept arguments at right index.
        String[] args_new = new String[args.length + 1];
        args_new[0] = "";
        for(int i = 1; i < args_new.length; i++) {
            args_new[i] = args[i - 1];
        }
        args = args_new;
	
        PySystemState.initialize(
            PySystemState.getBaseProperties(), new Properties(), args
        );

        PySystemState systemState = Py.getSystemState();

        // Decide if stdin is interactive.
        boolean interactive = ((PyFile)Py.defaultSystemState.stdin).isatty();
        if (!interactive) {
            systemState.ps1 = systemState.ps2 = Py.EmptyString;
        }
         
        // Create an interpreter.
        InteractiveConsole interp = newInterpreter(interactive);
        systemState.__setattr__("_jy_interpreter", Py.java2py(interp));
        interp.exec("try:\n import ontopilot_main\nexcept SystemExit: pass");
    }
}
