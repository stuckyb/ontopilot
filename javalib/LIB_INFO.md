
## Updating the Pellet reasoner

The documentation for Pellet does not seem to be up to date, and there is little information about how to build it.  Here is what worked for me.  After downloading/cloning the Pellet source (https://github.com/stardog-union/pellet), run

```
$ mvn package
```

This will create the file `distribution/target/pellet-2.4.0-SNAPSHOT-dist.tar.gz`.

Copy this file into a temporary directory and expand/untar it.

All of the pellet jar files (and required library files) will be in `pellet-2.4.0-SNAPSHOT/lib`.  To get Pellet working with OntoPilot, I needed to copy these files to OntoPilot's `javalib` directory (these are in addition to the libraries that were already there after installing HermiT and ELK): `aterm-java-1.8.2-p1.jar`, `jjtraveler-0.6.jar`, `pellet-core-2.4.0-SNAPSHOT.jar`, `pellet-owlapi-2.4.0-SNAPSHOT.jar`, and `shared-objects-1.4.9-p1.jar`.

## Updating the JFact reasoner

There does not appear to be any documentation for JFact at all.  Here's what worked for me.  After downloading/cloning the JFact source (https://github.com/owlcs/jfact), the default branch will be "version5", which requires the OWLAPI version 5. So after cloning, run
```
$ git fetch
$ git checkout master
```

Then build JFact:
```
$ mvn package
```

This will create the directory `target`, which will contain the JFact jar files.

Copy `jfact-1.2.4.jar` to the `javalib` directory.

## Creating the custom, data type-aware and data restriction-aware ELK reasoner

Disable the standard ELK reasoner library by renaming it.

```
$ mv elk-0.4.3-owlapi.jar elk-0.4.3-owlapi.jar.standard
```

Clone the ELK repository and fetch the "elk-parent-datatypes" branch.  Do this in the "javalib" folder.

```
$ git clone https://github.com/liveontologies/elk-reasoner.git
$ cd elk-reasoner
$ git checkout elk-parent-datatypes
```

Next, we need to hack in support for xsd:float and xsd:date data types.  This requires adding code to several files.  Note that the changes below really is a hack.  In particular, scientific notation literals are not supported, and all xsd:date values are just treated like strings.

`elk-owl-parent/elk-owl-model/src/main/java/org/semanticweb/elk/owl/predefined/PredefinedElkIri.java`

Line 46, in `public enum PredefinedElkIri {`:
```
	RDFS_LITERAL(new ElkFullIri(PredefinedElkPrefix.RDFS.get(), "Literal")), //

+	XSD_DATE(new ElkFullIri(PredefinedElkPrefix.XSD.get(), "date")), //
+
	XSD_DATE_TIME(new ElkFullIri(PredefinedElkPrefix.XSD.get(), "dateTime")), //
```

Line 64, in `public enum PredefinedElkIri {`:
```
 	XSD_DECIMAL(new ElkFullIri(PredefinedElkPrefix.XSD.get(), "decimal")), //
 
+	XSD_FLOAT(new ElkFullIri(PredefinedElkPrefix.XSD.get(), "float")), //
+
 	XSD_INTEGER(new ElkFullIri(PredefinedElkPrefix.XSD.get(), "integer")), //
```

`elk-owl-parent/elk-owl-implementation/src/main/java/org/semanticweb/elk/owl/managers/ElkDatatypeMap.java`

Line 78, in `public class ElkDatatypeMap {`:
```
	public static final LiteralDatatype RDFS_LITERAL = new LiteralDatatypeImpl(PredefinedElkIri.RDFS_LITERAL.get());
	public static final StringDatatype XSD_DATE = new StringDatatypeImpl(PredefinedElkIri.XSD_DATE.get());
	public static final DateTimeDatatype XSD_DATE_TIME = new DateTimeDatatypeImpl(PredefinedElkIri.XSD_DATE_TIME.get());
```

Line 86, in `public class ElkDatatypeMap {`:
```
 	public static final DecimalDatatype XSD_DECIMAL = new DecimalDatatypeImpl(PredefinedElkIri.XSD_DECIMAL.get());
+	public static final DecimalDatatype XSD_FLOAT = new DecimalDatatypeImpl(PredefinedElkIri.XSD_FLOAT.get());
 	public static final IntegerDatatype XSD_INTEGER = new IntegerDatatypeImpl(PredefinedElkIri.XSD_INTEGER.get());
```

The next addition is not strictly necessary, but is helpful for debugging data type lookups.

`elk-owlapi/src/main/java/org/semanticweb/elk/owlapi/wrapper/OwlConverter.java`

Line 507 in `public class OwlConverter {`:
```
 		if (owlDatatype != null && (owlLiteral.getLang() == null || owlLiteral.getLang().isEmpty())) {
+			System.out.println("DATATYPE LOOKUP: " + owlDatatype.toString());
 			ElkDatatype datatype = ElkDatatypeMap.get(PredefinedElkIri.lookup(new ElkFullIri(owlDatatype.getIRI().toString())).get());
```

Now build the ELK reasoner.

```
$ mvn clean install
```

Run the script to extract the new ELK library and add it to javalib.

```
$ ./install_custom_elk.sh
```

