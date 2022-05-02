#!/usr/bin/env sh
find . -size +32M | cat >> .gitignore_update
