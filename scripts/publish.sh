#!/bin/bash
set -e

echo "í·¹ Nettoyage des anciens builds..."
rm -rf build/ dist/ *.egg-info

echo "í´¨ Construction du package..."
python -m build

echo "âœ… VÃ©rification du package..."
python -m twine check dist/*

echo "í³¦ Upload vers TestPyPI..."
python -m twine upload --repository testpypi dist/*

echo "âœ¨ Package publiÃ© sur TestPyPI!"
echo "Test avec: pip install --index-url https://test.pypi.org/simple/ qc2plus"

read -p "Voulez-vous publier sur PyPI production? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "íº€ Upload vers PyPI..."
    python -m twine upload dist/*
    echo "í¾‰ Package publiÃ© sur PyPI!"
fi
