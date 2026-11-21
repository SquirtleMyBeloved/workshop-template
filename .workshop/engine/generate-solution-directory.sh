#!/bin/bash

for dir in ../../exercises/*; do
	cp -r "$dir"/src/ "$dir"/solution/
done