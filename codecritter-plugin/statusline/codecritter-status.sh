#!/usr/bin/env bash
# Codecritter statusline — animated, right-aligned multi-line companion
#
# Art is pre-rendered by codecritter/art_cache.py into ~/.claude/codecritter/art_cache.json.
# This script reads the cache, selects the animation frame, and renders it
# with rarity colors and a speech bubble.
#
# Animation: 500ms per tick, sequence: [0,0,0,0,1,0,0,0,-1,0,0,1,0,0,0]
#   Frame -1 = blink (read from blink_frames in cache)
#   Frames 0,1 = normal idle frames from cache
#
# Uses Braille Blank (U+2800) for padding — survives JS .trim()

STATE="$HOME/.claude/codecritter/save.json"
ART_CACHE="$HOME/.claude/codecritter/art_cache.json"

[ -f "$STATE" ] || exit 0

# Read from save.json (.codecritter wrapper, with .jamb fallback for migration)
_j() { jq -r "((.codecritter // .jamb) $1) // \"$2\"" "$STATE" 2>/dev/null; }

MUTED=$(_j '.muted' 'false')
[ "$MUTED" = "true" ] && exit 0

NAME=$(_j '.name' '')
[ -z "$NAME" ] && exit 0

RARITY=$(_j '.native_rarity' 'common')
RARITY="${RARITY,,}"
# Prefer current_quip (TUI-synced) over reaction (hook-set)
REACTION=$(_j '.current_quip' '')
[ -z "$REACTION" ] || [ "$REACTION" = "null" ] && REACTION=$(_j '.reaction' '')

cat > /dev/null  # drain stdin

# ─── Bootstrap art cache if missing ─────────────────────────────────────────
if [ ! -f "$ART_CACHE" ]; then
    codecritter art-cache 2>/dev/null
fi
[ -f "$ART_CACHE" ] || exit 0

# ─── Animation frame selection ───────────────────────────────────────────────
TUI_FRAME=$(_j '.animation_frame' '-1')
if [ "$TUI_FRAME" != "-1" ] && [ "$TUI_FRAME" != "null" ] && [ -n "$TUI_FRAME" ]; then
    FRAME=$TUI_FRAME
else
    SEQ=(0 0 0 0 1 0 0 0 -1 0 0 1 0 0 0)
    SEQ_LEN=${#SEQ[@]}
    NOW=$(date +%s)
    FRAME_IDX=$(( NOW % SEQ_LEN ))
    FRAME=${SEQ[$FRAME_IDX]}
fi

BLINK=0
if [ "$FRAME" -eq -1 ]; then
    BLINK=1
    FRAME=0
fi

# ─── Read pre-rendered art from cache ────────────────────────────────────────
FRAME_KEY=$( [ "$BLINK" -eq 1 ] && echo "blink_frames" || echo "frames" )
FRAME_COUNT=$(jq ".frames | length" "$ART_CACHE" 2>/dev/null)
[ "${FRAME_COUNT:-0}" -lt 1 ] && exit 0
CACHE_FRAME=$(( FRAME % FRAME_COUNT ))

mapfile -t CACHE_ART < <(jq -r ".${FRAME_KEY}[$CACHE_FRAME] // .${FRAME_KEY}[0] | .[]" "$ART_CACHE" 2>/dev/null)
HAT_LINE=$(jq -r '.hat_line // ""' "$ART_CACHE" 2>/dev/null)

# ─── Rarity color ────────────────────────────────────────────────────────────
NC=$'\033[0m'
case "$RARITY" in
  common)    C=$'\033[38;2;153;153;153m' ;;
  uncommon)  C=$'\033[38;2;78;186;101m'  ;;
  rare)      C=$'\033[38;2;177;185;249m' ;;
  epic)      C=$'\033[38;2;175;135;255m' ;;
  legendary) C=$'\033[38;2;255;193;7m'   ;;
  *)         C=$'\033[0m' ;;
esac

B=$'\xe2\xa0\x80'  # Braille Blank U+2800

# ─── Terminal width ──────────────────────────────────────────────────────────
COLS=0
PID=$$
for _ in 1 2 3 4 5; do
    PID=$(ps -o ppid= -p "$PID" 2>/dev/null | tr -d ' ')
    [ -z "$PID" ] || [ "$PID" = "1" ] && break
    PTY=$(readlink "/proc/${PID}/fd/0" 2>/dev/null)
    if [ -c "$PTY" ] 2>/dev/null; then
        COLS=$(stty size < "$PTY" 2>/dev/null | awk '{print $2}')
        [ "${COLS:-0}" -gt 40 ] 2>/dev/null && break
    fi
done
[ "${COLS:-0}" -lt 40 ] 2>/dev/null && COLS=${COLUMNS:-0}
[ "${COLS:-0}" -lt 40 ] 2>/dev/null && COLS=125

# ─── Build art lines (hat + cached art + name) ──────────────────────────────
DIM=$'\033[2;3m'

ALL_LINES=()
ALL_COLORS=()
[ -n "$HAT_LINE" ] && [ "$HAT_LINE" != "null" ] && { ALL_LINES+=("$HAT_LINE"); ALL_COLORS+=("$C"); }
for line in "${CACHE_ART[@]}"; do
    ALL_LINES+=("$line"); ALL_COLORS+=("$C")
done

