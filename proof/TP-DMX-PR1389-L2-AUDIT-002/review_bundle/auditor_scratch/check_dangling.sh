for file in $(git diff --name-status 728d7c42e9ab..176d965e8b | grep ^D | awk '{print $2}'); do
  basename=$(basename "$file")
  echo "Checking $basename:"
  # Exclude specific directories
  git grep -l "$basename" | grep -vE '^(proof|audit_inputs|reports|extraction|claudedocs)/' || echo "  No references found"
done
echo "Checking docs/01-tutorials/installation-3.md"
git grep "contributing-zen.md" docs/01-tutorials/installation-3.md
echo "Checking config/docs_hygiene/docs_placement_policy.yaml"
git grep "gemini.md" config/docs_hygiene/docs_placement_policy.yaml
