CURDIR = $(shell pwd)
GULP = $(CURDIR)/node_modules/.bin/gulp
BOWER = $(CURDIR)/node_modules/.bin/bower

NO_COLOR = $(shell test $$NO_COLOR && echo '--no-color' || echo '')
SILENT = $(shell test $$NO_COLOR && echo '--silent' || echo '')

all:
    npm install $(NO_COLOR) $(SILENT)
    $(GULP) $(NO_COLOR) dist

bower-install:
    $(BOWER) $(NO_COLOR) install

bower-clean:
    $(BOWER) $(NO_COLOR) cache clean

.PHONY: all watch bower-install
