#!/usr/bin/env zsh
# Use this script to build a new release and upload it to PyPI.

VERSION="1.0.0"
echo "BUILDING $VERSION"
sed s/X.Y.Z/$VERSION/ pyproject.toml.template > pyproject.toml
python3 -m build

if $(false) ; then
  echo "UPLOADING $VERSION"
  python3 -m twine upload dist/ccda_to_omop-${VERSION}-py3-none-any.whl dist/ccda_to_omop-${VERSION}.tar.gz
else
  echo "test UPLOADING $VERSION"
  python3 -m twine upload --repository testpypi dist/ccda_to_omop-${VERSION}-py3-none-any.whl dist/ccda_to_omop-${VERSION}.tar.gz
fi

