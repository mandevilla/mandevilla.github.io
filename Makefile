ASSETS_DIR=assets
SCSS_DIR=${ASSETS_DIR}/scss
CSS_DIR=site/html/media/css
BOOTSTRAP_VERSION=3.0.1
PYTHON=`which python`
NOSE=`which nosetests`

all: test

build:
	$(PYTHON) builder.py --fetch

test:
	$(NOSE) -s -lib/image.py lib/webapi.py

scss:
	sass --style compressed ${SCSS_DIR}/style.scss:${CSS_DIR}/style.css
	sass --style compressed ${SCSS_DIR}/bootstrap${BOOTSTRAP_VERSION}.scss:${CSS_DIR}/bootstrap.min.css
	sass --style compressed ${SCSS_DIR}/font-awesome.scss:${CSS_DIR}/font-awesome.min.css
