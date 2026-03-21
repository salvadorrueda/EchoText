#!/bin/bash

# Compatibilitat amb l'antic instal·lador d'echotextcommand.
# Deleguem tota la lògica al script unificat.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/install_client.sh" command "$@"
