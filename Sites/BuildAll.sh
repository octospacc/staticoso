#!/bin/sh
cd "$( dirname "$( realpath "$0" )" )"

# First build all sites independently,
# then move them to a base public folder

rm -rf ../public/*
mkdir -p ../public

for Site in *
do
	if [ -d "$Site" ]
	then
		cd $Site
		python3 ../../App/Source/Build.py
		cp -r ./public ../../public/$Site
		cd ..
	fi
done

cd ../public
mv ./Main/* ./
