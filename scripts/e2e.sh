#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

core="${CORE_URL:-http://localhost:8000}"

home="$(curl -fsSL "$core/")"
if [[ "$home" != *'Небольшой частный дом'* ]]; then
  echo "FAIL: the home page is not shown in Russian with compiled translations"
  exit 1
fi
stylesheet="$(curl -fsS "$core/static/site/site.css")"
if [[ "$stylesheet" != *tailwindcss* ]]; then
  echo "FAIL: the stylesheet was not built by the Tailwind CLI"
  exit 1
fi
echo "OK: the home page speaks Russian, the stylesheet is built"

services="$(curl -fsS "$core/en/services/")"
if [[ "$services" != *'Care services'* ]]; then
  echo "FAIL: the services page did not answer in English"
  exit 1
fi
echo "OK: the services page reads the database of care"
