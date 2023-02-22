#!/bin/sh
cd "$( dirname "$( realpath "$0" )" )"

cd ../Sources/Themes

for Theme in *
do
	cd ../../
	mkdir -p ./Build/Demos/$Theme
	cd ./Build/Demos/$Theme
	mkdir -p ./Assets ./Templates ./Posts
	cp -r ../../Themes/$Theme ./.Source
	cp ./.Source/$Theme.html ./Templates/Default.html
	cp ./.Source/*.css ./Assets/
	cp ../../../Sources/Snippets/*.md ./Posts/
	python3 ../../../../App/Source/Build.py \
		--SiteName="$Theme"
	cd ../../../Sources/Themes
done
