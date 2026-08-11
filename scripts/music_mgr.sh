#!/bin/bash
# Music Manager: Lyric Fetcher + Metadata Handler
# Genius API scraper with multi-line HTML parsing

set -euo pipefail

GENIUS_TOKEN="${GENIUS_TOKEN:-}"
CURL_TIMEOUT=10
GENIUS_UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
LYRICS_DIR="${HOME}/.lyrics"

mkdir -p "$LYRICS_DIR"

fetch_lyrics() {
    local artist="$1" title="$2"
    local cache_file="${LYRICS_DIR}/${artist}__${title}.txt"
    
    # Return cache if exists
    [[ -f "$cache_file" ]] && { cat "$cache_file"; return 0; }
    
    # Genius API query
    local query="${artist} ${title}"
    local search_url="https://api.genius.com/search?q=$(echo "$query" | sed 's/ /+/g')"
    
    local response
    response=$(curl -s -m "$CURL_TIMEOUT" \
        -H "Authorization: Bearer ${GENIUS_TOKEN}" \
        -H "User-Agent: ${GENIUS_UA}" \
        "$search_url" 2>/dev/null) || return 1
    
    # Extract URL via Perl (multi-line HTML parsing)
    local url
    url=$(echo "$response" | perl -ne '/"url":"([^"]*lyrics[^"]*)"/ && print $1' | head -1)
    [[ -z "$url" ]] && return 1
    
    # Scrape lyrics page
    local lyrics
    lyrics=$(curl -s -m "$CURL_TIMEOUT" \
        -H "User-Agent: ${GENIUS_UA}" \
        "$url" 2>/dev/null | \
        perl -0777 -ne 'while (/data-lyrics-container="true"[^>]*>(.*?)<\/div>/gs) { 
            my $block = $1; 
            $block =~ s/<[^>]+>//g; 
            $block =~ s/&nbsp;/ /g; 
            $block =~ s/&amp;/\&/g; 
            print $block . "\n"; 
        }') || return 1
    
    # Cache and output
    echo "$lyrics" | tee "$cache_file"
}

case "${1:-}" in
    lyrics)
        artist="$(mpc current -f '%artist%' 2>/dev/null || echo '')"
        title="$(mpc current -f '%title%' 2>/dev/null || echo '')"
        [[ -z "$artist" || -z "$title" ]] && { echo "No track playing"; exit 1; }
        fetch_lyrics "$artist" "$title"
        ;;
    *)
        echo "Usage: $0 lyrics"
        exit 1
        ;;
esac
