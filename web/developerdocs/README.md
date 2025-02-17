# Developer Documentation

## About

This directory contains some documentation regarding the MLTSHP API. The documentation
is in REST format and is built using Sphinx. If any updates are made to the API,
corresponding updates should be made to this documentation to keep things in sync.
The documentation is readable through the site, but as static HTML, which has to be
built from this directory. The resulting HTML files need to be checked in along with
the API code changes.

## Setting Up

To build the documentation HTML files, you'll need to do the usual Python virtualenv
steps if you haven't already. Then, with the virtualenv active, install the special
requirements like this:

    $ pip install -r developerdocs/requirements.txt

(You'd issue this from the top of the MLTSHP repository, with the virtualenv for it
already active.)

## Building

With the setup steps done, building the documentation is just a matter of executing
the `make` command from the directory.

    $ cd developerdocs
    $ make

That should produce the updates to the HTML files (in templates/developers). You
will need to add any updates to those files to your git branch and commit them
along with your API changes.

