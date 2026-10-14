#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./Tools/PinClient.sh <tag>    Pin the PythonClient submodule to <tag> and commit it
  ./Tools/PinClient.sh --check  Print the pinned tag; exit 1 if the pin is not a tagged release
  ./Tools/PinClient.sh --list   List PythonClient release tags, newest first

A submodule records a commit, not a tag. This script looks up the commit for
you and puts the tag in the commit message, so MRs say which release they pin.
On main it first creates the branch chore/pin-pythonclient-<tag>.
USAGE
}

SUBMODULE="PythonClient"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
cd "$repo_root"

client_url="$(git config -f .gitmodules "submodule.$SUBMODULE.url")"

# "<commit> <tag>" for every version tag on the client's origin.
# Annotated tags list twice; the peeled "^{}" line holds the commit.
remote_tags() {
  git ls-remote --tags "$client_url" |
    awk '{ ref = $2; sub("^refs/tags/", "", ref)
           if (ref ~ /\^\{\}$/) { sub(/\^\{\}$/, "", ref); peeled[ref] = $1 }
           else                 { direct[ref] = $1 } }
         END { for (t in direct) print (t in peeled ? peeled[t] : direct[t]), t }' |
    { grep -E ' [0-9]+\.[0-9]+\.[0-9]+$' || true; } |
    sort -k2,2 -V -r
}

pinned_commit() {
  git ls-tree HEAD "$SUBMODULE" | awk '{ print $3 }'
}

tag_for_commit() {
  awk -v c="$1" '$1 == c { print $2; exit }' <<< "$2"
}

case "${1:-}" in
  -h|--help)
    usage
    exit 0
    ;;
  "")
    usage >&2
    exit 2
    ;;
  --list)
    remote_tags | awk '{ print $2 "  " substr($1, 1, 9) }'
    exit 0
    ;;
  --check)
    tags="$(remote_tags)"
    commit="$(pinned_commit)"
    tag="$(tag_for_commit "$commit" "$tags")"
    if [[ -z "$tag" ]]; then
      echo "$SUBMODULE is pinned to ${commit:0:9}, which is not a tagged release." >&2
      echo "Pin a release instead: ./Tools/PinClient.sh <tag>  (see --list)" >&2
      exit 1
    fi
    echo "$SUBMODULE is pinned to $tag (${commit:0:9})"
    exit 0
    ;;
  -*)
    echo "Unknown option: $1" >&2
    usage >&2
    exit 2
    ;;
esac

new_tag="$1"

if ! git diff --cached --quiet; then
  echo "You have staged changes; commit or unstage them first so the pin commit holds only the pin." >&2
  exit 1
fi

git submodule update --init "$SUBMODULE"
if [[ -n "$(git -C "$SUBMODULE" status --porcelain)" ]]; then
  echo "$SUBMODULE has local changes; commit or discard them first." >&2
  exit 1
fi

git -C "$SUBMODULE" fetch --quiet --tags origin
if ! new_commit="$(git -C "$SUBMODULE" rev-parse -q --verify "refs/tags/$new_tag^{commit}")"; then
  echo "$SUBMODULE has no tag '$new_tag'. Available tags:" >&2
  remote_tags | awk '{ print "  " $2 }' >&2
  exit 1
fi

old_commit="$(pinned_commit)"
if [[ "$new_commit" == "$old_commit" ]]; then
  echo "$SUBMODULE is already pinned to $new_tag (${new_commit:0:9}); nothing to do."
  exit 0
fi
old_tag="$(tag_for_commit "$old_commit" "$(remote_tags)")"
old_desc="${old_tag:-untagged ${old_commit:0:9}}"

current_branch="$(git branch --show-current)"
if [[ "$current_branch" == "main" || "$current_branch" == "master" ]]; then
  git switch -c "chore/pin-pythonclient-$new_tag"
fi

git -C "$SUBMODULE" checkout --quiet "$new_tag"
git add "$SUBMODULE"
brought_in="$(git -C "$SUBMODULE" log --oneline --no-merges "$old_commit..$new_commit")"
git commit --quiet -m "Pin $SUBMODULE to tag $new_tag (was $old_desc)" \
  -m "$SUBMODULE ${old_commit:0:9} -> ${new_commit:0:9}. Commits brought in:" \
  -m "${brought_in:-(none; this moves the pin back)}"

echo "Pinned $SUBMODULE: $old_desc -> $new_tag (${new_commit:0:9})"
echo "Next: git push -u origin $(git branch --show-current), then open an MR."