# Compute art width from longest line
ART_W=0
for line in "${ALL_LINES[@]}"; do
    len=${#line}
    [ "$len" -gt "$ART_W" ] && ART_W=$len
done
# Minimum width / padding
[ "$ART_W" -lt 10 ] && ART_W=10
ART_W=$(( ART_W + 2 ))

# Center the name under art
NAME_LEN=${#NAME}
ART_CENTER=$(( ART_W / 2 - 1 ))
NAME_PAD=$(( ART_CENTER - NAME_LEN / 2 ))
[ "$NAME_PAD" -lt 0 ] && NAME_PAD=0
NAME_LINE="$(printf '%*s%s' "$NAME_PAD" '' "$NAME")"
ALL_LINES+=("$NAME_LINE"); ALL_COLORS+=("$DIM")

ART_COUNT=${#ALL_LINES[@]}

# ─── Speech bubble (left of art, word-wrapped) ──────────────────────────────
BUBBLE_TEXT=""
if [ -n "$REACTION" ] && [ "$REACTION" != "null" ]; then
    BUBBLE_TEXT="$REACTION"
fi

INNER_W=28
TEXT_LINES=()
if [ -n "$BUBBLE_TEXT" ]; then
    WORDS=($BUBBLE_TEXT)
    CUR_LINE=""
    for word in "${WORDS[@]}"; do
        if [ -z "$CUR_LINE" ]; then
            CUR_LINE="$word"
        elif [ $(( ${#CUR_LINE} + 1 + ${#word} )) -le $INNER_W ]; then
            CUR_LINE="$CUR_LINE $word"
        else
            TEXT_LINES+=("$CUR_LINE")
            CUR_LINE="$word"
        fi
    done
    [ -n "$CUR_LINE" ] && TEXT_LINES+=("$CUR_LINE")
fi

TEXT_COUNT=${#TEXT_LINES[@]}
BOX_W=$(( INNER_W + 4 ))
BUBBLE_LINES=()
BUBBLE_TYPES=()
if [ $TEXT_COUNT -gt 0 ]; then
    BORDER=$(printf '%*s' "$(( BOX_W - 2 ))" '' | tr ' ' '-')
    BUBBLE_LINES+=(".${BORDER}.")
    BUBBLE_TYPES+=("border")
    for tl in "${TEXT_LINES[@]}"; do
        tpad=$(( INNER_W - ${#tl} ))
        [ "$tpad" -lt 0 ] && tpad=0
        padding=$(printf '%*s' "$tpad" '')
        BUBBLE_LINES+=("| ${tl}${padding} |")
        BUBBLE_TYPES+=("text")
    done
    BUBBLE_LINES+=("\`${BORDER}'")
    BUBBLE_TYPES+=("border")
fi

BUBBLE_COUNT=${#BUBBLE_LINES[@]}

# ─── Right-align with bubble box to the left ─────────────────────────────────
GAP=2
if [ $BUBBLE_COUNT -gt 0 ]; then
    TOTAL_W=$(( BOX_W + GAP + ART_W ))
else
    TOTAL_W=$ART_W
fi
MARGIN=8
PAD=$(( COLS - TOTAL_W - MARGIN ))
[ "$PAD" -lt 0 ] && PAD=0

SPACER=$(printf "${B}%${PAD}s" "")
GAP_STR=$(printf '%*s' "$GAP" '')

# Vertically center bubble box on the art
BUBBLE_START=0
if [ $BUBBLE_COUNT -gt 0 ] && [ $BUBBLE_COUNT -lt $ART_COUNT ]; then
    BUBBLE_START=$(( (ART_COUNT - BUBBLE_COUNT) / 2 ))
fi

# Find the connector line (middle text line → points to buddy's mouth)
CONNECTOR_BI=-1
if [ $BUBBLE_COUNT -gt 2 ]; then
    FIRST_TEXT=1
    LAST_TEXT=$(( BUBBLE_COUNT - 2 ))
    CONNECTOR_BI=$(( (FIRST_TEXT + LAST_TEXT) / 2 ))
fi

# ─── Output: merged bubble box + connector + art per line ─────────────────────
RENDER_END=$(( BUBBLE_START + BUBBLE_COUNT ))
[ "$RENDER_END" -lt "$ART_COUNT" ] && RENDER_END=$ART_COUNT

for (( i=0; i<RENDER_END; i++ )); do
    if [ $i -lt $ART_COUNT ]; then
        art_part="${ALL_COLORS[$i]}${ALL_LINES[$i]}${NC}"
    else
        art_part=$(printf '%*s' "$ART_W" '')
    fi

    if [ $BUBBLE_COUNT -gt 0 ]; then
        bi=$(( i - BUBBLE_START ))
        if [ $bi -ge 0 ] && [ $bi -lt $BUBBLE_COUNT ]; then
            bline="${BUBBLE_LINES[$bi]}"
            btype="${BUBBLE_TYPES[$bi]}"

            if [ $bi -eq $CONNECTOR_BI ]; then
                gap="${C}--${NC} "
            else
                gap="   "
            fi

            if [ "$btype" = "border" ]; then
                echo "${SPACER}${C}${bline}${NC}${gap}${art_part}"
            else
                pipe_l="${bline:0:1}"
                pipe_r="${bline: -1}"
                inner="${bline:1:$(( ${#bline} - 2 ))}"
                echo "${SPACER}${C}${pipe_l}${NC}${DIM}${inner}${NC}${C}${pipe_r}${NC}${gap}${art_part}"
            fi
        else
            empty=$(printf '%*s' "$BOX_W" '')
            echo "${SPACER}${empty}   ${art_part}"
        fi
    else
        echo "${SPACER}${art_part}"
    fi
done

exit 0
