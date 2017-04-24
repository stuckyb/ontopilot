## Building the standalone OntoPilot JAR

The standalone JAR build was originally based on the example at https://github.com/jsbruneau/jython-selfcontained-jar/.

To build the standalone OntoPilot JAR, you need Apache Ant installed. It should be sufficient to just run `ant` in the same directory as `build.xml` (i.e., the project root directory).
    
Ant should create a new jar file called `dist/ontopilot.jar` which you can then run.
```
$ java -jar dist/ontopilot.jar
``` 
