VERSION=$(shell python -c 'import mamonsu; print(mamonsu.__version__)')
BUILDDIR=$(CURDIR)/build/mamonsu-$(VERSION)

all:
	@echo Install
	pip install --upgrade --editable .

publish: clean
	@echo Testing wheel build an installation
	@echo "Build $(VERSION)"
	python setup.py register
	python setup.py sdist upload
	@echo

prepare_builddir: clean
	@echo Prepare build directory
	mkdir build
	tar --transform='s,^\.,mamonsu-$(VERSION),'\
		-czf build/mamonsu-$(VERSION).tar.gz .\
		--exclude=build
	tar xvf build/mamonsu-$(VERSION).tar.gz -C build
	cp build/mamonsu-$(VERSION).tar.gz \
		$(BUILDDIR)/rpm/SOURCES
	chown -R root.root $(BUILDDIR)
	@echo

deb: prepare_builddir
	@echo Build deb
	cd $(BUILDDIR) && dpkg-buildpackage -b
	cp -av build/mamonsu*.deb .
	@echo

rpm: prepare_builddir
	@echo Build rpm
	rpmbuild -ba --define '_topdir $(BUILDDIR)/rpm'\
		$(BUILDDIR)/rpm/SPECS/mamonsu.spec
	cp -av $(BUILDDIR)/rpm/RPMS/noarch/mamonsu*.rpm .
	@echo

clean: python_clean
	rm -rf build

python_clean:
	@echo Cleaning up python fragments
	rm -rf *.egg dist build .coverage
	find . -name '__pycache__' -delete -print -o -name '*.pyc' -delete -print
	@echo
