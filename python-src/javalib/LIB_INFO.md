
## Updating the Pellet reasoner

The documentation for Pellet does not seem to be up to date, and there is little information about how to build it.  Here is what worked for me.  After downloading/cloning the Pellet source (https://github.com/stardog-union/pellet), run

```
$ mvn package
```

This will create the file `distribution/target/pellet-2.4.0-SNAPSHOT-dist.tar.gz`.

Copy this file into a temporary directory and expand/untar it.

All of the pellet jar files (and required library files) will be in `pellet-2.4.0-SNAPSHOT/lib`.  To get Pellet working with OntoPilot, I needed to copy these files to OntoPilot's `javalib` directory (these are in addition to the libraries that were already there after installing HermiT and ELK): `aterm-java-1.8.2-p1.jar`, `jjtraveler-0.6.jar`, `pellet-core-2.4.0-SNAPSHOT.jar`, `pellet-owlapi-2.4.0-SNAPSHOT.jar`, and `shared-objects-1.4.9-p1.jar`.

