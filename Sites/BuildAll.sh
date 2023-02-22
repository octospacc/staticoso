#!/bin/sh
cd "$( dirname "$( realpath "$0" )" )"

# First build all sites independently,
# then move them to a base public folder

mkdir ../public

for Site in *
do
	if [ -d "$Site" ]
	then
		cd $Site
		python3 ../../App/Source/Build.py
		mv ./public ../../public/$Site
		cd ..
	fi
done
