#!/bin/bash

tmpdir=$(mktemp -d) || exit 1

# check if python supports zipapp compression
zipapp="python3 -m zipapp"
if python3 -m zipapp --help | grep -q -- --compress; then
    zipapp="$zipapp --compress"
fi

for dir in lib resources templates; do
    if [ -d $dir ]; then cp -a $dir $tmpdir/; fi
done

if [ -z "$requirements" ]; then
  if [ -f requirements.txt ]; then
    requirements="$(cat requirements.txt)"
    if python3 -c 'import requests' 2>/dev/null; then
        requirements="$(grep -iv requests requirements.txt)"
    fi
  fi
fi
if [ -n "$requirements" ]; then
  python3 -m pip install $requirements --target $tmpdir
fi

if [ $# -lt 1 ]; then
  scripts=*.py
else
  scripts="$@"
fi

if [ $scripts = "main.py" ]; then
  cp $scripts $tmpdir/__main__.py
  $zipapp --python "/usr/bin/env python3" --output $(basename $(pwd)).pyz $tmpdir
else
  for script in $scripts; do
    cp $script $tmpdir/__main__.py
    $zipapp --python "/usr/bin/env python3" --output ${script}z $tmpdir
  done
fi

rm -r $tmpdir
