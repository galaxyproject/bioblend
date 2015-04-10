BioBlend.objects Examples
=========================

Microbiology
------------

This directory contains three examples of interaction with real-world
microbiology workflows hosted by CRS4's Orione Galaxy server:

 * bacterial re-sequencing (w2_bacterial_reseq.py);
 * bacterial de novo assembly (w3_bacterial_denovo.py);
 * metagenomics (w5_metagenomics.py).

All examples use workflows and datasets publicly available on Orione.
Before you can run them, you have to register and obtain an API key:

 * go to https://orione.crs4.it and register -- or log in, if you are
   already registered -- through the "User" menu at the top of the page;
 * open "User" -> "API Keys";
 * generate an API key if you don't have one.

In the example file, replace YOUR_API_KEY with your API key (or assign
its value to the GALAXY_API_KEY environment variable), then run it:

  export GALAXY_API_KEY=000this_should_be_your_api_key00
  python w2_bacterial_reseq.py

The job can take a long time to complete: before exiting, the script
runs the workflow asynchronously, then displays the name and id of the
output history on standard output.  In the Galaxy web UI, click the
gear icon at the top right corner of the History panel, select "Saved
Histories" and look for the name of the output history in the center
frame; finally, choose "switch" from the history's drop-down menu to
make it the current one and follow the job as it evolves on Galaxy.

Toy Example
-----------

The small.py file contains a "toy" example that should run much faster
(once the cluster's resource manager allows it to run)
than the above ones.  In this case, the script waits for the job to
complete and downloads its results to a local file.

See Also
--------

Cuccuru et al., "Orione, a web-based framework for NGS
analysis in microbiology". Bioinformatics (2014).
http://dx.doi.org/10.1093/bioinformatics/btu135
