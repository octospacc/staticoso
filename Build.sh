#!/bin/sh
cd "$( dirname "$( realpath "$0" )" )"

mkdir -p public

cp -R Pages/* public/
find public -type f -name "*.html" -exec sh -c 'cat Templates/Standard.html > "$1"' _ {} \;
find public -type f -name "*.html" -print0 | xargs -0 sed -i -e 's/\[HTML\:PageTitle\]/ERRE/g'

cp Style.css public/
