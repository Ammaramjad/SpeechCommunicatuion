#!/usr/bin/env bash
# One-time: npx surge login
# Then run this script to publish https://velora-private-rides.surge.sh/
set -euo pipefail
cd "$(dirname "$0")"
python3 -c "
import json
from catalog import *
from pathlib import Path
cat = {
    'classes': CLASSES, 'operators': OPERATORS, 'locations': LOCATIONS,
    'popular': POPULAR, 'extras': EXTRAS, 'reviews': REVIEWS, 'faq': FAQ,
    'help': HELP, 'promos': list(PROMOS.keys()),
    'promo_shelf': [{'code': k, **v} for k,v in PROMOS.items()],
    'fleet_os': FLEET_OS_URL, 'secondary_nav': SECONDARY_NAV,
    'service_tabs': SERVICE_TABS, 'regions': REGIONS, 'destinations': DESTINATIONS,
    'benefits': BENEFITS, 'how_to_book': HOW_TO_BOOK, 'favorites': FAVORITES,
    'trending': TRENDING, 'channels': CHANNELS,
    'pricing': PRICING, 'fixed_routes': {f'{a}|{b}': v for (a,b), v in FIXED_ROUTES.items()},
    'fx': FX, 'symbols': SYMBOL,
}
Path('data/catalog.json').write_text(json.dumps(cat, ensure_ascii=False, indent=2))
"
echo "Deploying to https://velora-private-rides.surge.sh/"
npx --yes surge . velora-private-rides.surge.sh
echo "Done — share that URL with anyone."
