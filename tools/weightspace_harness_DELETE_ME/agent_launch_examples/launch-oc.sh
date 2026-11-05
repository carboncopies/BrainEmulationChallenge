#!/bin/bash
# Launch the three OpenCode agents (pong_netmorph follow-ups), one per worktree, in the background.
# Briefs and logs: $P/<name>.md and $P/<name>.log
P=/tmp/claude-1002/-home-johnjose-dev-frame/e8571311-ad86-4e3f-95d5-868bed60ba5d/scratchpad/oc
OC=~/.opencode/bin/opencode
for a in "nes-spikewindow opencode/big-pickle spikewindow" \
         "nes-modelsave opencode/deepseek-v4-pro modelsave" \
         "devframe-docs opencode/deepseek-v4.1-flash docs"; do
  set -- $a
  (cd ~/BrainGenix/wt/$1 && nohup "$OC" run --auto -m "$2" --title "$3" "$(cat "$P/$3.md" "$P/rules.md")" > "$P/$3.log" 2>&1 &)
  echo "started $3 ($2) in ~/BrainGenix/wt/$1"
done
